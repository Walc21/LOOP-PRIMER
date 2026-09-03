"""Offline regression tests for the M12 budget and observability contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.budget import (  # noqa: E402
    BudgetAuthorizationError,
    BudgetExceeded,
    BudgetIdempotencyError,
    BudgetIntegrityError,
    BudgetLedger,
    BudgetLimits,
    BudgetStateError,
    LimitedSupervisor,
    ManualClock,
)
from article_loop.observability import ObservabilityError, StructuredLogger  # noqa: E402


class M12LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "control").mkdir()
        self.clock = ManualClock(current=datetime(2026, 1, 1, tzinfo=timezone.utc))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def ledger(self, **overrides):
        values = {
            "total_tokens": 100,
            "per_cycle_tokens": 80,
            "per_department_tokens": 70,
            "per_role_tokens": 60,
            "per_model_tokens": 90,
            "max_calls": 10,
            "max_concurrent_children": 3,
            "max_retries": 2,
            "max_wall_time_seconds": 100,
        }
        values.update(overrides.pop("limits", {}))
        return BudgetLedger(
            self.root, "run-1", limits=BudgetLimits(**values), clock=self.clock,
            **overrides,
        )

    def test_reserve_admit_reconcile_is_hash_bound_and_reported(self):
        ledger = self.ledger()
        reservation = ledger.reserve(
            "call-1", 20, cycle_id=0, department_id="S10", role_id="W11",
            model="local-model", children=1, estimated_wall_time_seconds=10,
        )
        self.assertEqual(reservation["status"], "reserved")
        ledger.admit(reservation["reservation_id"], "receipt-1")
        result = ledger.reconcile(
            reservation["reservation_id"], receipt_id="receipt-1",
            input_tokens=4, output_tokens=5, cache_tokens=1,
            wall_time_seconds=8, usage_available=True,
        )
        self.assertEqual(result["status"], "RECONCILED")
        self.assertEqual(result["usage_tokens"], 10)
        status = ledger.status()
        self.assertEqual(status["usage"]["confirmed_tokens"], 10)
        self.assertEqual(status["assurance"], "reported")
        self.assertEqual(len(ledger.read_events()), 3)
        self.assertEqual(len(ledger.read_events()), ledger.logger.status()["event_count"])

    def test_two_reservations_race_cannot_spend_last_balance_twice(self):
        root = self.root
        clock = self.clock

        def reserve(call_id: str):
            ledger = BudgetLedger(root, "run-1", limits=BudgetLimits(total_tokens=10), clock=clock)
            try:
                return ledger.reserve(call_id, 6)["status"]
            except BudgetExceeded:
                return "rejected"

        barrier = threading.Barrier(2)

        def synchronized(call_id: str):
            barrier.wait()
            return reserve(call_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(synchronized, ("call-1", "call-2")))
        self.assertEqual(sorted(result), ["rejected", "reserved"])
        self.assertEqual(BudgetLedger(root, "run-1", limits=BudgetLimits(total_tokens=10), clock=clock).status()["usage"]["reserved_tokens"], 6)

    def test_usage_absent_becomes_uncertain_and_keeps_reservation(self):
        ledger = self.ledger(limits={"total_tokens": 10})
        reservation = ledger.reserve("call-1", 10)
        ledger.admit(reservation["reservation_id"], "receipt-1")
        result = ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-1")
        self.assertEqual(result["status"], "UNCERTAIN")
        self.assertEqual(ledger.status()["assurance"], "uncertain")
        with self.assertRaises(BudgetExceeded):
            ledger.reserve("call-2", 1)
        self.assertEqual(ledger.mark_uncertain(reservation["reservation_id"], "usage_unavailable", receipt_id="receipt-1")["status"], "UNCERTAIN")

    def test_release_requires_proof_and_only_unadmitted_reservation(self):
        ledger = self.ledger(limits={"total_tokens": 10})
        reservation = ledger.reserve("call-1", 10)
        with self.assertRaises(BudgetStateError):
            ledger.release_unadmitted(reservation["reservation_id"], "")
        released = ledger.release_unadmitted(reservation["reservation_id"], "adapter-never-admitted")
        self.assertEqual(released["status"], "RELEASED")
        with self.assertRaises(BudgetStateError):
            ledger.release_unadmitted(reservation["reservation_id"], "other-proof")
        next_reservation = ledger.reserve("call-2", 10)
        ledger.admit(next_reservation["reservation_id"], "receipt-2")
        with self.assertRaises(BudgetStateError):
            ledger.release_unadmitted(next_reservation["reservation_id"], "not-admitted")

    def test_reconcile_duplicate_is_idempotent_but_conflicting_receipt_fails(self):
        ledger = self.ledger()
        reservation = ledger.reserve("call-1", 10)
        ledger.admit(reservation["reservation_id"], "receipt-1")
        first = ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-1", input_tokens=1, output_tokens=2, cache_tokens=0, usage_available=True)
        second = ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-1", input_tokens=99, output_tokens=0, cache_tokens=0, usage_available=True)
        self.assertEqual(first["usage_tokens"], second["usage_tokens"])
        with self.assertRaises(BudgetIdempotencyError):
            ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-2", input_tokens=1, output_tokens=2, cache_tokens=0, usage_available=True)

    def test_over_estimate_blocks_new_admission(self):
        ledger = self.ledger(limits={"total_tokens": 100})
        reservation = ledger.reserve("call-1", 10)
        ledger.admit(reservation["reservation_id"], "receipt-1")
        ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-1", input_tokens=11, output_tokens=0, cache_tokens=0, usage_available=True)
        self.assertTrue(ledger.status()["reservations"][0]["over_estimate"])
        with self.assertRaises(BudgetExceeded):
            ledger.reserve("call-2", 1)

    def test_hierarchical_balance_is_atomic_and_reported(self):
        ledger = self.ledger(limits={"total_tokens": 100, "per_department_tokens": 5})
        ledger.reserve("call-1", 4, department_id="S10")
        with self.assertRaises(BudgetExceeded):
            ledger.reserve("call-2", 2, department_id="S10")
        status = ledger.status(current_cycle=0)
        self.assertEqual(status["usage_by_limit"]["per_department_tokens"]["S10"]["committed"], 4)
        self.assertEqual(status["balance"]["per_department_tokens"]["S10"], 1)

    def test_deadline_and_monotonic_duration_resume_from_existing_ledger(self):
        ledger = self.ledger(limits={"total_tokens": 20}, deadline_at="2026-01-01T00:00:05Z")
        ledger.reserve("call-1", 2)
        self.clock.advance(seconds=6)
        resumed = BudgetLedger(self.root, "run-1", limits=ledger.limits, clock=self.clock)
        self.assertEqual(resumed.deadline_at, "2026-01-01T00:00:05Z")
        self.assertGreaterEqual(resumed.read_events()[-1]["monotonic_elapsed_seconds"], 0)
        with self.assertRaises(BudgetExceeded):
            resumed.reserve("call-2", 1)
        self.assertTrue(any(item["alert_code"] == "deadline" for item in resumed.status()["alerts"]))

    def test_restart_cannot_enlarge_or_change_a_run_budget(self):
        ledger = self.ledger(limits={"total_tokens": 20}, currency="USD")
        ledger.reserve("call-1", 2)
        with self.assertRaises(BudgetIntegrityError):
            BudgetLedger(self.root, "run-1", limits=BudgetLimits(total_tokens=21), currency="USD", clock=self.clock)
        with self.assertRaises(BudgetIntegrityError):
            BudgetLedger(self.root, "run-1", limits=BudgetLimits(total_tokens=20), currency="EUR", clock=self.clock)

    def test_invalid_numeric_values_and_currency_divergence_fail_closed(self):
        ledger = self.ledger(limits={"total_tokens": 100})
        with self.assertRaises(Exception):
            ledger.reserve("call-1", True)
        with self.assertRaises(Exception):
            ledger.reserve("call-2", -1)
        with self.assertRaises(Exception):
            ledger.reconcile("unknown", receipt_id="receipt", input_tokens=1, output_tokens=1, cache_tokens=0, cost_microunits=1, currency="USD")
        reservation = ledger.reserve("call-3", 10)
        ledger.admit(reservation["reservation_id"], "receipt-3")
        with self.assertRaises(Exception):
            ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-3", input_tokens=1, output_tokens=1, cache_tokens=0, cost_microunits=1, currency="USD", usage_available=True)
        with self.assertRaises(Exception):
            ledger.reconcile(reservation["reservation_id"], receipt_id="receipt-3", input_tokens=1, output_tokens=1, cache_tokens=0, usage_available=1)

    def test_authorization_is_bound_to_run_config_profile_and_provider(self):
        config_hash = "a" * 64
        ledger = self.ledger(profile="calibration", config_hash=config_hash, live_enabled=True, limits={"total_tokens": 100})
        authorization = {
            "run_id": "run-1", "profile": "calibration", "config_hash": config_hash,
            "provider": "local", "model": "model-1", "token_limit": 50,
            "approved_at": self.clock.now_utc(), "approval_reference": "approval-1",
        }
        ledger.authorize(authorization)
        reservation = ledger.reserve("call-1", 10, provider="local", model="model-1", live=True)
        self.assertEqual(reservation["status"], "reserved")
        with self.assertRaises(BudgetAuthorizationError):
            ledger.reserve("call-2", 1, provider="other", model="model-1", live=True)
        with self.assertRaises(BudgetAuthorizationError):
            ledger.authorize({**authorization, "token_limit": 40})

    def test_pause_stop_and_control_stop_preserve_open_reservations(self):
        ledger = self.ledger(limits={"total_tokens": 20})
        reservation = ledger.reserve("call-1", 10)
        ledger.pause()
        with self.assertRaises(BudgetStateError):
            ledger.reserve("call-2", 1)
        ledger.resume()
        ledger.stop()
        with self.assertRaises(BudgetStateError):
            ledger.reserve("call-3", 1)
        self.assertEqual(ledger.status()["open_reservations"], 1)
        self.assertEqual(ledger.status()["state"], "STOPPED")
        self.assertEqual(reservation["reservation_id"], ledger.status()["reservations"][0]["reservation_id"])

    def test_stop_sentinel_blocks_before_lock_admission(self):
        ledger = self.ledger(limits={"total_tokens": 10})
        (self.root / "control" / "STOP").touch()
        with self.assertRaises(BudgetStateError):
            ledger.reserve("call-1", 1)
        self.assertEqual(ledger.read_events(), [])

    def test_threshold_alerts_are_idempotent_and_status_is_operational(self):
        ledger = self.ledger(limits={"total_tokens": 10})
        ledger.reserve("call-1", 6)
        first = ledger.check_alerts()
        second = ledger.check_alerts()
        alerts = [item for item in second if item["alert_code"] == "budget_threshold"]
        self.assertEqual(first, second)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(ledger.status()["available"]["total_tokens"], 4)

    def test_deadline_orphan_and_no_progress_alerts_are_durable(self):
        ledger = self.ledger(
            limits={"total_tokens": 100, "max_cycles_without_improvement": 1},
            orphan_after_seconds=5,
            deadline_at="2026-01-01T00:00:05Z",
        )
        ledger.reserve("call-1", 1)
        self.clock.advance(seconds=6)
        alerts = ledger.check_alerts(current_cycle=0)
        codes = {item["alert_code"] for item in alerts}
        self.assertTrue({"deadline", "orphan_reservation", "no_progress"}.issubset(codes))
        self.assertEqual(len(ledger.check_alerts(current_cycle=0)), len(alerts))

    def test_manual_clock_wall_time_and_limited_supervisor(self):
        ledger = self.ledger(limits={"total_tokens": 20, "max_calls": 2})
        supervisor = LimitedSupervisor(ledger, max_steps=1)
        result = supervisor.execute(
            "call-1", 10, lambda _: {"input_tokens": 2, "output_tokens": 3, "cache_tokens": 0, "wall_time_seconds": 4, "usage_available": True},
            receipt_id="receipt-1",
        )
        self.assertEqual(result["reconciled"]["usage_tokens"], 5)
        with self.assertRaises(BudgetExceeded):
            supervisor.execute("call-2", 1, lambda _: {}, receipt_id="receipt-2")

    def test_partial_or_tampered_budget_log_is_rejected(self):
        ledger = self.ledger(limits={"total_tokens": 10})
        ledger.reserve("call-1", 1)
        original = ledger.ledger_path.read_bytes()
        ledger.ledger_path.write_bytes(original[:-1])
        with self.assertRaises(BudgetIntegrityError):
            ledger.read_events()
        ledger.ledger_path.write_bytes(original)
        value = json.loads(original.splitlines()[0])
        value["payload"]["estimate_tokens"] = 2
        ledger.ledger_path.write_bytes(json.dumps(value).encode() + b"\n")
        with self.assertRaises(BudgetIntegrityError):
            ledger.read_events()


class M12ObservabilityTests(unittest.TestCase):
    def test_allowlist_redaction_and_rotation_preserve_only_safe_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir()
            logger = StructuredLogger(root, "run-1", max_bytes=1024)
            logger.emit("budget_reserved", {"role_id": "W11", "usage_tokens": 1, "secret": "do-not-write", "prompt": "private"})
            logger.emit("budget_reconciled", {"role_id": "W11", "usage_tokens": 2})
            logger.emit("budget_alert", {"alert_code": "budget_threshold", "threshold": 50})
            self.assertGreaterEqual(len(logger.status()["files"]), 2)
            text = "\n".join(path.read_text(encoding="utf-8") for path in (root / "logs").glob("*.jsonl"))
            self.assertNotIn("do-not-write", text)
            self.assertNotIn("private", text)
            self.assertEqual(len(logger.read_events()), 3)

    def test_logger_rejects_oversized_single_record_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control").mkdir()
            logger = StructuredLogger(root, "run-1", max_bytes=1024)
            with self.assertRaises(ObservabilityError):
                logger.emit("budget_reserved", {"reason_code": "x" * 600})
            logger.path.symlink_to(root / "outside")
            with self.assertRaises(ObservabilityError):
                logger.emit("budget_reserved", {"usage_tokens": 1})

    def test_disabled_project_profiles_are_not_activated_by_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "control").mkdir()
            shutil.copy(ROOT / "config" / "budgets.yaml", root / "config" / "budgets.yaml")
            with self.assertRaises(BudgetAuthorizationError):
                BudgetLedger.from_project(root, "run-1", profile="calibration")
            ledger = BudgetLedger.from_project(root, "run-1")
            with self.assertRaises(BudgetExceeded):
                ledger.reserve("call-1", 1)


if __name__ == "__main__":
    unittest.main()
