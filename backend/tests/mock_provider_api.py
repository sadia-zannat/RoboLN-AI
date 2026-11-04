"""TEST ONLY: explicit HTTP provider fixture for browser/full-stack tests.

Never used by app.api or the normal launcher. Uses pinned httpx.MockTransport;
no external Meta request, credential, image analysis or physical observation.
"""
import json,os
import httpx,uvicorn
from app.api import app
from app import meta_ai

_real_client=httpx.Client
_calls=0

def fixture(request):
    global _calls
    _calls+=1
    if request.url.path.endswith('/models'):return httpx.Response(200,json={'data':[{'id':'muse-spark-1.3'}]})
    body=json.loads(request.content)
    text=json.dumps(body)
    if 'TRIGGER_TEST_RATE_LIMIT' in text:return httpx.Response(429,json={'error':'EXPLICIT TEST RATE LIMIT'})
    if 'Return ONLY a JSON object' in text:
        answer=json.dumps({'steps':[
            {'objective':'Identify the camera','instruction':'Read the unpowered camera label and record unknown ratings.','component_ids':['camera'],'checks':['Record the exact physical label'],'mistakes':['Guessing ratings from appearance'],'safety':'Keep all power disconnected.','evidence_required':True},
            {'objective':'Review the mounting location','instruction':'Compare the unpowered mount with the provisional reference and record the independent check.','component_ids':['camera'],'checks':['Support and clearance reviewed'],'mistakes':['Forcing a connector'],'safety':'Do not energize hardware.','evidence_required':True},
            {'objective':'Record remaining checks','instruction':'Save independent checks and unresolved issues before any commissioned hardware test.','component_ids':[],'checks':['Unresolved issues retained'],'mistakes':[],'safety':'No control executor is present.','evidence_required':True}]})
    else:
        answer='## Visible observations\nEXPLICIT TEST MOCK: synthetic image fixture received.\n\n## Recognized parts\nNo real hardware identification was performed.\n\n## Placement\nReview the saved reference independently.\n\n## Possible mistakes\nPhysical wiring cannot be judged by this software fixture.\n\n## Cannot verify\nContinuity, polarity, voltage, current limits, insulation or readiness.\n\n## Next check\nRead the real component label with power disconnected.\n\n## More evidence needed\nIndependent test notes.\n\n## Recommended next step\nRecord the independent check before user confirmation.'
    return httpx.Response(200,json={'id':f'EXPLICIT-TEST-MOCK-{_calls}','model':'muse-spark-1.3','choices':[{'message':{'content':answer},'finish_reason':'stop'}]})

meta_ai.httpx.Client=lambda **kwargs:_real_client(**kwargs,transport=httpx.MockTransport(fixture))
os.environ['MODEL_API_KEY']='EXPLICIT_TEST_ONLY_NOT_A_REAL_KEY'
if __name__=='__main__':
    print('TEST-ONLY Meta HTTP mock active; no external provider calls.',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=int(os.environ.get('ROBOLN_TEST_API_PORT','8000')))
