"""Security utilities and middleware."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# API Key settings
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = {API_KEY_NAME: "api-key"}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list = []

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: list = []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        if username is None:
            return None
        return TokenData(username=username, scopes=scopes)
    except JWTError:
        return None

# API Key Authentication
api_keys_db = {
    "test-key-123": {
        "key": "test-key-123",
        "username": "test-user",
        "scopes": ["read", "write"],
        "created_at": datetime.utcnow(),
        "last_used": None,
        "rate_limit": 100,  # requests per hour
    }
}

def verify_api_key(api_key: str) -> Optional[dict]:
    """Verify API key and return user info."""
    if api_key in api_keys_db:
        user_info = api_keys_db[api_key].copy()
        user_info["last_used"] = datetime.utcnow()
        return user_info
    return None

def generate_api_key(username: str, scopes: list = None) -> str:
    """Generate a new API key."""
    if scopes is None:
        scopes = ["read"]

    # Generate secure random key
    key = secrets.token_urlsafe(32)

    api_keys_db[key] = {
        "key": key,
        "username": username,
        "scopes": scopes,
        "created_at": datetime.utcnow(),
        "last_used": None,
        "rate_limit": 100,
    }

    return key

# Security Middleware
security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    request: Request = None
) -> Optional[User]:
    """Get current user from JWT token or API key."""
    if credentials:
        # JWT Token authentication
        token_data = verify_token(credentials.credentials)
        if token_data:
            return User(
                username=token_data.username,
                scopes=token_data.scopes
            )

    # API Key authentication (fallback)
    api_key = request.headers.get(API_KEY_NAME) if request else None
    if api_key:
        user_info = verify_api_key(api_key)
        if user_info:
            return User(
                username=user_info["username"],
                scopes=user_info["scopes"]
            )

    return None

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user."""
    if current_user and not current_user.disabled:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def check_scope(required_scope: str, user_scopes: list) -> bool:
    """Check if user has required scope."""
    return required_scope in user_scopes or "admin" in user_scopes

# Rate Limiting
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        # Clean old entries
        if key in self.requests:
            self.requests[key] = [req for req in self.requests[key] if req > window_start]

        # Check current count
        current_count = len(self.requests.get(key, []))
        if current_count >= limit:
            return False

        # Add current request
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key].append(now)

        return True

rate_limiter = RateLimiter()

def check_rate_limit(request: Request, limit: int = 100, window: int = 3600) -> bool:
    """Check rate limit for request."""
    # Use client IP or API key as identifier
    api_key = request.headers.get(API_KEY_NAME)
    client_ip = request.client.host if request.client else "unknown"

    identifier = api_key or client_ip

    return rate_limiter.is_allowed(identifier, limit, window)

# Input Validation and Sanitization
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove path separators and dangerous characters
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip('.')

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename

def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Validate file extension."""
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def hash_content(content: bytes) -> str:
    """Generate SHA256 hash of content for integrity checking."""
    return hashlib.sha256(content).hexdigest()

# CSRF Protection
def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)

def verify_csrf_token(session_token: str, request_token: str) -> bool:
    """Verify CSRF token."""
    if not session_token or not request_token:
        return False

    return hmac.compare_digest(session_token, request_token)

# Security Headers Middleware
def add_security_headers(response):
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response