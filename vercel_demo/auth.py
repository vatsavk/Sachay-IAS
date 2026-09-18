"""SANCHAY Authentication Module"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.environ.get('JWT_SECRET', 'sanchay-dev-secret-CHANGE-IN-PROD')
ALGORITHM  = "HS256"
EXPIRE_MIN = int(os.environ.get('JWT_EXPIRE_MINUTES', 480))  # 8 hours

FIRM_WIDE_ROLES = {'principal_consultant', 'compliance_officer'}
WRITE_ROLES     = {'advisor', 'principal_consultant'}

# 'admin' is an accepted alias for 'principal_consultant'
ROLE_ALIASES = {'admin': 'principal_consultant'}

def normalize_role(role: str) -> str:
    """Map legacy/alias role names to the canonical role."""
    return ROLE_ALIASES.get(role, role)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: Optional[str]) -> bool:
    if not h or not h.startswith('$'):
        return False
    try:
        return pwd_context.verify(p, h)
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def has_firm_wide_access(role: str) -> bool:
    return role in FIRM_WIDE_ROLES

def can_write(role: str) -> bool:
    return role in WRITE_ROLES
