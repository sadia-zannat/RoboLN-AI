"""Meta Model API wire contract verified against official dev.meta.ai docs 2026-10-30.
No local response generator, credential guessing, tool execution or provider fallback.
"""
import os, time
import httpx
from fastapi import HTTPException

BASE_URL='https://api.meta.ai/v1'

def configuration():
    model=os.getenv('ROBOLN_META_MODEL','muse-spark-1.3')
    configured=bool(os.getenv('MODEL_API_KEY','').strip())
    return {'provider':'META_MODEL_API','model':model,'status':'CONFIGURED_UNVERIFIED' if configured else 'NOT_CONFIGURED',
        'text_supported':True,'image_supported':model in ('muse-spark-1.3','muse-spark-1.2','muse-spark-1.1'),
        'external_inference_verified':False,'endpoint':BASE_URL,'message':'Configuration is not proof of a successful inference.'}

def provider_request(path, payload=None):
    key=os.getenv('MODEL_API_KEY','').strip()
    if not key: raise HTTPException(503,'NOT_CONFIGURED: set MODEL_API_KEY on the backend')
    for attempt in range(2):
        try:
            with httpx.Client(timeout=httpx.Timeout(35,connect=8),follow_redirects=False) as client:
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
                r=client.get(BASE_URL+path,headers=headers) if payload is None else client.post(BASE_URL+path,headers=headers,json=payload)
            if r.status_code in (429,502,503,504) and attempt==0:
                time.sleep(0.5);continue
            if r.status_code==429: raise HTTPException(429,'Meta rate limit reached. Try again later.',headers={'Retry-After':'30'})
            if r.status_code in (401,403): raise HTTPException(502,'Meta rejected credentials or model access. Check your provider account.')
            if r.status_code>=400: raise HTTPException(502,f'Meta request failed (HTTP {r.status_code}); provider content is withheld to protect secrets.')
            if len(r.content)>2_000_000: raise HTTPException(502,'Meta response exceeded the configured limit')
            data=r.json()
            if not isinstance(data,dict): raise HTTPException(502,'Meta returned an invalid response object. No successful answer was recorded.')
            return data
        except httpx.TimeoutException: raise HTTPException(504,'Meta request timed out. No response was recorded.')
        except (httpx.HTTPError,ValueError): raise HTTPException(502,'Meta network or response-format error. No response was recorded.')

def infer(messages):
    c=configuration()
    data=provider_request('/chat/completions',{'model':c['model'],'messages':messages,'max_completion_tokens':4000,'stream':False})
    try:
        answer=data['choices'][0]['message']['content']
        if not isinstance(answer,str) or not answer.strip(): raise ValueError()
        return {'answer':answer[:50_000],'model':str(data.get('model',c['model']))[:100],
            'provider_id':str(data.get('id',''))[:200],'finish_reason':data['choices'][0].get('finish_reason')}
    except (KeyError,IndexError,TypeError,ValueError): raise HTTPException(502,'Meta returned no usable text. No successful answer was recorded.')
