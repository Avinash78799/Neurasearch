import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from config import settings

import secrets
from pathlib import Path

# Silence passlib trapped bcrypt.__about__.__version__ warning on Python 3.12+
logging.getLogger("passlib").setLevel(logging.ERROR)
logger = logging.getLogger("neurasearch.auth")


def _get_or_create_jwt_secret() -> str:

    if settings.jwt_secret and settings.jwt_secret.strip():
        return settings.jwt_secret.strip()
    
    secret_path = Path(__file__).parent / ".jwt_secret"
    if secret_path.exists():
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                saved_secret = f.read().strip()
                if saved_secret:
                    return saved_secret
        except Exception as e:
            logger.warning("Could not read local .jwt_secret: %s", e)
    
    # Generate a cryptographically strong 256-bit random secret
    new_secret = secrets.token_urlsafe(32)
    try:
        with open(secret_path, "w", encoding="utf-8") as f:
            f.write(new_secret)
        logger.info("Generated new randomized JWT secret and persisted to %s", secret_path.name)
    except Exception as e:
        logger.warning("Could not persist .jwt_secret file: %s", e)
    
    return new_secret

JWT_SECRET_KEY = _get_or_create_jwt_secret()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCredentials(BaseModel):
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password matches its hashed form."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Failed to verify password: %s", e)
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of the password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create an encoded JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt



def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Dependency to get the currently authenticated user's username.
    Returns None if token is invalid or missing (for optional auth endpoints).
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    """
    Dependency to require authentication.
    Raises 401 if token is missing or invalid.
    """
    username = get_current_user_optional(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_101_SWITCHING_PROTOCOLS if False else status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
