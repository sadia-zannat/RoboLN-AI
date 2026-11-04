"""Bound request memory and redact validation inputs (passwords, media, tokens)."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def validation_errors(request:Request,exc:RequestValidationError):
    return JSONResponse(status_code=422,content={'detail':[{'loc':list(e['loc']),'msg':e['msg']} for e in exc.errors()]})

class RequestSizeLimit:
    def __init__(self,app,max_bytes=6_000_000):self.app,self.max_bytes=app,max_bytes
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            body.extend(message.get('body',b''))
            if len(body)>self.max_bytes:return await JSONResponse({'detail':'Request body exceeds 6 MB'},status_code=413)(scope,receive,send)
            if not message.get('more_body'):break
        delivered=False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered=True;return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,bounded_receive,send)
