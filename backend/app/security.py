import hashlib, hmac, secrets, os
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import Cookie, Depends, Header, HTTPException, Request, Response
from argon2 import PasswordHasher, exceptions
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from .db import get_db
from .models import Session as LoginSession, User, now

hasher = PasswordHasher(time_cost=3, memory_cost=32768, parallelism=2)
SESSION_SECONDS = 8 * 60 * 60

def digest(raw: str) -> str: return hashlib.sha256(raw.encode()).hexdigest()

def password_hash(password: str) -> str: return hasher.hash(password)
def password_valid(saved: str, plain: str) -> bool:
    try: return hasher.verify(saved, plain)
    except (exceptions.VerifyMismatchError, exceptions.InvalidHashError, exceptions.VerificationError): return False

def issue(db: DBSession, response: Response, user: User):
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    session = LoginSession(user_id=user.id, token_hash=digest(token), csrf_hash=digest(csrf), expires_at=now()+timedelta(seconds=SESSION_SECONDS))
    db.add(session); db.commit()
    secure = os.getenv('ROBOLN_COOKIE_SECURE','false').lower() == 'true'
    response.set_cookie('roboln_session', token, httponly=True, secure=secure, samesite='lax', path='/', max_age=SESSION_SECONDS)
    response.set_cookie('roboln_csrf', csrf, httponly=False, secure=secure, samesite='lax', path='/', max_age=SESSION_SECONDS)

def clear(response: Response):
    response.delete_cookie('roboln_session', path='/'); response.delete_cookie('roboln_csrf', path='/')

def valid_session(token: str | None, db: DBSession):
    if not token: return None
    s=db.scalar(select(LoginSession).where(LoginSession.token_hash==digest(token), LoginSession.revoked==False))
    if not s or s.expires_at.replace(tzinfo=timezone.utc) <= now(): return None
    return s

def current_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    s=valid_session(request.cookies.get('roboln_session'), db)
    if not s: raise HTTPException(401, 'Sign in required')
    u=db.get(User,s.user_id)
    if not u: raise HTTPException(401, 'Session expired')
    return u

def csrf_guard(request: Request, db: DBSession = Depends(get_db)):
    origin=request.headers.get('origin')
    permitted=[x.strip().rstrip('/') for x in os.getenv('ROBOLN_ALLOWED_ORIGINS','http://127.0.0.1:3000,http://localhost:3000').split(',')]
    if origin and origin.rstrip('/') not in permitted: raise HTTPException(403,'Invalid request origin')
    s=valid_session(request.cookies.get('roboln_session'),db)
    csrf=request.headers.get('x-csrf-token','')
    if not s or not csrf or not hmac.compare_digest(s.csrf_hash, digest(csrf)) or not hmac.compare_digest(csrf, request.cookies.get('roboln_csrf','')):
        raise HTTPException(403,'CSRF verification failed')

def auth_origin(request: Request):
    origin=request.headers.get('origin')
    allowed=[x.strip().rstrip('/') for x in os.getenv('ROBOLN_ALLOWED_ORIGINS','http://127.0.0.1:3000,http://localhost:3000').split(',')]
    if origin and origin.rstrip('/') not in allowed: raise HTTPException(403, 'Invalid request origin')
