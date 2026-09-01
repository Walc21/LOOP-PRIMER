# Contributing to LOOP-PRIMER

Thank you for your interest in contributing to **LOOP-PRIMER**! We welcome contributions that maintain the mathematical rigor, determinism, and auditability of the framework.

---

## Development Principles

1. **Deterministic Contracts**: All state transitions, evaluation gates, and candidate syntheses must be deterministic and fully reproducible.
2. **Contract-First Testing**: Any new feature or modification must be accompanied by unit tests adhering to the contract suites in `control/`.
3. **No Unauthenticated Execution**: Modules must not trigger external API calls or non-reproducible external models without explicit orchestrator permission.
4. **Architecture Decision Records (ADRs)**: Significant architectural decisions must be documented in `docs/decisions.md` following the established ADR format.

---

## Getting Started

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Walc21/LOOP-PRIMER.git
   cd LOOP-PRIMER
   ```

2. **Run Dependency Bootstrap**:
   ```bash
   bash bin/bootstrap-deps.sh
   ```
   Or set up a virtual environment manually:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Run Contract Tests**:
   ```bash
   .venv/bin/python -m unittest control.test_contracts
   .venv/bin/python -m unittest control.test_ai_handoff
   ```

---

## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(milestone)`: A new feature or milestone implementation.
- `fix(milestone)`: A bug fix or gate hardening.
- `docs(adrs)`: Documentation updates or new ADR records.
- `test(contracts)`: Adding or updating contract tests.
- `refactor(core)`: Code refactoring without behavioral modification.

---

## Pull Request Checklist

Before submitting a Pull Request:
- [ ] All contract and unit tests pass (`python3 -m unittest discover -s control`).
- [ ] Code compiles without warnings (`python3 -m py_compile ...`).
- [ ] All JSON schemas validate correctly against sample manifests.
- [ ] `AI_CONTEXT.md` and documentation are updated if architectural signatures changed.
