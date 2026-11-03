"""Run/resume a synthetic two-wallet Studionet assessment, exporting public proof only."""
import argparse
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ROOT = Path(__file__).resolve().parents[1]

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + '\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--env-file', default='.env')
    p.add_argument('--plan', default='demo-ready-001')
    a = p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", a.plan):
        raise SystemExit("Invalid plan ID")
    load_dotenv(a.env_file)
    owner = create_account(os.environ['RESTOREPROOF_OWNER_KEY'])
    auditor = create_account(os.environ['RESTOREPROOF_AUDITOR_KEY'])
    c = create_client(chain=studionet, account=owner)
    deployment = json.loads((ROOT / 'deployments/studionet.json').read_text())
    address = deployment['contract_address']
    if c.w3.eth.chain_id != 61999:
        raise SystemExit('Unexpected chain')
    config = json.loads(c.read_contract(address=address, function_name='get_config'))
    if config['owner'].lower() != owner.address.lower() or config['auditor'].lower() != auditor.address.lower():
        raise SystemExit('Wallets do not match contract roles')
    out = ROOT / 'deployments' / a.plan
    out.mkdir(parents=True, exist_ok=True)

    def send(method, args, account):
        txfile = out / (method + '.json')
        if txfile.exists():
            tx = json.loads(txfile.read_text())['transaction']
        else:
            tx = c.write_contract(address=address, function_name=method, args=args, account=account, leader_only=False)
            save(txfile, {'transaction': tx, 'method': method})
        print(method, tx, flush=True)
        receipt = c.wait_for_transaction_receipt(tx, status=TransactionStatus.FINALIZED, interval=3000, retries=100)
        # Preserve public consensus evidence, excluding bulky calldata and node configuration.
        consensus = receipt.get('consensus_data') or {}
        summary = {k: receipt.get(k) for k in ['hash','status_name','status','result_name','from_address','to_address']}
        summary['votes'] = consensus.get('votes')
        summary['executions'] = [
            {'mode': x.get('mode'), 'vote': x.get('vote'), 'execution_result': x.get('execution_result'),
             'genvm_result': x.get('genvm_result'), 'result': x.get('result')}
            for x in (consensus.get('leader_receipt') or []) + (consensus.get('validators') or [])
        ]
        save(txfile, {'transaction': tx, 'method': method, 'receipt': summary})
        if not summary['executions'] or summary['executions'][0]['execution_result'] != 'SUCCESS':
            raise RuntimeError('Execution failed; inspect ' + str(txfile))
        print('FINALIZED', flush=True)

    policy = (ROOT / 'fixtures/policy.json').read_text()
    manifest = (ROOT / 'fixtures/live_manifest.json').read_text()
    send('lock_requirements', [a.plan, policy], owner)
    send('submit_evidence', [a.plan, manifest], owner)
    send('attest_evidence', [a.plan], auditor)
    send('evaluate_readiness', [a.plan], owner)
    receipt = json.loads(c.read_contract(address=address, function_name='get_receipt', args=[a.plan, 0]))
    save(out / 'assessment.json', receipt)
    events = []
    config = json.loads(c.read_contract(address=address, function_name='get_config'))
    for i in range(config['events']):
        event = json.loads(c.read_contract(address=address, function_name='get_event', args=[i]))
        if event['plan_id'] == a.plan:
            events.append(event)
    save(out / 'events.json', events)
    save(out / 'status.json', json.loads(c.read_contract(address=address, function_name='get_status', args=[a.plan])))
    from verify_receipt import verify
    print(receipt['outcome'], verify(receipt, events), flush=True)

if __name__ == '__main__':
    main()
