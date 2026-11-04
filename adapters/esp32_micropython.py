"""MicroPython HTTP packet adapter. Your reviewed sensor firmware calls publish().
Requires a MicroPython build with TLS certificate verification and requests support.
No GPIO assignments, synthetic readings or physical control functions are included.
Never disable TLS verification to make a connection work.
"""
import json

def publish(api_url,token,packet,tls_context):
    # Use a firmware-specific verified transport. urequests variants often disable
    # certificate checks; require an explicit verified TLS context from the caller.
    import socket,ssl
    if not api_url.startswith('https://'):raise ValueError('ESP32 adapter requires HTTPS')
    if tls_context.verify_mode!=ssl.CERT_REQUIRED:raise ValueError('TLS certificate validation is required')
    address=api_url[8:].rstrip('/')
    if '/' in address or ':' in address:raise ValueError('Use an HTTPS hostname without a path or custom port')
    body=json.dumps(packet).encode()
    raw=socket.socket();raw.settimeout(15)
    try:
        raw.connect(socket.getaddrinfo(address,443)[0][-1])
        secure=tls_context.wrap_socket(raw,server_hostname=address)
        try:
            headers=('POST /api/device/telemetry HTTP/1.1\r\nHost: '+address+'\r\nAuthorization: Bearer '+token+'\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\n\r\n').encode()
            secure.write(headers+body)
            first=secure.readline()
            if b' 201 ' not in first:raise OSError('Telemetry upload rejected; inspect status locally')
            return True
        finally:secure.close()
    finally:raw.close()
