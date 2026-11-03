"""Deploy to hosted Studionet with an operator-owned key. No keys enter output files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import CalldataAddress, TransactionStatus

ROOT=Path(__file__).resolve().parents[1]

def save(path,data):
    Path(path).write_text(json.dumps(data,indent=2,default=str)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--auditor',required=True)
    p.add_argument('--env-file',default='.env')
    p.add_argument('--out',default='deployments/studionet.json')
    a=p.parse_args()
    load_dotenv(a.env_file)
    key=os.environ.get('RESTOREPROOF_OWNER_KEY')
    if not key: raise SystemExit('Set RESTOREPROOF_OWNER_KEY in your private environment')
    owner=create_account(key)
    if owner.address.lower()==a.auditor.lower(): raise SystemExit('Auditor must be a distinct wallet')
    client=create_client(chain=studionet,account=owner)
    if client.w3.eth.chain_id!=61999: raise SystemExit('Unexpected Studionet chain ID')
    code=(ROOT/'contracts/restore_proof.py').read_bytes()
    tx=client.deploy_contract(code=code,args=[CalldataAddress(a.auditor)],leader_only=False)
    deployment={'network':'studionet','chain_id':61999,'rpc':'https://studio.genlayer.com/api',
                'source_sha256':hashlib.sha256(code).hexdigest(),'owner':owner.address,'auditor':a.auditor,
                'deploy_transaction':tx,'status':'PENDING','contract_address':None}
    save(a.out,deployment)
    print('Submitted:',tx,flush=True)
    receipt=client.wait_for_transaction_receipt(tx,status=TransactionStatus.ACCEPTED,interval=2000,retries=25)
    save(Path(a.out).with_suffix('.receipt.json'), {**{k: receipt.get(k) for k in ['hash','status_name','status','result_name','from_address','to_address']}, 'votes': (receipt.get('consensus_data') or {}).get('votes')})
    deployment['status']=str(receipt.get('status_name') or receipt.get('status'))
    deployment['contract_address']=receipt.get('contract_address') or (receipt.get('data') or {}).get('contract_address') or receipt.get('to_address')
    save(a.out,deployment)
    leaders = (receipt.get('consensus_data') or {}).get('leader_receipt') or []
    if not leaders or leaders[0].get('execution_result') != 'SUCCESS':
        raise SystemExit('Deployment execution failed; inspect transaction before retrying')
    print(json.dumps(deployment,indent=2))
