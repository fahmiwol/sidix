# System Design

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari System Design Interview (Alex Xu), Designing Data-Intensive Applications (Kleppmann), dan dokumentasi AWS/GCP.
> Relevan untuk: senior engineers, architects, technical leads, interview candidates
> Tags: system-design, scalability, distributed-systems, caching, databases, microservices, kafka, redis, cap-theorem, load-balancing

## Scalability: Horizontal vs Vertical

### Vertical Scaling (Scale Up)
Add more power (CPU, RAM, disk) to a single machine.
- Pros: No code changes, simpler operations, no distributed system complexity
- Cons: Hard upper limit, single point of failure, expensive at high end, downtime for upgrades

### Horizontal Scaling (Scale Out)
Add more machines to a pool.
- Pros: Theoretically unlimited, fault tolerant, commodity hardware
- Cons: Requires stateless services, distributed system complexity, data consistency challenges

**Rule of thumb**: Vertical scale until the pain of a single machine forces horizontal scaling. For most services this is 4–32 CPU cores, 16–256 GB RAM. Anything beyond needs horizontal scaling.

## Load Balancing

Distributes incoming traffic across multiple servers to prevent any single server from becoming a bottleneck.

### Algorithms
```
Round Robin          — requests distributed sequentially across servers
Weighted Round Robin — servers with more capacity get proportionally more traffic
Least Connections    — routes to server with fewest active connections
IP Hash              — consistent mapping of client IP → server (session affinity)
Random               — simple, works surprisingly well at scale
```

### Layer 4 vs Layer 7
- **L4 (TCP/UDP)**: Faster, forwards packets without inspecting content (HAProxy TCP mode, AWS NLB)
- **L7 (HTTP)**: Can route based on URL path, headers, cookies; can terminate SSL; smarter but more CPU (Nginx, AWS ALB)

### Health Checks
```nginx
# Nginx upstream with health checks
upstream app_servers {
    least_conn;
    server 10.0.0.1:8000 weight=3;
    server 10.0.0.2:8000 weight=1;
    server 10.0.0.3:8000 backup;  # only used if primaries fail
    
    keepalive 100;  # persistent connections to upstreams
}

server {
    listen 80;
    location / {
        proxy_pass http://app_servers;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }
}
```

## Caching

Caching stores expensive-to-compute results for fast retrieval. The single biggest performance win in most systems.

### Cache Hierarchy
```
L1/L2/L3 CPU cache   — nanoseconds, managed by hardware
In-process memory    — microseconds, lost on restart (e.g., Python dict, lru_cache)
Redis/Memcached      — microseconds over loopback, shared across processes
CDN edge cache       — milliseconds, geographically distributed
Browser cache        — eliminates network round trip entirely
```

### Cache Patterns
```python
# Cache-Aside (Lazy Loading) — most common
def get_user(user_id: int) -> dict:
    key = f"user:{user_id}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)          # cache hit
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)
    redis.setex(key, 3600, json.dumps(user))  # cache for 1 hour
    return user

# Write-Through — write to cache and DB simultaneously
def update_user(user_id: int, data: dict) -> None:
    db.execute("UPDATE users SET ... WHERE id = %s", user_id)
    key = f"user:{user_id}"
    redis.setex(key, 3600, json.dumps(data))  # always up to date

# Write-Behind (Write-Back) — write to cache first, async flush to DB
# Risk: data loss if cache fails before flush

# Read-Through — cache fetches from DB on miss automatically
# Common with caching libraries (e.g., Spring Cache)
```

### Cache Invalidation Strategies
```
TTL (Time-to-Live)        — expire after fixed duration; simple but stale window
Event-based invalidation  — invalidate on write events (pub/sub)
Cache-busting URLs        — for static assets: /app.a1b2c3.js
Versioned keys            — cache key includes version: user:42:v3

# The two hard problems in CS: cache invalidation and naming things
```

### Redis Patterns
```python
import redis
import json
from datetime import timedelta

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# String (simple key-value)
r.set("session:abc123", json.dumps({"user_id": 42}), ex=1800)  # 30 min
r.get("session:abc123")

# Hash (object with fields — better than JSON for partial updates)
r.hset("user:42", mapping={"name": "Fahmi", "email": "f@example.com", "score": "100"})
r.hincrby("user:42", "score", 10)
r.hget("user:42", "score")

# Sorted Set (leaderboard, rate limiting)
r.zadd("leaderboard", {"player1": 1500, "player2": 1200})
r.zrevrange("leaderboard", 0, 9, withscores=True)  # top 10

# List (queue, activity feed)
r.rpush("notifications:42", json.dumps({"type": "like", "post": 7}))
r.lrange("notifications:42", 0, 49)  # latest 50

# Rate limiting with sliding window
def is_rate_limited(user_id: str, limit: int = 100, window: int = 60) -> bool:
    key = f"rate:{user_id}:{int(time.time() // window)}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count > limit

# Pub/Sub
publisher = redis.Redis()
subscriber = redis.Redis()
sub = subscriber.pubsub()
sub.subscribe("notifications")

publisher.publish("notifications", json.dumps({"event": "user_joined", "user": 42}))
for message in sub.listen():
    if message["type"] == "message":
        data = json.loads(message["data"])
```

## Databases: SQL vs NoSQL

### When to Use SQL (PostgreSQL, MySQL)
- Complex relational data with joins
- Strong ACID transactions required
- Structured, well-defined schema
- Reporting and analytics queries
- Examples: financial data, user accounts, inventory

### When to Use NoSQL
| Type | Examples | Best For |
|------|----------|----------|
| Document | MongoDB, Firestore | Semi-structured data, flexible schema |
| Key-Value | Redis, DynamoDB | Sessions, caching, simple lookups |
| Column Family | Cassandra, HBase | Time-series, write-heavy, wide rows |
| Graph | Neo4j, Neptune | Relationships, social graphs, recommendations |

### Database Scaling Patterns

#### Read Replicas
```
Primary (read-write)
├── Replica 1 (read-only)
├── Replica 2 (read-only)
└── Replica 3 (read-only) — maybe in another region

Reads → route to replicas (70-90% of traffic is reads in most apps)
Writes → always go to primary
Replication lag → 10ms-seconds, acceptable for most reads
```

#### Sharding (Horizontal Partitioning)
Split data across multiple database servers.
```
# Hash sharding
shard_id = hash(user_id) % num_shards
# → deterministic, even distribution
# → resharding requires data migration

# Range sharding (by date, alphabetical)
shard = "2024" if date.year == 2024 else "2023"
# → good for time-series, easy resharding
# → hotspot risk (all new writes go to latest shard)

# Directory sharding
# → lookup table maps key → shard
# → flexible but single point of failure (the directory)
```

#### Indexes
```sql
-- B-tree index (default) — equality, range queries
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_posts_created ON posts (created_at DESC);

-- Composite index — order matters! (a, b) serves queries on a alone and (a, b) together
CREATE INDEX idx_posts_user_date ON posts (user_id, created_at DESC);

-- Partial index — index subset of rows
CREATE INDEX idx_active_users ON users (email) WHERE active = true;

-- Covering index — includes all columns needed by query, avoids table lookup
CREATE INDEX idx_posts_covering ON posts (user_id, created_at) INCLUDE (title, status);
```

## Microservices vs Monolith

### Monolith First
For most new products, start with a monolith:
- Simpler to develop, test, and deploy
- Easy refactoring across service boundaries
- No distributed system overhead
- Split when: team > 10 engineers, deploy frequency > 1/day, clear domain boundaries emerge

### Microservices Characteristics
```
Each service:
├── Owns its data (no shared database)
├── Communicates via APIs (REST, gRPC) or events (Kafka)
├── Deployed independently
├── Can use different tech stack
└── Bounded by a business domain (not a technical layer)

Communication patterns:
├── Synchronous: REST, gRPC — for real-time, blocking calls
└── Asynchronous: Message queues — for decoupling, resilience
```

### Service Mesh (for mature microservices)
Istio, Linkerd provide: mTLS between services, traffic management, observability, circuit breaking — without application code changes.

## Message Queues: Kafka and RabbitMQ

### Apache Kafka
Distributed log. Messages are stored durably and can be replayed.
```
Concepts:
├── Topic: category of messages (like a table name)
├── Partition: ordered log within a topic (unit of parallelism)
├── Consumer Group: multiple consumers share partitions (one partition → one consumer in group)
├── Offset: position in partition (consumer tracks its own offset)
└── Retention: messages kept for days/weeks (default 7 days)

Use cases:
├── Event streaming (user activity, IoT)
├── Activity log / audit trail
├── Data pipeline between services
└── Replaying events to rebuild state
```

```python
from kafka import KafkaProducer, KafkaConsumer
import json

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

producer.send("user-events", key="user-42", value={"type": "login", "ts": 1700000000})
producer.flush()

consumer = KafkaConsumer(
    "user-events",
    bootstrap_servers=["localhost:9092"],
    group_id="analytics-service",
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

for message in consumer:
    print(f"Partition {message.partition}, Offset {message.offset}: {message.value}")
```

### RabbitMQ
Traditional message broker. Messages are consumed and deleted.
```
Concepts:
├── Exchange: receives messages, routes to queues
│   ├── Direct: routes by exact routing key
│   ├── Fanout: broadcasts to all bound queues
│   ├── Topic: routes by pattern (*.error, logs.#)
│   └── Headers: routes by message headers
├── Queue: holds messages until consumed
└── Binding: link between exchange and queue with routing key

Use cases:
├── Task queues (background jobs)
├── RPC patterns
└── When you need dead-letter queues, priorities, per-message TTL
```

## CAP Theorem

In a distributed system, you can only guarantee **two** of:
- **Consistency**: all nodes see the same data at the same time
- **Availability**: every request receives a response (not necessarily the latest data)
- **Partition Tolerance**: system continues operating despite network partitions

Network partitions are unavoidable in real distributed systems. So the real choice is **CP vs AP**:
- **CP systems** (e.g., HBase, Zookeeper, Redis Cluster): may reject requests during partition to maintain consistency
- **AP systems** (e.g., Cassandra, CouchDB, DynamoDB): remain available but may serve stale data

### PACELC Extension
Even without partition, there's a trade-off between **latency** and **consistency**. A more complete model: during Partition → AP or CP; Else → Latency or Consistency.

## Consistency Patterns

```
Strong consistency       — read always returns latest write (sync replication)
Eventual consistency     — reads may be stale, but will converge (async replication)
Read-your-writes         — user always sees their own writes immediately
Monotonic reads          — once you read value X, you won't read older values
Causal consistency       — causally related operations seen in order

# Practical implementations:
# Strong: write to all replicas synchronously (high latency, lower availability)
# Eventual: write to primary, async replicate (lower latency, risk of stale reads)
# Read-your-writes: route reads to primary for user's own data
```

## API Gateway

Entry point for all external requests. Handles cross-cutting concerns:
```
├── Authentication & Authorization  — validate JWT, check permissions
├── Rate Limiting                   — per-user or per-key limits
├── SSL Termination                 — decrypt HTTPS, forward HTTP internally
├── Request Routing                 — route /api/users → user-service
├── Load Balancing                  — across service instances
├── Request/Response Transformation — format conversion, header injection
├── Circuit Breaker                 — fail fast when downstream is unhealthy
└── Observability                   — centralized logging, metrics, tracing

Examples: Kong, AWS API Gateway, Nginx, Traefik, Envoy
```

## Circuit Breaker Pattern

Prevents cascading failures. Like an electrical circuit breaker.
```
States:
├── CLOSED   — requests flow normally; failures tracked
├── OPEN     — circuit tripped; requests fail immediately (no downstream call)
└── HALF-OPEN — after timeout, allows test request; if success → CLOSED, else → OPEN

Thresholds: trip at 50% failure rate in 10-second window
Recovery: wait 30 seconds before trying HALF-OPEN
```

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=30):
        self.threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN — fast fail")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN
```

## Event Sourcing and CQRS

### Event Sourcing
Instead of storing current state, store all events that led to the state. State is derived by replaying events.
```
Traditional: User table { id, name, balance=90 }

Event sourced:
  UserCreated    { id: 1, name: "Fahmi" }
  MoneyDeposited { id: 1, amount: 100 }
  MoneyWithdrawn { id: 1, amount: 10 }
  → Current state = replay = 100 - 10 = 90

Benefits: full audit trail, replay to any point in time, easy debugging
Drawbacks: complex queries, storage growth, eventual consistency
```

### CQRS (Command Query Responsibility Segregation)
Separate read and write models.
```
Write side (Command):
  POST /transfer → validates, creates event → stored in event store

Read side (Query):
  GET /balance → queries pre-built read model (optimized for reads)

The read model is updated asynchronously from events.
```

## Back-of-Envelope Estimation

```
Latency numbers (approximate):
  L1 cache reference:         0.5 ns
  RAM reference:              100 ns
  SSD sequential read:        100 μs
  Network round trip (DC):    500 μs
  HDD seek:                   10 ms
  Network round trip (cross-country): 150 ms

Traffic estimation:
  1 million users × 10 requests/day = ~115 requests/second
  1 million users × 100 requests/day = ~1,150 req/sec (needs load balancing)

Storage estimation:
  1 million users × 1 KB profile = 1 GB
  1 million photos × 1 MB = 1 TB
  Twitter: 500M tweets/day × 280 chars = ~150 GB/day text

Bandwidth: 10 GB/s per 10 Gbps NIC (theoretical max)
```

## Referensi & Sumber Lanjut
- "Designing Data-Intensive Applications" — Martin Kleppmann
- "System Design Interview" Vol. 1 & 2 — Alex Xu
- https://highscalability.com/ — real-world architecture case studies
- https://aws.amazon.com/architecture/
- https://martin.kleppmann.com/
- roadmap.sh/system-design
