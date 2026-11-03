# Evidence and verdict rules

All JSON submitted to the contract and all evidence documents must use the exact canonical representation:

```python
json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
```

No trailing newline is permitted in canonical evidence. Duplicate JSON keys, alternate whitespace, floats in integer fields, and booleans used as integers are rejected.

## Locked policy

`fixtures/policy.json` is a complete example. Exact fields: `organization`, `as_of` (Unix seconds), `max_age_seconds`, `publisher` (`owner/repository`), and `requirements`. Each requirement has exactly `id`, `system`, `scenario`, `rto_seconds`, `rpo_seconds`. The fixed `as_of` is chosen by the owner; there is no wall-clock freshness guarantee. RTO is at least one second; RPO can be zero. Requirements must have unique IDs and unique system/scenario pairs.

## Manifest

Exact top-level field: `documents`. Each entry has `url`, `sha256` (lowercase hex), `bytes`, `kind`, `test_id`, `requirement_id`. Only HTTPS `raw.githubusercontent.com` URLs beneath the locked publisher, with full 40-character lowercase Git commit SHAs and restricted `.json` paths, are accepted. Branches, query strings, encoded paths, traversal and duplicate URLs are rejected.

There are 1–8 requirements, 1–16 documents, at most 12,000 committed bytes per document and 48,000 committed bytes per package. Each requirement/test/kind tuple is unique. These are application validation bounds; the underlying HTTP runtime controls transport buffering, redirects and timeouts. The contract does not promise pre-download streaming limits.

Generate the demo manifest from bytes in an existing local Git commit:

```bash
python scripts/build_manifest.py FULL_40_CHARACTER_COMMIT_SHA
```

`fixtures/mock_manifest.json` uses placeholder commit URLs exclusively for mocked tests. Use `fixtures/live_manifest.json` for the live synthetic demonstration.

## Documents

All documents have exactly `organization`, `test_id`, `system`, `scenario`, `kind`, `observed_at`, `narrative`, plus the kind-specific fields below. Identity must match the manifest and policy.

| Kind | Additional fields | Mandatory interpretation |
| --- | --- | --- |
| `restore` | `started_at`, `service_restored_at`, `data_checkpoint_at`, `result` (`SUCCESS`/`FAILURE`) | Completed usable service/data recovery, not a successful backup alone. |
| `integrity` | `checksum_verified`, `application_checks_passed` (booleans) | Backup checksum and recovered application/data verification. |
| `exercise` | `production_like` (boolean), `result` (`PASS`/`FAIL`) | Completed representative scenario exercise, not a tabletop or future plan. |
| `runbook` | `steps` | Executable ordered steps, operator, dependencies, validation and rollback/escalation. |

RTO = service restoration minus test start. RPO = test start minus last recovered checkpoint. Chronology requires checkpoint ≤ start ≤ restoration ≤ observation ≤ policy as-of. All records must be fresh, including restore start; integrity/exercise observations must not precede restoration.

Each model check contains exact fields `document`, `state`, `quote`, `reason`. States: `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `UNKNOWN`. Non-unknown states require at least 12 characters quoted exactly from narrative or steps. Metadata-only quotes cannot establish support under the semantic task. Independent validators compare semantic states and calculated decisions; evidence quotation grounding alone does not prove the model interpretation correct.

## Tamper evidence

A receipt binds policy hash, manifest hash, as-of, auditor, previous event hash and result. `decision_hash` is SHA-256 of the canonical receipt with that field removed. Each event hashes its full canonical content excluding `event_hash`, including previous per-plan event hash, global sequence, actor and action.

```bash
python scripts/verify_receipt.py deployments/demo-ready-001/assessment.json \
  --events deployments/demo-ready-001/events.json
```

Offline hash verification proves internal consistency. Compare the exported chain's last hash to a fresh `get_status(plan_id)` read to anchor it to contract state; an attacker can fabricate an internally consistent unanchored export.
