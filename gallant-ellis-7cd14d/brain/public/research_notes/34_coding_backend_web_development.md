# Backend Web Development: FastAPI, REST, Auth, and Databases

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari dokumentasi FastAPI, RFC 7231/7235, OWASP guidelines, dan praktik industri.
> Relevan untuk: backend developers, API designers, full-stack engineers
> Tags: fastapi, rest-api, http, jwt, authentication, cors, websocket, sqlalchemy, postgresql, backend

## HTTP Fundamentals

### Methods and Semantics
| Method | Semantics | Idempotent | Safe | Body |
|--------|-----------|------------|------|------|
| GET    | Retrieve resource | Yes | Yes | No |
| POST   | Create / process | No | No | Yes |
| PUT    | Replace resource | Yes | No | Yes |
| PATCH  | Partial update | No | No | Yes |
| DELETE | Remove resource | Yes | No | Optional |
| HEAD   | GET metadata only | Yes | Yes | No |
| OPTIONS| CORS preflight | Yes | Yes | No |

### Status Codes
```
2xx Success
  200 OK                — GET, PUT, PATCH success
  201 Created           — POST that creates resource; include Location header
  202 Accepted          — async operation started, not finished
  204 No Content        — DELETE success, or PATCH with no response body

3xx Redirection
  301 Moved Permanently — update bookmarks
  304 Not Modified      — ETag/If-None-Match cache hit

4xx Client Errors
  400 Bad Request       — malformed syntax, validation failure
  401 Unauthorized      — missing/invalid credentials (authentication)
  403 Forbidden         — authenticated but not authorized
  404 Not Found         — resource doesn't exist
  409 Conflict          — state conflict (duplicate, version mismatch)
  422 Unprocessable     — valid syntax but semantic errors (FastAPI default for validation)
  429 Too Many Requests — rate limit hit; include Retry-After header

5xx Server Errors
  500 Internal Server Error — unexpected server failure
  502 Bad Gateway           — upstream failure
  503 Service Unavailable   — overloaded or maintenance; include Retry-After
```

## REST API Design Principles

### Resource-Oriented Design
```
# Resources are nouns, not verbs
GET    /users              → list users (paginated)
POST   /users              → create user
GET    /users/{id}         → get specific user
PUT    /users/{id}         → replace user
PATCH  /users/{id}         → partial update
DELETE /users/{id}         → delete user

# Nested resources for clear ownership
GET  /users/{id}/posts     → posts owned by user
POST /users/{id}/posts     → create post under user
GET  /users/{id}/posts/{post_id}  → specific post

# Actions that don't map to CRUD: use sub-resource verbs
POST /users/{id}/activate
POST /orders/{id}/cancel
POST /payments/{id}/refund

# Versioning — always include from day 1
/api/v1/users
/api/v2/users   # breaking changes bump version

# Alternative: header versioning
Accept: application/vnd.myapi.v2+json
```

### Pagination, Filtering, Sorting
```
# Cursor-based pagination (preferred for large datasets)
GET /posts?cursor=eyJpZCI6MTAwfQ&limit=20
Response: { "data": [...], "next_cursor": "eyJpZCI6MTIwfQ", "has_more": true }

# Offset pagination (simple but has drift issues)
GET /posts?page=2&per_page=20
Response: { "data": [...], "total": 500, "page": 2, "pages": 25 }

# Filtering
GET /posts?status=published&author_id=42&created_after=2024-01-01

# Sorting
GET /posts?sort=-created_at,title  # - prefix = descending

# Field selection (sparse fieldsets)
GET /users?fields=id,name,email
```

## FastAPI

FastAPI is a modern, high-performance Python web framework built on Starlette and Pydantic.

### Basic Application
```python
from fastapi import FastAPI, HTTPException, status, Depends, Query, Path
from pydantic import BaseModel, EmailStr, Field
from typing import Annotated

app = FastAPI(
    title="SIDIX API",
    version="1.0.0",
    description="AI Knowledge Platform",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
)

# Pydantic models — used for request/response validation
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    model_config = {"from_attributes": True}  # enables ORM mode (Pydantic v2)

# Route with path parameter, query parameter, body
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=list[UserResponse])
async def list_users(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page
    return db.query(User).offset(offset).limit(per_page).all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: Annotated[int, Path(ge=1)],
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Dependency Injection
```python
from fastapi import Depends
from sqlalchemy.orm import Session

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Role-based access control
def require_role(role: str):
    def dependency(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

@app.delete("/admin/users/{id}")
async def admin_delete_user(
    id: int,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ...
```

### Middleware
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import uuid

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sidix.ai", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Custom middleware — request ID + timing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    
    response = await call_next(request)
    
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed:.4f}s"
    return response
```

### Background Tasks
```python
from fastapi import BackgroundTasks

def send_email_async(email: str, message: str):
    # runs after response is sent
    send_smtp(email, message)

def cleanup_temp_files(paths: list[str]):
    for path in paths:
        Path(path).unlink(missing_ok=True)

@app.post("/users/{id}/invite")
async def invite_user(id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.get(User, id)
    background_tasks.add_task(send_email_async, user.email, "You're invited!")
    background_tasks.add_task(cleanup_temp_files, ["/tmp/invite_data.json"])
    return {"message": "Invitation sent"}
```

### WebSockets
```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    
    async def broadcast(self, message: str):
        for ws in self.active:
            await ws.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{room_id}")
async def chat_ws(websocket: WebSocket, room_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Room {room_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

## JWT Authentication

```python
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-minimum-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_tokens(user_id: int) -> dict[str, str]:
    access = create_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

# Login endpoint
@app.post("/auth/login")
async def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_tokens(user.id)

# Token refresh
@app.post("/auth/refresh")
async def refresh(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        user_id = int(payload["sub"])
    except (jwt.JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return create_tokens(user_id)
```

## Rate Limiting

```python
# Using slowapi (starlette-compatible rate limiter)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/search")
@limiter.limit("10/minute")        # 10 requests per minute per IP
async def search(request: Request, q: str):
    return {"query": q, "results": []}

# Per-user rate limiting
@app.get("/api/generate")
@limiter.limit("5/minute", key_func=lambda req: req.state.user_id)
async def generate(request: Request, user: User = Depends(get_current_user)):
    request.state.user_id = str(user.id)
    return {}
```

## Database Integration: SQLAlchemy + PostgreSQL

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.sql import func

DATABASE_URL = "postgresql+psycopg2://user:pass@localhost:5432/sidix"

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_users_email_lower", func.lower(email)),  # case-insensitive index
    )

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    author = relationship("User", back_populates="posts")

# Async SQLAlchemy (for FastAPI async routes)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/sidix",
    echo=False,
    pool_size=20,
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Repository Pattern
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def list_paginated(self, page: int = 1, per_page: int = 20) -> list[User]:
        offset = (page - 1) * per_page
        result = await self.session.execute(
            select(User).offset(offset).limit(per_page).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update(self, user_id: int, data: dict) -> User | None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(**data)
        )
        await self.session.commit()
        return await self.get_by_id(user_id)
```

## Error Handling and Validation

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Custom exception
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message}
    )

# Pydantic validation errors → 422 with details
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "details": [
                {"field": " -> ".join(str(l) for l in e["loc"]), "message": e["msg"]}
                for e in exc.errors()
            ]
        }
    )
```

## Async Patterns in FastAPI

```python
import asyncio
from typing import AsyncIterator

# Streaming response
from fastapi.responses import StreamingResponse

async def generate_tokens(prompt: str) -> AsyncIterator[str]:
    """Simulate LLM token streaming."""
    words = f"Response to: {prompt}".split()
    for word in words:
        yield f"data: {word}\n\n"
        await asyncio.sleep(0.05)

@app.get("/chat/stream")
async def stream_chat(prompt: str):
    return StreamingResponse(
        generate_tokens(prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# Lifespan — startup/shutdown events (FastAPI 0.95+)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    redis_pool = await init_redis()
    app.state.redis = redis_pool
    yield
    # Shutdown
    await redis_pool.close()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## OpenAPI / Swagger Best Practices

```python
# Rich metadata for generated docs
@app.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user",
    description="Creates a user account. Email must be unique.",
    response_description="The created user object",
    tags=["users"],
    responses={
        409: {"description": "Email already exists"},
        422: {"description": "Validation error"},
    }
)
async def create_user(user: UserCreate):
    ...

# Group routes with routers
from fastapi import APIRouter

users_router = APIRouter(prefix="/users", tags=["users"])
posts_router = APIRouter(prefix="/posts", tags=["posts"])

app.include_router(users_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")
```

## Referensi & Sumber Lanjut
- https://fastapi.tiangolo.com/
- https://docs.pydantic.dev/
- https://docs.sqlalchemy.org/en/20/
- https://owasp.org/www-project-api-security/
- https://jwt.io/introduction
- roadmap.sh/backend
- roadmap.sh/api-design
