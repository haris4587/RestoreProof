# RestoreProof contribution

Category: Builder / Intelligent Contracts.

## Suggested title

RestoreProof — Evidence-backed Disaster Recovery Readiness

## Description

RestoreProof verifies whether documented recovery tests meet locked RTO, RPO and mandatory coverage requirements. The owner commits immutable policies and commit-pinned, SHA-256/byte-bound evidence; a distinct auditor wallet attests to each package. GenLayer validators independently fetch and review restoration logs, backup/application integrity checks, production-like exercises and runbooks. Custom equivalence checks compare independently derived semantic states and complete deterministic decisions, while grounding leader quotations in exact evidence. Outcomes are RECOVERY_READY, PARTIAL, FAILED or INCONCLUSIVE, with bounded retries and append-only hash-linked receipts. Includes 31 adversarial SDK tests, CI and reproducible deployment/evidence tools. Auditor attestation is a wallet assertion; readiness applies to supplied records at the locked reference time.

## Live assessment

Synthetic plan `demo-ready-001` finalized as RECOVERY_READY with majority agreement. Independently validated checks supported all four evidence categories. Deterministic RTO: 1,200 seconds against 1,800; RPO: 120 seconds against 300. Assessment transaction: https://explorer-studio.genlayer.com/tx/0x8ec9b147f42d157a101605ca27ff4837616d700897d00023d40c80eab6063e0f

Receipt: `deployments/demo-ready-001/assessment.json`. Decision hash: `e27ef19dd3fea5481afbf6625497b481af062b562eab693eba29931a35c638f7`. All four workflow writes finalized. Test, lint, SDK validation, type-check and ABI CI passed: https://github.com/haris4587/RestoreProof/actions/runs/41644285569

## Evidence

- Source: https://github.com/haris4587/RestoreProof/blob/main/contracts/restore_proof.py
- Tests: https://github.com/haris4587/RestoreProof/blob/main/tests/test_restoreproof.py
- Deployment: https://explorer-studio.genlayer.com/tx/0xa6ed3c893c2c206ab7e123c6aeb4dc7809460e741dfc09e14486de919bfe5472
- Public deployment and assessment exports: https://github.com/haris4587/RestoreProof/tree/main/deployments
- CI: https://github.com/haris4587/RestoreProof/actions

The deployed contract is on hosted Studionet (chain 61999), not mainnet. Demo records are synthetic. Successful deployment alone does not prove a completed semantic assessment; use the assessment transaction and exported receipt when present. No contribution submission is sent automatically by these tools.
