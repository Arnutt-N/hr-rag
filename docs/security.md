# HR-RAG Security Best Practices

## Overview

This document outlines security best practices for the HR-RAG system. Given that HR documents often contain sensitive employee information, strong security measures are essential.

## Security Principles

1. **Defense in Depth** - Multiple layers of security
2. **Least Privilege** - Minimal access needed for each role
3. **Data Minimization** - Only collect what's necessary
4. **Zero Trust** - Verify every request, trust nothing

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Network Security                               │   │
│  │  • HTTPS/TLS 1.3                                         │   │
│  │  • Firewall / WAF                                        │   │
│  │  • DDoS protection (Cloudflare)                         │   │
│  │  • VPN for admin access                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Authentication & Authorization                 │   │
│  │  • JWT tokens with short expiry                         │   │
│  │  • OAuth 2.0 / SSO integration                          │   │
│  │  • Role-Based Access Control (RBAC)                    │   │
│  │  • API key rotation                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Application Security                         │   │
│  │  • Input validation & sanitization                     │   │
│  │  • Rate limiting                                        │   │
│  │  • Request/response logging                             │   │
│  │  • SQL injection prevention                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Data Security                                 │   │
│  │  • Encryption at rest (AES-256)                        │   │
│  │  • PII detection & masking                              │   │
│  │  • Data retention policies                              │   │
│  │  • Secure key management                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication

### JWT Implementation

```python
# backend/app/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    user_id: str
    role: str
    exp: datetime

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except JWTError:
        raise ValueError("Invalid token")

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### FastAPI Dependency for Auth

```python
# backend/app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    try:
        token_data = verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": token_data.user_id,
        "role": token_data.role
    }

def require_role(allowed_roles: list[str]):
    """Dependency factory for role-based access"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker
```

## Role-Based Access Control (RBAC)

### Roles Definition

```python
# backend/app/models/schemas.py
from enum import Enum
from pydantic import BaseModel

class UserRole(str, Enum):
    ADMIN = "admin"         # Full access
    HR_MANAGER = "hr_manager"  # Manage HR docs
    EMPLOYEE = "employee"   # Read-only access
    GUEST = "guest"         # Limited access

class Permission(str, Enum):
    # Document permissions
    DOC_READ = "doc:read"
    DOC_UPLOAD = "doc:upload"
    DOC_DELETE = "doc:delete"
    DOC_ADMIN = "doc:admin"
    
    # Chat permissions
    CHAT_READ = "chat:read"
    CHAT_WRITE = "chat:write"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    USER_MANAGE = "admin:user"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.DOC_READ, Permission.DOC_UPLOAD, Permission.DOC_DELETE,
        Permission.DOC_ADMIN, Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.ADMIN_READ, Permission.ADMIN_WRITE, Permission.USER_MANAGE
    ],
    UserRole.HR_MANAGER: [
        Permission.DOC_READ, Permission.DOC_UPLOAD, Permission.DOC_DELETE,
        Permission.CHAT_READ, Permission.CHAT_WRITE, Permission.ADMIN_READ
    ],
    UserRole.EMPLOYEE: [
        Permission.DOC_READ, Permission.CHAT_READ, Permission.CHAT_WRITE
    ],
    UserRole.GUEST: [
        Permission.CHAT_READ, Permission.CHAT_WRITE
    ]
}
```

### RBAC Implementation

```python
# backend/app/auth/rbac.py
from functools import wraps
from fastapi import HTTPException, status

def check_permission(permission: Permission):
    """Decorator for permission checking"""
    def decorator(func):
        @wraps(func)
        async def wrapper(current_user: dict, *args, **kwargs):
            user_role = current_user.get("role")
            allowed = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
            
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator

# Usage in routes
@app.post("/documents")
@check_permission(Permission.DOC_UPLOAD)
async def upload_document(current_user: dict, ...):
    ...
```

## Rate Limiting

```python
# backend/app/middleware/rate_limiter.py
from fastapi import Request, HTTPException, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

# Initialize rate limiter
@app.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://localhost:6379")
    await FastAPILimiter.init(redis_client)

# Rate limit by user role
def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user"""
    if request.state.user:
        return f"ratelimit:{request.state.user['user_id']}"
    return f"ratelimit:{request.client.host}"

# Apply rate limits
@app.post("/chat")
@limiter.limit(get_rate_limit_key)
async def chat(request: Request, body: ChatRequest):
    # Chat: 30 requests/minute for authenticated, 10 for anonymous
    ...

@app.post("/documents/upload")
@limiter.limit("10/minute")  # Stricter limit for heavy operations
async def upload_document(request: Request, ...):
    ...
```

## Input Validation

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field, validator
import re

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove potentially dangerous characters
        v = v.strip()
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)",
            r"(--|;|\/\*|\*\/)"
        ]
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid characters in query")
        
        return v

class DocumentUpload(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    
    @validator('filename')
    def validate_filename(cls, v):
        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename")
        
        # Allow only safe extensions
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError("Unsupported file type")
        
        return v
```

## PII Detection and Masking

```python
# backend/app/security/pii_detection.py
import re
from typing import Optional

class PIIDetector:
    """Detect and mask Personally Identifiable Information"""
    
    # Thai ID (เลขบัตรประจำตัวประชาชน)
    THAI_ID_PATTERN = r'\b\d{13}\b'
    
    # Phone number (Thai format)
    THAI_PHONE_PATTERN = r'\b0\d{8,9}\b'
    
    # Email
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Bank account
    BANK_ACCOUNT_PATTERN = r'\b\d{10,16}\b'
    
    @classmethod
    def detect_pii(cls, text: str) -> list[dict]:
        """Detect PII in text"""
        findings = []
        
        patterns = [
            ('thai_id', cls.THAI_ID_PATTERN),
            ('phone', cls.THAI_PHONE_PATTERN),
            ('email', cls.EMAIL_PATTERN),
            ('bank_account', cls.BANK_ACCOUNT_PATTERN),
        ]
        
        for pii_type, pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    'type': pii_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return findings
    
    @classmethod
    def mask_pii(cls, text: str) -> str:
        """Replace PII with masked version"""
        findings = cls.detect_pii(text)
        
        # Sort by position (reverse) to avoid index shifting
        findings.sort(key=lambda x: x['start'], reverse=True)
        
        masked = text
        for finding in findings:
            pii_type = finding['type']
            value = finding['value']
            
            if pii_type == 'thai_id':
                replacement = f"XXX-XX-{value[5:8]}-{value[8:13]}"
            elif pii_type == 'phone':
                replacement = f"0XX-XXX-{value[-4:]}"
            elif pii_type == 'email':
                parts = value.split('@')
                replacement = f"{parts[0][:2]}XXX@{parts[1]}"
            elif pii_type == 'bank_account':
                replacement = f"XXXXXX{value[-4:]}"
            else:
                replacement = "XXX"
            
            masked = masked[:finding['start']] + replacement + masked[finding['end']:]
        
        return masked
```

## API Key Management

```python
# backend/app/security/api_keys.py
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

class APIKeyManager:
    """Manage API keys for external integrations"""
    
    def __init__(self, db):
        self.db = db
    
    def generate_key(self, user_id: str, name: str, expires_in_days: int = 90) -> str:
        """Generate new API key"""
        key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Store hash, not the key itself
        api_key_record = {
            'user_id': user_id,
            'name': name,
            'key_hash': key_hash,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=expires_in_days),
            'last_used': None,
            'is_active': True
        }
        
        self.db.api_keys.insert(api_key_record)
        
        # Return full key only once!
        return key
    
    def verify_key(self, key: str) -> Optional[dict]:
        """Verify API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        api_key = self.db.api_keys.find_one({
            'key_hash': key_hash,
            'is_active': True,
            'expires_at': {'$gt': datetime.utcnow()}
        })
        
        if api_key:
            # Update last used
            self.db.api_keys.update_one(
                {'_id': api_key['_id']},
                {'$set': {'last_used': datetime.utcnow()}}
            )
        
        return api_key
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        result = self.db.api_keys.update_one(
            {'key_hash': key_hash},
            {'$set': {'is_active': False}}
        )
        return result.modified_count > 0
```

## Secure Logging

```python
# backend/app/middleware/logging.py
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecureLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests without sensitive data"""
    
    PII_FIELDS = ['password', 'token', 'api_key', 'secret', 'ssn', 'id_card']
    
    async def dispatch(self, request: Request, call_next):
        # Log request (sanitized)
        log_data = {
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent'),
        }
        
        # Don't log request body for sensitive endpoints
        if not any(sensitive in request.url.path for sensitive in ['/login', '/upload']):
            # Log will be added later
        
        response = await call_next(request)
        
        log_data['status_code'] = response.status_code
        
        # Log (use your logging infrastructure)
        logging.info(json.dumps(log_data))
        
        return response

def sanitize_for_logging(data: dict) -> dict:
    """Remove sensitive fields before logging"""
    sanitized = data.copy()
    
    for field in SecureLoggingMiddleware.PII_FIELDS:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'
    
    return sanitized
```

## Environment Security

```bash
# .env.example (never commit .env)
# Copy this file and fill in actual values

# Authentication
SECRET_KEY=change-this-to-random-32-character-string
JWT_SECRET=change-this-to-another-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hr_rag
REDIS_URL=redis://localhost:6379

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# External Services
SMTP_HOST=smtp.example.com
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60
```

## Security Checklist

- [ ] Enable HTTPS/TLS 1.3
- [ ] Use strong JWT secrets (32+ random characters)
- [ ] Implement rate limiting
- [ ] Add PII detection/masking
- [ ] Enable request logging (without sensitive data)
- [ ] Use environment variables for secrets
- [ ] Implement RBAC
- [ ] Enable CORS restrictions
- [ ] Add input validation
- [ ] Regular security audits
- [ ] API key rotation policy
- [ ] Backup and disaster recovery

---

*Generated for HR-RAG Project*
