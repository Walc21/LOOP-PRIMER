"""Public API."""
from .state_machine import State, TransitionError
from .store import DurableStore, IntegrityError, StopRequested, StoreError
from .ingestion import IngestionError, SourceReadyError, ingest
from .prompts import CompiledPrompt, INTERNAL_SCHEMAS, OUTPUT_SCHEMAS, PromptContractError, PromptIntegrityError, PromptRegistry, compile_manager_prompt, compile_prompt, expected_prompt_version, validate_output
from .blackboard import Blackboard, BlackboardError, Impact, ImpactGraph, stable_claim_id
from .activation import ActivationEntry, ActivationMode, ActivationPlan, ActivationPlanner, PlanningLimits, manager_view, specialist_view, submanager_view
from .adapters import ChildHandle, FakeRLMAdapter, PrimeRLMAdapter
from .orchestrator import Orchestrator, OrchestrationError
from .synthesis import M7Pipeline, SynthesisError, tree_hash
from .gates import compare, run_gates
from .evaluation import (
    BlindComparisonBundle,
    EvaluationError,
    FakeJurorAdapter,
    FakeMetaReviewerAdapter,
    check_inversion_consistency,
    evaluate_candidate,
    load_rubric,
)
from .diagnosis import (
    DiagnosisError,
    classify_cycle_progress,
    diagnose_cycle,
    load_history_series,
    verify_published_diagnosis,
)
from .refocus import (
    RefocusError,
    generate_refocus_plan,
    register_overlay_cas,
)
from .policy import PolicyError, choose_action, decide, load_policy, load_published_decision, pareto_relation
from .finalization import FinalizationError, TransactionalFinalizer, finalize_decision
from .budget import (
    BudgetAuthorizationError, BudgetError, BudgetExceeded, BudgetIdempotencyError,
    BudgetIntegrityError, BudgetLedger, BudgetLimits, BudgetStateError,
    LimitedSupervisor, ManualClock, RunAuthorization, load_budget_config,
)
from .observability import ObservabilityError, StructuredLogger, redact_payload
from .inference import (
    InferenceBackend, InferenceBackendError, InferenceConfigError, InferenceError,
    InferenceIntegrityError, InferenceOutputError, InferenceReceipt,
    InferenceRequest, InferenceResult, InferenceRuntime, InferenceStore,
    InferenceTarget, ModelRegistry, ModelRouter, RouteDecision,
    TargetPricing, agent_proposal_payload_schema, compose_agent_proposal,
    inference_preflight, model_output_schema, output_identity_matches,
    output_identity_values, routing_policy_hash, trusted_protocol_envelope,
)
from .inference_backends import FakeInferenceBackend, LocalOpenAICompatibleBackend, RemoteOpenAICompatibleBackend
from .execution import (
    ContextItem, ContextMaterializer, DualExecutionAdapter,
    DualExecutionController, ExecutionError, ExecutionPolicy,
    MaterializedContext, RoutedControlAdapter, execution_readiness,
)
from .delivery import DeliveryError, verify_delivery

__version__ = "0.7.0"

async def bootstrap(pdf_path, root="."): return await Orchestrator(root).bootstrap(pdf_path)
async def preflight(root="."): return await Orchestrator(root).preflight()
async def run_cycle(root=".", cycle_id=None, dry_run=False): return await Orchestrator(root).run_cycle(cycle_id=cycle_id, dry_run=dry_run)
async def status(root="."): return await Orchestrator(root).status()
async def checkpoint(root="."): return await Orchestrator(root).checkpoint(Orchestrator(root)._only_run())
async def pause(root="."): return await Orchestrator(root).pause(Orchestrator(root)._only_run())
async def resume(root="."): return await Orchestrator(root).resume(Orchestrator(root)._only_run())
async def stop(root="."): return await Orchestrator(root).stop(Orchestrator(root)._only_run())
async def finalize(root="."): return finalize_decision(root, Orchestrator(root)._only_run())
async def run(*args, **kwargs): return await run_cycle(*args, **kwargs)

__all__ = [
    "ActivationEntry", "ActivationMode", "ActivationPlan", "ActivationPlanner",
    "Blackboard", "BlackboardError", "BlindComparisonBundle", "ChildHandle",
    "CompiledPrompt", "DeliveryError", "DiagnosisError", "DurableStore", "EvaluationError",
    "FakeJurorAdapter", "FakeMetaReviewerAdapter", "FakeRLMAdapter",
    "INTERNAL_SCHEMAS", "Impact", "ImpactGraph", "IngestionError",
    "IntegrityError", "M7Pipeline", "OUTPUT_SCHEMAS", "Orchestrator",
    "OrchestrationError", "PlanningLimits", "PrimeRLMAdapter",
    "PromptContractError", "PromptIntegrityError", "PromptRegistry",
    "RefocusError", "SourceReadyError", "State", "StopRequested", "StoreError",
    "PolicyError", "FinalizationError", "TransactionalFinalizer",
    "SynthesisError", "TransitionError", "bootstrap", "checkpoint",
    "BudgetAuthorizationError", "BudgetError", "BudgetExceeded",
    "BudgetIdempotencyError", "BudgetIntegrityError", "BudgetLedger",
    "BudgetLimits", "BudgetStateError", "LimitedSupervisor", "ManualClock",
    "RunAuthorization", "load_budget_config", "ObservabilityError",
    "StructuredLogger", "redact_payload",
    "InferenceBackend", "InferenceBackendError", "InferenceConfigError",
    "InferenceError", "InferenceIntegrityError", "InferenceOutputError",
    "InferenceReceipt", "InferenceRequest", "InferenceResult",
    "InferenceRuntime", "InferenceStore", "InferenceTarget", "ModelRegistry",
    "ModelRouter", "RouteDecision", "TargetPricing", "FakeInferenceBackend",
    "LocalOpenAICompatibleBackend", "RemoteOpenAICompatibleBackend",
    "ContextItem", "ContextMaterializer", "DualExecutionAdapter",
    "DualExecutionController", "ExecutionError", "ExecutionPolicy",
    "MaterializedContext", "RoutedControlAdapter", "execution_readiness",
    "inference_preflight",
    "agent_proposal_payload_schema", "compose_agent_proposal",
    "model_output_schema", "output_identity_matches", "output_identity_values",
    "routing_policy_hash", "trusted_protocol_envelope",
    "check_inversion_consistency", "classify_cycle_progress", "compare",
    "choose_action", "compile_manager_prompt", "compile_prompt", "decide", "diagnose_cycle",
    "evaluate_candidate", "expected_prompt_version", "finalize", "finalize_decision",
    "generate_refocus_plan", "ingest", "load_history_series", "load_policy", "load_published_decision", "load_rubric", "pareto_relation",
    "manager_view", "pause", "preflight", "register_overlay_cas", "resume",
    "run", "run_cycle", "run_gates", "specialist_view", "stable_claim_id",
    "status", "stop", "submanager_view", "tree_hash", "validate_output",
    "verify_delivery", "verify_published_diagnosis",
]
