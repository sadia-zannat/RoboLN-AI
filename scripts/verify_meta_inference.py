"""Operator-invoked real provider smoke test. Never run in automatic release tests.
The only outgoing content is the explicit readiness question below. No project data.
"""
import argparse,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.meta_ai import configuration,provider_request,infer

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--consent-send',action='store_true');args=parser.parse_args()
    if not args.consent_send:raise SystemExit('Re-run with --consent-send only when you approve sending the readiness question to Meta.')
    if configuration()['status']=='NOT_CONFIGURED':raise SystemExit('NOT_CONFIGURED: set MODEL_API_KEY in the environment')
    models=provider_request('/models');ids=[x['id'] for x in models.get('data',[]) if 'id' in x]
    if configuration()['model'] not in ids:raise SystemExit('Configured model is not in the provider model catalog for this account')
    result=infer([{'role':'user','content':'Reply with a short readiness acknowledgement. This is an operator-approved API integration test.'}])
    print('REAL_PROVIDER_RESPONSE',result['model'],result['provider_id']);print(result['answer'])
if __name__=='__main__':main()
