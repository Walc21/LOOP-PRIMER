"""Bounded Atheris target for local M2/M6 replay and run identifiers.

Every filesystem write uses a fixed path in a disposable root. Fuzzed run IDs
are passed only to the identifier validators, never to filesystem operations.
No Prime adapter, backend, model or scientific run is started.
"""
from pathlib import Path
import sys
import tempfile

import atheris

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

with atheris.instrument_imports():
    from article_loop.store import DurableStore, StoreError
    from article_loop.orchestrator import Orchestrator, OrchestrationError


class JournalTarget:
    def __init__(self, root: Path):
        self.root = root
        self.store = DurableStore(root)
        self.orchestrator = Orchestrator(root)
        self.store_path = root / "state/events/fuzz.jsonl"
        self.orchestration_path = self.orchestrator._file("fuzz", "journal.jsonl")

    @atheris.instrument_func
    def __call__(self, data: bytes) -> None:
        if len(data) > 4096:
            return
        kind, raw = data[:1], data[1:]
        if kind == b"I":
            run = raw.decode("utf-8", errors="replace")
            for validate in (self.store._run_id, self.orchestrator._run):
                try:
                    accepted = validate(run)
                except (StoreError, OrchestrationError):
                    continue
                # Independent containment property, including absolute paths,
                # traversal, Windows separators and embedded control bytes.
                path = self.root / accepted
                assert path.parent == self.root
                assert "\\" not in accepted and "\x00" not in accepted
            return

        if kind == b"O":
            path, read = self.orchestration_path, self.orchestrator._events
        else:
            path, read = self.store_path, self.store.read_events
            if kind != b"S":
                raw = data
        path.write_bytes(raw)
        try:
            events = read("fuzz")
        except (StoreError, OrchestrationError):
            return
        assert events == read("fuzz"), "replay must be deterministic"
        assert path.read_bytes() == raw, "replay must preserve journal evidence"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="article-loop-fuzz-") as temporary:
        target = JournalTarget(Path(temporary))
        atheris.Setup(sys.argv, target)
        atheris.Fuzz()


if __name__ == "__main__":
    main()
