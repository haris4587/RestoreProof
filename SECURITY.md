# Security model

Owner and auditor are distinct nonzero wallets fixed at construction. The owner alone locks requirements, commits evidence and triggers assessment. Only the auditor attests to the current immutable package. All views are public. There are no fund transfers, administrative outcome overrides, role replacements or upgrade mechanism.

Policy and package state are immutable. A committed package cannot be replaced before assessment, including when the auditor refuses attestation. Start a new plan if necessary. Every non-inconclusive result closes its plan; inconclusive results allow at most three attempts with separate attestations. This bounds contract-level retries but does not prevent an owner deploying another contract or opening another plan. Reporting should include the full history rather than cherry-picked successful plans.

Evidence is publisher-allowlisted, Git-commit-pinned, byte-count-bound, SHA-256-bound, schema-checked and identity-checked. GitHub hosting, availability and the GenVM HTTP runtime are external dependencies. HTTPS and a publisher's repository do not prove source-instrument authenticity. The application does not validate signed log producers, PKI chains or auditor professional qualifications.

AI sees evidence explicitly as untrusted data and is instructed to ignore embedded instructions. Exact schemas, quotation grounding, independently rerun validator reasoning and deterministic calculations constrain its influence. Models may still make shared mistakes or agree on misleading evidence. Format checks and quoted text are not proof of truth. Failure to obtain valid evidence or valid model output produces an inconclusive assessment when validators agree on that failure; validator disagreement may instead leave the transaction unsuccessful.

`as_of` is caller-supplied and immutable. Assessments cover that reference instant and submitted tests only. They are not continuously refreshed, a certification, or a guarantee of actual disaster recovery. Incomplete or stale tests conservatively block readiness; a recent demonstrated failure takes precedence over a different passing test.

Demo wallets are disposable development wallets operated for a synthetic demonstration. Distinct keys demonstrate role enforcement, not independent real-world auditors. No secrets are included in public exports. Production operators should use independently controlled wallets and their own reviewed deployment, private evidence transformation/redaction process, and trustworthy signed source records outside this v1 scope.

Report a suspected vulnerability privately to the repository owner through their GitHub profile before publishing sensitive exploit details. Do not include private keys or confidential operational evidence in issues.
