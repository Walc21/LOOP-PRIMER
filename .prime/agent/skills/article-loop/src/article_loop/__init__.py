"""Public API."""
from .state_machine import State, TransitionError
from .store import DurableStore, IntegrityError, StopRequested, StoreError
from .ingestion import IngestionError, SourceReadyError, ingest
from .prompts import CompiledPrompt, INTERNAL_SCHEMAS, OUTPUT_SCHEMAS, PromptContractError, PromptIntegrityError, PromptRegistry, compile_manager_prompt, compile_prompt, expected_prompt_version, validate_output
from .blackboard import Blackboard, BlackboardError, Impact, ImpactGraph, stable_claim_id
from .activation import ActivationEntry, ActivationMode, ActivationPlan, ActivationPlanner, PlanningLimits, manager_view, specialist_view, submanager_view
from .adapters import ChildHandle, FakeRLMAdapter, PrimeRLMAdapter
from .orchestrator import Orchestrator
__version__ = "0.4.0"

async def bootstrap(pdf_path, root="."): return await Orchestrator(root).bootstrap(pdf_path)
async def preflight(root="."): return await Orchestrator(root).preflight()
async def run_cycle(root=".", cycle_id=None, dry_run=False): return await Orchestrator(root).run_cycle(cycle_id=cycle_id, dry_run=dry_run)
async def status(root="."): return await Orchestrator(root).status()
async def checkpoint(root="."): return await Orchestrator(root).checkpoint(Orchestrator(root)._only_run())
async def pause(root="."): return await Orchestrator(root).pause(Orchestrator(root)._only_run())
async def resume(root="."): return await Orchestrator(root).resume(Orchestrator(root)._only_run())
async def stop(root="."): return await Orchestrator(root).stop(Orchestrator(root)._only_run())
async def finalize(root="."): return await Orchestrator(root).finalize(Orchestrator(root)._only_run())
async def run(*args, **kwargs): return await run_cycle(*args, **kwargs)
__all__ = ["ActivationEntry", "ActivationMode", "ActivationPlan", "ActivationPlanner", "Blackboard", "BlackboardError", "ChildHandle", "CompiledPrompt", "DurableStore", "FakeRLMAdapter", "INTERNAL_SCHEMAS", "Impact", "ImpactGraph", "IngestionError", "IntegrityError", "OUTPUT_SCHEMAS", "Orchestrator", "PlanningLimits", "PrimeRLMAdapter", "PromptContractError", "PromptIntegrityError", "PromptRegistry", "SourceReadyError", "State", "StopRequested", "StoreError", "TransitionError", "bootstrap", "checkpoint", "compile_manager_prompt", "compile_prompt", "expected_prompt_version", "finalize", "ingest", "manager_view", "pause", "preflight", "resume", "run", "run_cycle", "specialist_view", "stable_claim_id", "status", "stop", "submanager_view", "validate_output"]
