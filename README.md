<div align="center">

# 🔬 LOOP-PRIMER
### Autonomous Multi-Agent Peer Review & Refinement Framework for Scientific & Mathematical Manuscripts

[![CI Suite](https://github.com/Walc21/LOOP-PRIMER/actions/workflows/ci.yml/badge.svg)](https://github.com/Walc21/LOOP-PRIMER/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Architecture: RLM](https://img.shields.io/badge/Architecture-RLM%20(Max%20Depth%202)-purple.svg)](docs/architecture.md)
[![Agents: 21 Roles](https://img.shields.io/badge/Agents-21%20Specialized%20Roles-orange.svg)](docs/architecture.md#catálogo-exato-de-21-papéis)
[![Verification: Deterministic Gates](https://img.shields.io/badge/Verification-13%20Deterministic%20Gates-red.svg)](docs/decisions.md)

<p align="center">
  <b>A deterministic, auditable multi-agent review loop engineered for LaTeX and PDF scientific literature.</b>
</p>

</div>

> **Implementation status:** M0–M14 are implemented structurally and validated
> offline. M13 adds system acceptance and independent delivery verification;
> M13.1–M13.2 harden routed evaluator identity, test-double boundaries,
> durability, workspace binding and jury anonymization. M14 adds a local
> loopback Control Center with read-only projections, resumable events, typed
> configuration drafts, canonical controls and an independent audit ledger.
> M10 publishes a canonical, content-addressed `Decision`; M10 CLIs are operational within their documented fail-closed boundaries.
> The code remains fail-closed: it does not run an article, model, Prime Agent,
> provider or paid API by itself. A future live execution still requires explicit
> human authorization, configuration, budget, content policy and preflight.

---

### Offline system acceptance

Run `python3 scripts/m13_system_check.py` to verify synthetic cycles from
immutable ingestion through promotion, Pareto archival or rejection, including
tamper detection, recovery and replay. It uses deterministic external test
adapters and requires no model, credentials or network. To retain evidence and
audit a completed delivery separately, see
[M13 acceptance and verification](docs/m13-system-acceptance.md).

## 📌 Table of Contents

- [Executive Summary](#-executive-summary)
- [Key Architectural Pillars](#-key-architectural-pillars)
- [System Pipeline Flow](#-system-pipeline-flow)
- [The 21-Agent Matrix](#-the-21-agent-matrix)
- [Deterministic Gates & Security](#-deterministic-gates--security)
- [Quick Start](#-quick-start)
- [CLI Reference](#-cli-reference)
- [Local Control Center](docs/control-center.md)
- [Runbook](docs/runbook.md)
- [Repository Structure](#-repository-structure)
- [Architecture Decision Records (ADRs)](#-architecture-decision-records-adrs)
- [Contributing & License](#-contributing--license)

---

## 🔭 Executive Summary

**LOOP-PRIMER** is a contract-first, deterministic framework under incremental
implementation for auditable analysis, critique, mathematical verification and
iterative improvement of scientific papers. Its durable state machine,
orchestration contracts, gates, jury, diagnosis, decision and finalization are
implemented; M11–M14 add fail-closed operations, budget/observability, routing,
offline system acceptance, structural hardening and a local Control Center.

Unlike conventional LLM wrappers, LOOP-PRIMER operates under **strict mathematical and architectural constraints**:
- **Offline Contract Verification**: Local validation uses deterministic fixtures and does not require a model, provider or paid API.
- **Content-Addressed Immutability**: Cryptographic SHA-256 fingerprinting for every manuscript version, diff, report, and decision.
- **Hierarchical Depth Boundary (Max Depth 2)**: Strict 21-agent hierarchy preventing uncontrolled recursion or authority escalation.
- **Blind External Jury**: Double-blind randomized evaluation with meta-reviewer consensus before candidate promotion.
- **Transactional Finalizer**: Atomic champion upgrades and Pareto frontier tracking with hash-bound audit receipts.
- **Finalization Evidence Package**: W22/W51/W53 attestations bind the final
  candidate manifest, rendered PDF and final report before `FINALIZE`; crash
  recovery derives the same receipt instead of repeating an effect.

---

## 🏛 Key Architectural Pillars

```
+-----------------------------------------------------------------------------------+
|                                  LOOP-PRIMER                                      |
+-----------------------------------------------------------------------------------+
|  1. Ingestion & Invariants (SHA-256, Anti-Traversal, UTF-8 Normalization)         |
|  2. 21 Hierarchical Roles (General Direction -> 5 Departments -> 15 Workers)      |
|  3. Sparse Activation Engine (RUN, CHECK, SHIFT, FREEZE)                          |
|  4. 13 Deterministic Synthesis Gates (LaTeX Syntax, Theorem Proofs, BibTeX)      |
|  5. Blind External Jury & Meta-Review (Double-Blind Candidate Evaluation)         |
|  6. Stagnation Detection & Adaptive Refocusing (Plateau & Oscillation Analytics)  |
|  7. M10 Decision Policy, Pareto Evidence & Transactional Finalization             |
|  8. Transactional State Machine & Append-Only Event Chaining                      |
|  9. M14 Local Control Center (Loopback Projections & Canonical Controls)          |
+-----------------------------------------------------------------------------------+
```

---

## 🔄 System Pipeline Flow

```mermaid
flowchart TD
    A["📄 Input Manuscript (input/inbox/artigo.pdf or source.zip)"] --> B["🔒 SHA-256 Content-Addressed Staging"]
    B --> C{"🛡️ Gate: SOURCE_READY\n(Anti-Traversal & Integrity Check)"}

    C -->|Pass| D["👑 Publish Initial Champion (v0000)"]
    C -->|Fail| ERR["❌ Reject Ingestion (No Artifact Overwrite)"]

    D --> E["🎯 M00: General Direction & Agenda Synthesis"]

    subgraph S_DEP ["Departmental Sparse Activation & Proposal Generation"]
        E --> S10["S10: Structural & Logic Audit"]
        E --> S20["S20: Mathematical Verification"]
        E --> S30["S30: Mathematical Strengthening"]
        E --> S40["S40: Textual & Semantic Precision"]
        E --> S50["S50: LaTeX & Layout Formatting"]

        S10 -.-> W_AUD["W11, W12, W13 Workers"]
        S20 -.-> W_VER["W21, W22, W23 Workers"]
        S30 -.-> W_STR["W31, W32, W33 Workers"]
        S40 -.-> W_SEM["W41, W42, W43 Workers"]
        S50 -.-> W_LAT["W51, W52, W53 Workers"]
    end

    S_DEP --> F["🔬 S20 Formal Math Cross-Verification"]
    F --> G["🧩 Candidate Synthesis (versions/challengers/vXXXX)"]

    G --> H{"🚦 13 Deterministic Gates\n(LaTeX, Math Proofs, Citations)"}
    H -->|Fail| I["📦 Archive to versions/rejected/"]
    H -->|Pass| J["⚖️ M8: Blind External Jury Evaluation"]

    J --> L["📈 M9: Stagnation & Oscillation Detector"]
    L --> M["🧭 M10: Canonical decision policy"]
    M -->|PROMOTE| P["🏁 Transactional champion upgrade"]
    M -->|ARCHIVE_PARETO / REJECT| N["📊 Immutable Pareto / rejected reference"]
    M -->|REFOCUS / CONTINUE / extra judgment| O["🔄 Durable next-cycle preparation"]
    O --> E
    M -->|PAUSE / FINALIZE / technical abort| Q["🔒 Checkpointed terminal or paused state"]

    CC["🖥️ M14 Local Control Center\n(loopback only)"] -.->|projects durable state| D
    CC -.->|canonical controls only| M
```

---

## 👥 The 21-Agent Matrix

LOOP-PRIMER establishes a strict 3-tier organizational hierarchy:

| ID | Role Name | Department | Depth | Focal Responsibility |
|:---|:---|:---|:---:|:---|
| **M00** | **General Director** | Direction | `0` | Strategic agenda, synthesis, gate verification, decision finalization |
| **S10** | **Lead Structural Auditor** | Structural/Auditing | `1` | Global logic, structural hierarchy, consistency audit |
| `W11` | Abstract & Introduction Worker | Structural/Auditing | `2` | Framing, thesis clarity, intro-to-conclusion alignment |
| `W12` | Logical Architecture Worker | Structural/Auditing | `2` | Argument flow, lemma dependency DAG, section transitions |
| `W13` | Contributions & Conclusion Worker | Structural/Auditing | `2` | Claim precision, future work bounds, conclusion integrity |
| **S20** | **Lead Math Verifier** | Math Verification | `1` | Formal rigor, theorem correctness, reproducibility consolidation |
| `W21` | Definitions & Hypotheses Worker | Math Verification | `2` | Axiomatic precision, notation consistency, hypothesis audit |
| `W22` | Theorems & Proofs Worker | Math Verification | `2` | Step-by-step deductive correctness, lemma soundness |
| `W23` | Computations & Reproducibility | Math Verification | `2` | Constant calculation, numerical examples, proof verification |
| **S30** | **Lead Math Strengthener** | Math Strengthening | `1` | Generalization and theorem strengthening consolidation |
| `W31` | Statements & Constants Worker | Math Strengthening | `2` | Tightening bounds, optimizing constants, statement sharpening |
| `W32` | Generalizations Worker | Math Strengthening | `2` | Extending proof domains, weakening preconditions |
| `W33` | Applications & Counterexamples | Math Strengthening | `2` | Instructive examples, edge cases, boundary checks |
| **S40** | **Lead Semantic Auditor** | Semantic Quality | `1` | Technical prose, linguistic clarity, academic cohesion |
| `W41` | Orthography & Grammar Worker | Semantic Quality | `2` | Syntax correctness, spelling, typographical standards |
| `W42` | Semantic Precision Worker | Semantic Quality | `2` | Eliminating ambiguity, sharpening technical vocabulary |
| `W43` | Academic Style & Cohesion | Semantic Quality | `2` | Tone harmonization, register consistency, academic cadence |
| **S50** | **Lead LaTeX & Layout** | Formatting/PDF | `1` | Compilation compliance, typographic beauty, PDF hygiene |
| `W51` | LaTeX & BibTeX Worker | Formatting/PDF | `2` | Macro hygiene, citation consistency, bibliography validation |
| `W52` | Equations & Visuals Worker | Formatting/PDF | `2` | Formula alignment, float placement, table/figure formatting |
| `W53` | PDF Compliance Worker | Formatting/PDF | `2` | PDF/A standard checks, font embedding, margin validation |

---

## 🔒 Deterministic Gates & Security

LOOP-PRIMER enforces security by construction:

1. **Gate Guardrails**: Missing or insufficient deterministic evidence fails closed. If OCR confidence or textual coverage is insufficient, execution halts with explicit issue diagnostics.
2. **Immutable Original Staging**: Manuscripts placed in `input/inbox/` are never overwritten in-place. Staging creates content-addressed read-only mirrors in `artifacts/original/<sha256>/`.
3. **Cryptographic Chaining**: Every state mutation records an event in `state/events/` referencing parent hashes.
4. **Offline Isolation**: Core contract tests require no model, provider or paid API key; live execution remains separately authorized and fail-closed.
5. **Local Control Center**: M14 binds only to `127.0.0.1`, serves no arbitrary files or shell, and delegates only confirmed canonical controls.

---

## 🚀 Quick Start

### 1. Prerequisites

- Linux (Ubuntu 22.04+, Debian 12+, Arch, etc.) or macOS
- Python 3.11+
- TeX Live & Poppler (`pdflatex`, `pdfinfo`, `pdftotext`) — required by the full regression suite and installed by `bin/bootstrap-deps.sh` on Debian/Ubuntu

### 2. Installation & Automated Bootstrap

```bash
# Clone the repository
git clone https://github.com/Walc21/LOOP-PRIMER.git
cd LOOP-PRIMER

# Automated system dependencies and virtual environment setup
bash bin/bootstrap-deps.sh
```

Or set up manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 3. Running Contract & Verification Tests

```bash
# Run core contract tests
.venv/bin/python -m unittest control.test_contracts

# Run AI context and handoff tests
.venv/bin/python -m unittest control.test_ai_handoff

# Run the complete M0-M14 regression suite
.venv/bin/python -m unittest discover -s control -p 'test_*.py' -q
```

### 4. Running Preflight Ingestion

Place your paper PDF in `input/inbox/artigo.pdf` and execute:

```bash
bash bin/preflight.sh
```

### 5. Opening the Local Control Center

Start the M14 interface through its canonical loopback launcher:

```bash
bash bin/start-control-center.sh
```

Then open `http://127.0.0.1:8765`. Do not open
`control_center_static/index.html` directly with `file://`: that mode does not
provide the Central's `/assets/` resources or its `/api/v1` backend. To use a
different local port, pass `--port` as documented in
[the Control Center guide](docs/control-center.md).

---

## 🧰 CLI Reference

LOOP-PRIMER provides modular, JSON-in / JSON-out CLI entrypoints:

- **`bin/preflight.sh`**: Ingestion, validation, and `SOURCE_READY` gate verifier.
- **`bin/check.sh`**: Fast local integrity and fail-closed readiness check for the operational surfaces; it does not start Prime Agent or a model.
- **`bin/start-control-center.sh`**: Starts the M14 Control Center only through its canonical `127.0.0.1` server. See [the local guide](docs/control-center.md).
- **`bin/start-prime.sh`**: Dry-run-by-default launcher; live mode requires
  explicit authorization, budget/configuration, preflight, STOP clearance and
  a discovered Prime Agent binary.
- **`scripts/article_loop_command.py`**: Thin JSON-in / JSON-out bridge for
  the existing bootstrap, preflight, cycle, status, checkpoint, pause, resume,
  stop and finalization APIs. See [`docs/runbook.md`](docs/runbook.md).
- **`scripts/01_external_evaluator.py`**: Double-blind jury evaluator CLI (Milestone 8).
- **`scripts/02_stagnation_detector.py`**: Plateau, oscillation, and diagnostic detector (Milestone 9).
- **`scripts/03_refocus_generator.py`**: Adaptive prompt and parameter refocusing generator (Milestone 9).
- **`scripts/04_compensation_policy.py`**: Revalidates M7–M9 evidence and
  publishes one immutable M10 `Decision`; accepts `--root`, `--run-id`,
  `--cycle-id` or the equivalent bounded JSON input.
- **`scripts/05_transactional_finalizer.py`**: Revalidates the published
  `Decision`, candidate and evidence package under a per-run lock, then records
  the atomic disposition and immutable receipt. A retry after a receipt-only
  crash records only the pending event/checkpoint.
- **`scripts/ai_context.py`**: Deterministic content-addressed session context snapshot generator.
- **`scripts/ai_history.py`**: Session ledger and ADR history updater.

---

## 📂 Repository Structure

```text
LOOP-PRIMER/
├── .github/                      # GitHub Actions CI & community templates
│   ├── workflows/ci.yml          # Multi-Python version test suite
│   ├── copilot-instructions.md   # GitHub Copilot entrypoint
│   ├── pull_request_template.md  # PR checklist and verification template
│   └── ISSUE_TEMPLATE/           # Bug report & feature request schemas
├── .prime/                       # Prime Agent integration layer, prompts and local skills
│   └── agent/skills/article-loop/src/article_loop/ # Core framework, including M10-M14 modules
├── bin/                          # Shell entrypoints (bootstrap, preflight, checks, Prime and Control Center launchers)
├── config/                       # Declarative budgets, gates, roles, policy, and JSON schemas
│   ├── roles/                    # 21 YAML definitions for M00, S10-S50, W11-W53
│   ├── rubrics/                  # Evaluation rubrics for blind jury
│   └── schemas/                  # JSON Schema definitions for strict validation
├── control/                      # Contract and milestone test suites (M1 through M14)
├── docs/                         # Architecture, ADRs, compatibility, and AI history
│   ├── architecture.md           # Canonical system architecture
│   ├── decisions.md              # Architectural Decision Records (ADRs)
│   ├── control-center.md         # M14 loopback Control Center operation guide
│   ├── runbook.md                # Local M11/M12/M12.5.1 operation and recovery guide
│   └── AI_HISTORY.md             # Chronological ledger of system evolution
├── .prime/agent/prompts/         # Immutable project-local command prompts
├── scripts/                      # Independent, deterministically tested CLI modules
├── artifacts/                    # Content-addressed input & extracted cache (gitignored)
├── state/                        # Append-only durable event logs, locks and Control Center audit state
├── versions/                     # Champion, challenger, Pareto & rejected versions
├── requirements-dev.txt          # Pinned development dependencies
├── AGENTS.md                     # Canonical policy for AI coding agents
├── CLAUDE.md                     # Claude adapter to AGENTS.md
├── GEMINI.md                     # Gemini adapter to AGENTS.md
├── AI_CONTEXT.md                 # Portable generated context for AI sessions
├── LICENSE                       # MIT License
├── CONTRIBUTING.md               # Contribution guidelines & commit convention
└── SECURITY.md                   # Security and sandboxing policy
```

---

## 📜 Architecture Decision Records (ADRs)

All core design choices are formally recorded in [`docs/decisions.md`](docs/decisions.md):

| ADR | Title | Status | Scope |
|:---|:---|:---:|:---|
| **ADR-001** | Estado durável próprio | `Accepted` | Base do repositório |
| **ADR-002** | Topologia lógica 1 + 5 + 15 e profundidade RLM 2 | `Accepted` | Organização |
| **ADR-003** | Mensagem curta, arquivo canônico | `Accepted` | Handoff |
| **ADR-008** | Ordem transacional do pipeline | `Accepted` | Estado e evidência |
| **ADR-013** | Replay semântico e commit transacional do event log | `Accepted` | Recuperação |
| **ADR-021** | Blackboard append-only e planejamento determinístico | `Accepted` | M5 |
| **ADR-024** | Júri externo cego e meta-review | `Accepted` | M8 |
| **ADR-028** | Política pura e finalização transacional | `Accepted` | M10 |
| **ADR-029** | Pacote final canônico e recuperação por fase | `Accepted` | M10.1 |
| **ADR-030** | Comandos locais e integração Prime fail-closed | `Accepted` | M11 |
| **ADR-031** | Orçamento durável e observabilidade fail-closed | `Accepted` | M12 |
| **ADR-032** | Routing determinístico governado pelo ledger | `Accepted` | M12.5 |
| **ADR-033** | Execução dual ligada ao contrato M6 | `Accepted` | M12.5.1 |
| **ADR-034–036** | Aceitação M13 e hardening estrutural | `Accepted` | M13–M13.2 |
| **ADR-037** | Central de Controle local | `Implemented` | M14 |
| **ADR-038** | Inicialização pelo servidor local canônico | `Implemented` | M14 |
| **ADR-026** | Handoff compacto e histórico de sessões de IA | `Accepted` | Protocolo de IA |
| **ADR-027** | Separação de audiências e histórico Git publicável | `Accepted` | Integração do repositório |

---

## 🤝 Contributing & License

Contributions are welcome! Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md) before opening pull requests.

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for complete details.

**Author**: Victor Gabriel de Oliveira ([@Walc21](https://github.com/Walc21))
