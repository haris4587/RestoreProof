"""Reproducible synthetic fixtures. Never represent these as organization audit evidence."""
import hashlib
import json
from pathlib import Path

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

def generate():
    root = Path(__file__).resolve().parents[1] / 'fixtures'
    root.mkdir(exist_ok=True)
    policy = {'organization': 'demo-hotel', 'as_of': 1793700000, 'max_age_seconds': 604800,
              'publisher': 'haris4587/RestoreProof', 'requirements': [
                  {'id': 'booking-db', 'system': 'booking', 'scenario': 'region-loss', 'rto_seconds': 1800, 'rpo_seconds': 300}]}
    (root / 'policy.json').write_text(canonical(policy))
    narratives = {
        'restore': 'The booking service was restored in the isolated recovery region. Operators verified usable recovered guest reservations through application queries. Start and service restoration timestamps are from the recovery harness; checkpoint time is the last durable transaction recovered.',
        'integrity': 'Backup object checksum matched its committed checksum. Recovered reservation row counts, foreign keys and application booking queries passed validation after restoration.',
        'exercise': 'Operators completed the region-loss recovery exercise in a production-like isolated environment with representative booking volume and dependency failover; the service passed the end-to-end recovery test.',
        'runbook': 'Operators followed the booking region-loss runbook, including dependency startup, restoration, service validation and rollback escalation.'}
    docs = []
    for kind in ['restore', 'integrity', 'exercise', 'runbook']:
        d = {'organization': 'demo-hotel', 'test_id': 'dr-001', 'system': 'booking', 'scenario': 'region-loss', 'kind': kind,
             'observed_at': 1793699000, 'narrative': narratives[kind]}
        if kind == 'restore':
            d.update(started_at=1793697000, service_restored_at=1793698200, data_checkpoint_at=1793696880, result='SUCCESS')
        elif kind == 'integrity':
            d.update(checksum_verified=True, application_checks_passed=True)
        elif kind == 'exercise':
            d.update(production_like=True, result='PASS')
        else:
            d['steps'] = 'Responsible operator: DR on-call. 1. Declare region loss and isolate old writers. 2. Start network and identity dependencies in recovery region. 3. Verify backup checksum, restore database, replay durable logs. 4. Start booking service; validate guest reservation queries and sample writes. 5. If validation fails, isolate recovery service, roll back routing and escalate to incident commander.'
        docs.append(d)
        (root / f'{kind}.json').write_text(canonical(d))
    checks = {'checks': [{'document': i, 'state': 'SUPPORTED', 'quote': d['narrative'], 'reason': f'Synthetic mocked response supports {d["kind"]}; no live model was invoked.'} for i,d in enumerate(docs)]}
    (root / 'mock_semantics.json').write_text(canonical(checks))
    # Placeholder commit is ONLY used with mocked web requests; real manifest is built after publication.
    documents = []
    for d in docs:
        body = canonical(d).encode()
        documents.append({'url': f'https://raw.githubusercontent.com/haris4587/RestoreProof/{"0"*40}/fixtures/{d["kind"]}.json',
                          'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body), 'kind': d['kind'], 'test_id': d['test_id'], 'requirement_id': 'booking-db'})
    (root / 'mock_manifest.json').write_text(canonical({'documents': documents}))

if __name__ == '__main__':
    generate()
