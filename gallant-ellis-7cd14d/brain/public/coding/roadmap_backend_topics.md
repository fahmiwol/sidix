# Backend Development Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/backend (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/backend

## Internet Fundamentals

### How the Internet Works
- **Client → DNS → IP → TCP → HTTP → Server → Response**
- DNS: resolves domain → IP address (A record, AAAA, CNAME, MX, TXT)
- TCP: reliable, ordered, connection-based (3-way handshake: SYN, SYN-ACK, ACK)
- UDP: fast, unreliable, connectionless (DNS, video streaming, gaming)
- TLS: encrypts data; HTTPS = HTTP over TLS (certificates, asymmetric + symmetric keys)

### HTTP
```
Request:
  GET /api/users HTTP/1.1
  Host: api.example.com
  Authorization: Bearer eyJ...
  Content-Type: application/json

Response:
  HTTP/1.1 200 OK
  Content-Type: application/json
  Cache-Control: max-age=3600
  
  {"users": [...]}

Status codes:
  2xx Success: 200 OK, 201 Created, 204 No Content
  3xx Redirect: 301 Moved Permanently, 302 Found, 304 Not Modified
  4xx Client Error: 400 Bad Request, 401 Unauthorized, 403 Forbidden,
                    404 Not Found, 409 Conflict, 422 Unprocessable Entity,
                    429 Too Many Requests
  5xx Server Error: 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable

HTTP Methods:
  GET    — read resource (idempotent, no body)
  POST   — create resource (not idempotent)
  PUT    — replace resource (idempotent)
  PATCH  — partial update (not idempotent by default)
  DELETE — delete resource (idempotent)
  HEAD   — like GET, but no response body
  OPTIONS — CORS preflight, method discovery
```

### HTTP/2 and HTTP/3
- **HTTP/2**: multiplexing (multiple requests over one TCP connection), header compression (HPACK), server push
- **HTTP/3**: uses QUIC (UDP-based), reduces head-of-line blocking, faster connection setup

## APIs

### REST API Design
```
REST constraints:
1. Stateless — server stores no client session state
2. Client-Server — clear separation of concerns
3. Uniform Interface — consistent URL structure
4. Cacheable — responses must declare cacheability
5. Layered System — client doesn't know if direct/via proxy

URL conventions:
  GET    /users                  — list users
  POST   /users                  — create user
  GET    /users/{id}             — get user
  PUT    /users/{id}             — replace user
  PATCH  /users/{id}             — update user
  DELETE /users/{id}             — delete user
  GET    /users/{id}/orders      — user's orders (nested resource)
  POST   /users/{id}/deactivate  — actions use POST (not verbs in URL)

Query parameters:
  /users?page=2&limit=20
  /users?sort=name&order=desc
  /users?status=active
  /users?search=fahmi
  /posts?include=author,tags    — side-loading related

Versioning strategies:
  /api/v1/users                 — URL versioning (most common)
  Accept: application/vnd.api+json;version=1  — header versioning
  ?version=1                    — query param (avoid)
```

### FastAPI (Python)
```python
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional
import uvicorn

app = FastAPI(
    title="SIDIX API",
    version="1.0.0",
    description="SIDIX AI backend API"
)

# Request/Response models
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    age: Optional[int] = Field(None, ge=0, le=150)
    
    class Config:
        schema_extra = {"example": {"name": "Fahmi", "email": "fahmi@example.com"}}

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True  # Pydantic v2; orm_mode=True in v1

# Dependency injection
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    token = credentials.credentials
    user = verify_jwt(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# Routes
@app.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = db.query(User)
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    return query.offset(offset).limit(limit).all()

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(req: CreateUserRequest, db = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(**req.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global exception handler
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

### Authentication and Authorization

```python
# JWT Authentication
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-secret-key-from-env"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# RBAC (Role-Based Access Control)
def require_role(*roles: str):
    async def dependency(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return dependency

@app.delete("/users/{id}")
async def delete_user(
    id: int,
    admin = Depends(require_role("admin", "superuser")),
    db = Depends(get_db),
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}
```

## Databases

### SQL with SQLAlchemy
```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, relationship, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    orders = relationship("Order", back_populates="user", lazy="selectin")
    
    __table_args__ = (
        Index("idx_users_email", "email"),
    )

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Integer, nullable=False)  # store in cents
    user = relationship("User", back_populates="orders")

# Connection pool
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # check connection before using
)

# Queries
with Session(engine) as session:
    # Create
    user = User(name="Fahmi", email="fahmi@example.com")
    session.add(user)
    session.commit()
    
    # Read
    user = session.get(User, 1)
    users = session.query(User).filter(User.name.ilike("%fah%")).all()
    
    # Update
    user.name = "Updated Name"
    session.commit()
    
    # Delete
    session.delete(user)
    session.commit()
```

### Redis (Caching)
```python
import redis.asyncio as redis
import json
from typing import Optional

r = redis.from_url("redis://localhost:6379", decode_responses=True)

async def get_user(user_id: int, db) -> dict:
    # Check cache
    cached = await r.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    user = db.get_user(user_id)
    if not user:
        return None
    
    # Cache with TTL
    await r.setex(f"user:{user_id}", 300, json.dumps(user))  # 5 min TTL
    return user

async def invalidate_user(user_id: int):
    await r.delete(f"user:{user_id}")

# Rate limiting with Redis
async def check_rate_limit(client_id: str, limit: int, window: int) -> bool:
    key = f"rate_limit:{client_id}"
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, window)  # set TTL on first request
    return current <= limit
```

## Background Tasks and Queues

### Celery
```python
from celery import Celery
from celery.schedules import crontab

app = Celery("sidix", broker="redis://localhost:6379/0",
             backend="redis://localhost:6379/1")

app.conf.update(
    task_serializer="json",
    result_expires=3600,
    timezone="UTC",
)

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str):
    try:
        email_service.send(to=to, subject=subject, body=body)
    except Exception as exc:
        raise self.retry(exc=exc)

@app.task
def index_documents(doc_ids: list[int]):
    for doc_id in doc_ids:
        document = get_document(doc_id)
        search_index.index(document)

# Periodic tasks
app.conf.beat_schedule = {
    "cleanup-expired": {
        "task": "tasks.cleanup_expired_sessions",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
}

# Calling tasks
send_email.delay("user@example.com", "Welcome!", "Hello!")
send_email.apply_async(args=["user@example.com", "Hi", "Body"],
                       countdown=30)  # 30 second delay
result = send_email.apply_async(...)
result.get(timeout=60)  # wait for result
```

## WebSockets and Real-time

```python
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}
    
    async def connect(self, ws: WebSocket, user_id: str):
        await ws.accept()
        self.active[user_id] = ws
    
    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)
    
    async def send(self, user_id: str, message: dict):
        if ws := self.active.get(user_id):
            await ws.send_json(message)
    
    async def broadcast(self, message: dict):
        for ws in self.active.values():
            await ws.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(ws: WebSocket, user_id: str):
    await manager.connect(ws, user_id)
    try:
        while True:
            data = await ws.receive_json()
            # process data, broadcast, etc.
            await manager.broadcast({"from": user_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

## Security Best Practices

```
OWASP Top 10 (2021):
1.  Broken Access Control — enforce authz on every endpoint
2.  Cryptographic Failures — use TLS, hash passwords with bcrypt
3.  Injection — use parameterized queries, ORM
4.  Insecure Design — threat modeling, security by design
5.  Security Misconfiguration — disable debug mode, remove defaults
6.  Vulnerable Components — keep dependencies updated (dependabot)
7.  Authentication Failures — rate limit, lockout, MFA
8.  Software & Data Integrity — verify packages, CI/CD security
9.  Logging & Monitoring — log all auth events, set up alerts
10. SSRF — validate URLs, allowlist outbound connections

Input validation checklist:
- Validate type, length, format, range on all inputs
- Sanitize HTML (bleach library) if rendering user input
- Use parameterized queries (never string concatenation for SQL)
- Rate limit auth endpoints
- Set security headers (Content-Security-Policy, X-Frame-Options)
- Use HTTPS everywhere; HSTS header
- Store secrets in env vars / secret manager (never in code)
```

## Deployment

```yaml
# Gunicorn + Uvicorn workers (production ASGI)
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker brain_qa.agent_serve:app

# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker",
     "--bind", "0.0.0.0:8765", "brain_qa.agent_serve:app"]
```

## Referensi Lanjut
- https://roadmap.sh/backend
- https://fastapi.tiangolo.com/ — FastAPI documentation
- https://docs.sqlalchemy.org/ — SQLAlchemy
- https://owasp.org/www-project-top-ten/ — OWASP Top 10
- https://github.com/donnemartin/system-design-primer
- "Designing Data-Intensive Applications" — Martin Kleppmann
