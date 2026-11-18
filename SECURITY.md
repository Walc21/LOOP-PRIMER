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

Use GitHub's private vulnerability reporting form. Include the affected
version, a description of the issue, reproduction steps, and the potential
impact. Redact credentials and personal data from any attachments.
[Report a vulnerability privately](https://github.com/Walc21/LOOP-PRIMER/security/advisories/new)
