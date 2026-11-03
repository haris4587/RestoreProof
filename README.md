# RestoreProof

Evidence-backed disaster recovery readiness verification on GenLayer. A successful backup does not establish that an application can actually be recovered. RestoreProof combines independently validated semantic review of recovery records with deterministic recovery-time, data-loss, and test-coverage checks.

## Contract primitive

An organization owner locks immutable recovery requirements, commits exact evidence files, obtains a separate auditor wallet's attestation, and requests an assessment. Each participating validator independently retrieves and hashes the evidence and performs its own AI analysis. Deterministic code derives the outcome. Receipts and per-plan event hash chains preserve the policy, evidence commitment, decision and bounded assessment history.

This is a standalone Intelligent Contract with Python operator tools; no frontend is required.

| Outcome | Deterministic rule |
| --- | --- |
| `RECOVERY_READY` | Every requirement has complete, fresh, supported evidence for a production-like recovery test, meeting RTO and RPO; no submitted test is incomplete or failing. |
| `PARTIAL` | At least one requirement is ready, others remain unknown, and none fails. |
| `FAILED` | Any fresh test demonstrates an RTO/RPO breach, failed restore, failed integrity/application checks, failed exercise, or semantic contradiction. |
| `INCONCLUSIVE` | No requirement is ready and none fails, or evidence retrieval/validation or model-output validation fails. |

Fresh failure takes precedence even if another test succeeds. Stale evidence cannot establish current readiness or current failure. Unknown semantic checks never count as support. A consensus disagreement may prevent a transaction from committing; it is not automatically converted into an assessment receipt.

## Live demonstration

[![RestoreProof checks](https://github.com/haris4587/RestoreProof/actions/workflows/ci.yml/badge.svg)](https://github.com/haris4587/RestoreProof/actions/workflows/ci.yml)

- Network: **Studionet**, chain **61999** (hosted development network).
- Contract: [`0xd2e3a3f5c5db35a26C5F20E8930eA908BdC23a70`](https://explorer-studio.genlayer.com/contracts/0xd2e3a3f5c5db35a26C5F20E8930eA908BdC23a70)
- Deployment (FINALIZED): [`0xa6ed3c893c2c206ab7e123c6aeb4dc7809460e741dfc09e14486de919bfe5472`](https://explorer-studio.genlayer.com/tx/0xa6ed3c893c2c206ab7e123c6aeb4dc7809460e741dfc09e14486de919bfe5472)
- Source SHA-256: `acb9ad7ecc5ddef4736e353318c199268e3118b2dd91a50de56d230915771814`.
- Evidence is pinned to commit `59a591374cf6afe5257db4438c57d887ec07004f`; the sample describes a synthetic hotel booking database recovery.

The synthetic `demo-ready-001` assessment **FINALIZED as RECOVERY_READY** with majority agreement. RTO was **1,200 / 1,800 seconds**, RPO **120 / 300 seconds**, and all four evidence checks were supported. [Assessment transaction](https://explorer-studio.genlayer.com/tx/0x8ec9b147f42d157a101605ca27ff4837616d700897d00023d40c80eab6063e0f) · [receipt](deployments/demo-ready-001/assessment.json) · [event history](deployments/demo-ready-001/events.json). This is a demonstration using fabricated sample records, not a real hotel readiness certification.

See [deployment instructions](DEPLOYMENT.md), [evidence format](EVIDENCE.md), [security assumptions](SECURITY.md), and [submission notes](SUBMISSION.md). Public deployment records are in `deployments/`.

## Quick verification

Python 3.12 is the tested environment.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export GENVM_VERSION=v0.2.16
genvm-lint check contracts/restore_proof.py
genvm-lint typecheck contracts/restore_proof.py
pytest -q tests
genvm-lint schema contracts/restore_proof.py --output artifacts/abi.json
```

The 31 direct GenVM SDK tests use mocked web/model responses, exercise independent validator callbacks, and require no wallet or live RPC. They cover ready/partial/failure/inconclusive outcomes, stale and missing evidence, tabletop exercises, permissions, immutability, forged quotations, bad hashes, URL restrictions, malformed AI output, forged leader decisions, independent semantic disagreement, plan isolation and retry/history integrity. They complement the live consensus demonstration rather than simulate live model reliability.

## API

| Method | Caller | Purpose |
| --- | --- | --- |
| `lock_requirements(plan_id, policy_json)` | Owner | Register immutable policy. |
| `submit_evidence(plan_id, manifest_json)` | Owner | Commit one immutable package for the current attempt. |
| `attest_evidence(plan_id)` | Auditor | Attest to that package and policy. |
| `evaluate_readiness(plan_id)` | Owner | Run independent validator review and persist receipt. |
| `get_receipt(plan_id, attempt)` | Anyone | Read zero-based attempt receipt. |
| `get_plan(plan_id)` | Anyone | Read locked policy. |
| `get_package(plan_id, attempt)` | Anyone | Read committed manifest. |
| `get_status(plan_id)` | Anyone | Read attempt count, terminal state and event head. |
| `get_event(sequence)` | Anyone | Read globally indexed append-only event. |
| `get_config()` | Anyone | Read roles, version, event count and retry cap. |

All non-inconclusive assessments are terminal. An inconclusive result permits another freshly attested package, up to three committed assessment attempts. Network-level failed transactions do not consume an assessment attempt.

## Consensus design

`gl.vm.run_nondet_unsafe` invokes a leader assessment and a custom validator. Validators do their own web fetches, byte/hash/schema checks, semantic analysis, and arithmetic. They compare exact source bytes, complete calculated decisions and per-document semantic states, and validate leader quotations against independently fetched narrative/steps. Grounded quote selection and prose reasons may differ. Checking output format alone is insufficient for acceptance.

Storage writes occur after consensus in deterministic execution. The contract pins its GenVM SDK dependency; ABI generation and CI validate its ten public methods. Official references: [non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism), [networks](https://docs.genlayer.com/developers/networks).

## Boundaries

Auditor attestation is a wallet assertion, not cryptographic instrument provenance. Distinct wallets do not prove distinct people. Records, structured numbers and narratives can all be fabricated by colluding parties. The contract verifies consistency and readiness against supplied evidence as of a locked timestamp, not operational truth or future recoverability. Never upload guest information, credentials, private infrastructure details or unredacted recovery logs to the public evidence repository.

MIT licensed.
