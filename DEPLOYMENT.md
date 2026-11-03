# Deploy and reproduce

Tested: Python 3.12, `genlayer-py` 0.16.3, GenVM SDK v0.2.16. Install requirements and run the README checks first. Studionet is a hosted development environment, not mainnet; state and service availability can change.

## Own deployment

Create distinct owner and auditor wallets. Keep private keys outside the repository. Fund development accounts through the appropriate Studio faucet if needed. Copy `.env.example` to an ignored `.env` and set both private keys. Never reuse demo keys or real-funds wallets.

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/deploy.py --auditor 0xYOUR_AUDITOR_ADDRESS --env-file .env
```

The script checks chain 61999, deploys with `leader_only=False`, and exports public metadata and transaction evidence. It initially waits for ACCEPTED status; finalization must be checked separately. A timeout does not imply deployment failure: inspect its saved transaction hash before resubmitting. The active deployment's source hash must match the contract file, not documentation or tool changes.

For public deployments, reduce raw RPC exports to public proof fields before committing them: raw node configurations and signed transaction blobs are not required for review.

## Demo workflow

The supplied policy and four evidence files are entirely synthetic. The demo manifest pins real committed bytes in this repository. To change evidence, commit the evidence first, fetch that commit locally, generate a new manifest, then open a new plan.

```bash
python scripts/build_manifest.py 59a591374cf6afe5257db4438c57d887ec07004f
python scripts/demo.py --env-file .env --plan demo-ready-001
```

The demo loads the address from `deployments/studionet.json`, checks live chain and role configuration, then locks, submits, attests and evaluates using the corresponding wallets. Every write uses multi-validator execution. It records the transaction hash immediately, waits for FINALIZED, and exports public vote/execution summaries, the assessment receipt, the per-plan events and final status. Rerunning the same plan resumes saved transactions. Use a new plan ID for a new assessment. Only the matching deployment wallets can operate the existing demo contract.

The assessment can legitimately be INCONCLUSIVE or fail to reach consensus. Do not weaken semantic or quotation checks to obtain a preferred verdict.

## Current deployment

See `deployments/studionet.json` for RPC, chain, source hash, roles, address and transaction hash. The README links the public deployment explorer. The deployment proof is stored separately from application assessment receipts; successful deployment alone does not demonstrate a successful evidence review.
