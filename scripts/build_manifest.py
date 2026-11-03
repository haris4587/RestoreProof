"""Build a byte-bound manifest from files at an existing Git commit, not the worktree."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build(commit, publisher='haris4587/RestoreProof'):
    if not re.fullmatch('[0-9a-f]{40}',commit): raise ValueError('Use a full 40-character commit SHA')
    docs=[]
    for kind in ['restore','integrity','exercise','runbook']:
        path=f'fixtures/{kind}.json'
        body=subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
        record=json.loads(body)
        docs.append({'url':f'https://raw.githubusercontent.com/{publisher}/{commit}/{path}',
                     'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'kind':kind,
                     'test_id':record['test_id'],'requirement_id':'booking-db'})
    return {'documents':docs}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit');parser.add_argument('--out',default='fixtures/live_manifest.json')
    args=parser.parse_args()
    Path(args.out).write_text(json.dumps(build(args.commit),sort_keys=True,separators=(',',':')))
    print(args.out)
