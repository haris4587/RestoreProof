import copy
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

def load(name):
    return json.loads((ROOT / 'fixtures' / name).read_text())

@pytest.fixture
def ctx(direct_vm, direct_deploy, direct_bob):
    import sys
    from gltest.direct import wasi_mock
    from gltest.direct.sdk_loader import setup_sdk_paths
    from gltest.direct.loader import _inject_message_to_fd0
    sys.modules['_genlayer_wasi'] = wasi_mock
    setup_sdk_paths(ROOT / 'contracts/restore_proof.py', 'v0.2.16')
    _inject_message_to_fd0(direct_vm)
    from genlayer import Address
    direct_bob = Address(direct_bob) if isinstance(direct_bob, bytes) else direct_bob
    contract = direct_deploy('contracts/restore_proof.py', direct_bob, sdk_version='v0.2.16')
    return contract, direct_vm, direct_vm.sender, direct_bob

def prepare(ctx, *, policy=None, docs=None, semantics=None, manifest=None, plan='audit-001', attest=True):
    c, vm, owner, auditor = ctx
    p = policy or load('policy.json')
    m = manifest or load('mock_manifest.json')
    ds = docs or [load(f'{k}.json') for k in ['restore', 'integrity', 'exercise', 'runbook']]
    sem = semantics or load('mock_semantics.json')
    for i, meta in enumerate(m['documents']):
        body = canon(ds[i]).encode()
        meta['bytes'] = len(body)
        meta['sha256'] = hashlib.sha256(body).hexdigest()
        vm.mock_web(meta['url'], {'status': 200, 'body': body})
    vm.mock_llm('RestoreProof semantic', canon(sem))
    c.lock_requirements(plan, canon(p))
    c.submit_evidence(plan, canon(m))
    if attest:
        with vm.prank(auditor):
            c.attest_evidence(plan)
    return p, m, ds, sem

def receipt(c, plan='audit-001', attempt=0):
    return json.loads(c.get_receipt(plan, attempt))

def test_ready_and_independent_validator(ctx):
    c, vm, _, _ = ctx
    prepare(ctx)
    c.evaluate_readiness('audit-001')
    r = receipt(c)
    assert r['outcome'] == 'RECOVERY_READY'
    assert r['result']['decision']['requirements'][0]['tests'][0]['rto_seconds'] == 1200
    assert r['result']['decision']['requirements'][0]['tests'][0]['rpo_seconds'] == 120
    assert vm.run_validator() is True
    original_hash = r.pop('decision_hash')
    assert hashlib.sha256(canon(r).encode()).hexdigest() == original_hash

@pytest.mark.parametrize('change', ['rto', 'rpo', 'checksum', 'application', 'restore-failed', 'exercise-failed', 'contradiction'])
def test_failures(ctx, change):
    c, vm, _, _ = ctx
    ds = [load(f'{k}.json') for k in ['restore', 'integrity', 'exercise', 'runbook']]
    sem = load('mock_semantics.json')
    if change == 'rto': ds[0]['started_at'] -= 1000
    if change == 'rto': ds[0]['data_checkpoint_at'] -= 1000
    if change == 'rpo': ds[0]['data_checkpoint_at'] -= 500
    if change == 'checksum': ds[1]['checksum_verified'] = False
    if change == 'application': ds[1]['application_checks_passed'] = False
    if change == 'restore-failed': ds[0]['result'] = 'FAILURE'
    if change == 'exercise-failed': ds[2]['result'] = 'FAIL'
    if change == 'contradiction': sem['checks'][0]['state'] = 'CONTRADICTED'
    prepare(ctx, docs=ds, semantics=sem)
    c.evaluate_readiness('audit-001')
    assert receipt(c)['outcome'] == 'FAILED'
    assert vm.run_validator() is True

@pytest.mark.parametrize('state', ['UNSUPPORTED', 'UNKNOWN'])
def test_backup_only_or_ambiguous_never_ready(ctx, state):
    c, vm, _, _ = ctx
    sem = load('mock_semantics.json'); sem['checks'][0]['state'] = state
    prepare(ctx, semantics=sem)
    c.evaluate_readiness('audit-001')
    assert receipt(c)['outcome'] == 'INCONCLUSIVE'
    assert vm.run_validator()

def test_partial_coverage(ctx):
    c, _, _, _ = ctx
    p = load('policy.json')
    p['requirements'].append({'id':'billing', 'system':'billing', 'scenario':'region-loss', 'rto_seconds':1800, 'rpo_seconds':300})
    prepare(ctx, policy=p)
    c.evaluate_readiness('audit-001')
    assert receipt(c)['outcome'] == 'PARTIAL'

@pytest.mark.parametrize('change', ['stale','tabletop','missing'])
def test_incomplete(ctx, change):
    c, _, _, _ = ctx
    ds = [load(f'{k}.json') for k in ['restore', 'integrity', 'exercise', 'runbook']]
    m = load('mock_manifest.json'); sem = load('mock_semantics.json')
    if change == 'stale':
        p = load('policy.json'); p['as_of'] += 604801
    else: p = None
    if change == 'tabletop': ds[2]['production_like'] = False
    if change == 'missing':
        ds.pop(); m['documents'].pop(); sem['checks'].pop()
    prepare(ctx, policy=p, docs=ds, manifest=m, semantics=sem)
    c.evaluate_readiness('audit-001')
    assert receipt(c)['outcome'] == 'INCONCLUSIVE'

def test_permission_and_two_person_attestation(ctx):
    c, vm, owner, auditor = ctx
    prepare(ctx, attest=False)
    with pytest.raises(Exception, match='Auditor attestation required'): c.evaluate_readiness('audit-001')
    with pytest.raises(Exception, match='Auditor only'): c.attest_evidence('audit-001')
    with vm.prank(auditor):
        with pytest.raises(Exception, match='Owner only'): c.submit_evidence('audit-001', canon(load('mock_manifest.json')))
        c.attest_evidence('audit-001')
        with pytest.raises(Exception, match='Owner only'): c.evaluate_readiness('audit-001')
    c.evaluate_readiness('audit-001')
    with pytest.raises(Exception, match='terminal'): c.evaluate_readiness('audit-001')
    with pytest.raises(Exception, match='terminal'): c.submit_evidence('audit-001', canon(load('mock_manifest.json')))

def test_immutable_policy_and_package(ctx):
    c, _, _, _ = ctx
    prepare(ctx)
    with pytest.raises(Exception, match='already locked'): c.lock_requirements('audit-001', canon(load('policy.json')))
    with pytest.raises(Exception, match='already committed'): c.submit_evidence('audit-001', canon(load('mock_manifest.json')))

def test_hash_mismatch_never_ready(ctx):
    c, vm, _, _ = ctx
    _,m,_,_ = prepare(ctx)
    vm.clear_mocks()
    vm.mock_web(m['documents'][0]['url'], {'status':200, 'body':b'forged'})
    c.evaluate_readiness('audit-001')
    assert receipt(c)['outcome'] == 'INCONCLUSIVE'
    assert receipt(c)['result']['error'] == 'EVIDENCE_UNAVAILABLE_OR_INVALID'
    assert vm.run_validator()

@pytest.mark.parametrize('field,value', [('quote','fabricated supporting quote'), ('document',True), ('state','READY')])
def test_malformed_model_response(ctx, field, value):
    c, _, _, _ = ctx
    sem = load('mock_semantics.json'); sem['checks'][0][field] = value
    prepare(ctx, semantics=sem)
    c.evaluate_readiness('audit-001')
    assert receipt(c)['result']['error'] == 'SEMANTIC_RESPONSE_INVALID'

@pytest.mark.parametrize('url', [
    'http://127.0.0.1/a.json',
    'https://raw.githubusercontent.com.evil.test/haris4587/RestoreProof/'+'0'*40+'/a.json',
    'https://raw.githubusercontent.com/haris4587/RestoreProof/main/a.json',
    'https://raw.githubusercontent.com/haris4587/RestoreProof/'+'0'*40+'/../a.json',
    'https://raw.githubusercontent.com/haris4587/RestoreProof/'+'0'*40+'/a.json?token=secret',
    'https://raw.githubusercontent.com/evil/publisher/'+'0'*40+'/a.json',
])
def test_retrieval_allowlist(ctx, url):
    c, _, _, _ = ctx
    c.lock_requirements('a', canon(load('policy.json')))
    m = load('mock_manifest.json'); m['documents'][0]['url'] = url
    with pytest.raises(Exception): c.submit_evidence('a', canon(m))

def test_independent_validator_rejects_forged_leader(ctx):
    c, vm, _, _ = ctx
    prepare(ctx); c.evaluate_readiness('audit-001')
    proposed = copy.deepcopy(receipt(c)['result'])
    proposed['decision']['outcome'] = 'FAILED'
    assert vm.run_validator(leader_result=(proposed, [canon(load(f'{k}.json')) for k in ['restore', 'integrity', 'exercise', 'runbook']])) is False
    proposed = copy.deepcopy(receipt(c)['result'])
    proposed['checks'][0]['quote'] = 'Invented quote not in authenticated bytes'
    assert vm.run_validator(leader_result=(proposed, [canon(load(f'{k}.json')) for k in ['restore', 'integrity', 'exercise', 'runbook']])) is False
    assert vm.run_validator(leader_error=Exception('boom')) is False

def test_independent_semantic_disagreement(ctx):
    c, vm, _, _ = ctx
    _,m,ds,sem = prepare(ctx); c.evaluate_readiness('audit-001')
    vm.clear_mocks()
    for meta,d in zip(m['documents'],ds): vm.mock_web(meta['url'], {'status':200, 'body':canon(d).encode()})
    sem['checks'][0]['state']='UNSUPPORTED'
    vm.mock_llm('RestoreProof semantic', canon(sem))
    assert vm.run_validator() is False

def test_history_chain_and_retry_cap(ctx):
    c, vm, _, auditor = ctx
    sem = load('mock_semantics.json'); sem['checks'][0]['state']='UNKNOWN'
    prepare(ctx, semantics=sem)
    for n in range(3):
        if n:
            c.submit_evidence('audit-001', canon(load('mock_manifest.json')))
            with vm.prank(auditor): c.attest_evidence('audit-001')
        c.evaluate_readiness('audit-001')
        assert receipt(c,attempt=n)['outcome']=='INCONCLUSIVE'
    assert json.loads(c.get_status('audit-001'))['terminal']
    previous='0'*64
    for i in range(10):
        event=json.loads(c.get_event(i)); h=event.pop('event_hash')
        assert event['previous_hash']==previous
        assert hashlib.sha256(canon(event).encode()).hexdigest()==h
        previous=h
    assert json.loads(c.get_status('audit-001'))['head']==previous
    assert receipt(c,attempt=0)['attempt']==0
    with pytest.raises(Exception,match='terminal'): c.submit_evidence('audit-001',canon(load('mock_manifest.json')))

def test_canonical_and_duplicate_policy_keys(ctx):
    c, _, _, _ = ctx
    with pytest.raises(Exception,match='Canonical'): c.lock_requirements('a',json.dumps(load('policy.json')))
    raw=canon(load('policy.json')).replace('"as_of":1793700000','"as_of":1,"as_of":1793700000')
    with pytest.raises(Exception,match='Canonical'): c.lock_requirements('a',raw)

def test_plan_isolation(ctx):
    c, _, _, _ = ctx
    prepare(ctx); c.lock_requirements('other',canon(load('policy.json')))
    with pytest.raises(Exception,match='attestation'): c.evaluate_readiness('other')
    assert c.get_receipt('other',0)==''
    c.evaluate_readiness('audit-001')
    assert json.loads(c.get_status('other'))['attempts']==0
