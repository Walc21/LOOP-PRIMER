# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Principles & Architecture

**LOOP-PRIMER** is engineered with strict deterministic and security guarantees:

1. **Air-Gapped & Offline Execution**: The core pipeline, gates, and synthesis routines run locally and offline by default. No network calls or unauthorized LLM API requests are triggered during gate verification.
2. **Content-Addressed Immutability**: All original inputs, extracted derivatives, manifests, and candidate versions are content-addressed and integrity-verified via SHA-256 digests.
3. **Anti-Traversal & Path Sanitization**: Archive ingestions (`source.zip`) are subject to strict anti-traversal, UTF-8 normalization, encryption checks, and symlink prohibition.
4. **Append-Only Auditing**: Durable state logs (`state/events/`, `docs/ai_sessions.jsonl`) enforce append-only discipline with cryptographic integrity chaining.

## Reporting a Vulnerability

If you discover a security vulnerability within LOOP-PRIMER:

1. **Do not** create a public issue.
2. Email details to `victor.gabriel@estudante.ufscar.br` with:
   - Description of the vulnerability.
   - Steps to reproduce or proof-of-concept.
   - Potential impact.
3. You will receive an acknowledgment within 48 hours and regular updates on the resolution.
