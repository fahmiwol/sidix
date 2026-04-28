# SQL & Databases

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari PostgreSQL documentation, SQLAlchemy docs, Use The Index, Luke!, dan praktik industri.
> Relevan untuk: backend developers, data engineers, data analysts, full-stack engineers
> Tags: sql, postgresql, databases, indexes, transactions, acid, query-optimization, sqlalchemy, mongodb, redis, orm

## SQL Fundamentals

### SELECT — Querying Data
```sql
-- Basic SELECT
SELECT id, name, email FROM users;
SELECT * FROM users;  -- avoid * in production (fragile, slower)

-- WHERE — filter rows
SELECT * FROM users
WHERE active = true
  AND created_at > '2024-01-01'
  AND email LIKE '%@gmail.com'
  AND age BETWEEN 18 AND 65
  AND role IN ('admin', 'editor')
  AND deleted_at IS NULL;

-- ORDER BY, LIMIT, OFFSET
SELECT id, name, created_at
FROM posts
WHERE user_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 40;  -- page 3 of 20 per page

-- DISTINCT
SELECT DISTINCT country FROM users;

-- Aliases
SELECT u.id, u.name AS user_name, p.title AS post_title
FROM users u
JOIN posts p ON p.user_id = u.id;
```

### JOINs
```sql
-- INNER JOIN — only matching rows from both tables
SELECT u.name, p.title
FROM users u
INNER JOIN posts p ON p.user_id = u.id;

-- LEFT JOIN — all users, even without posts
SELECT u.name, COUNT(p.id) AS post_count
FROM users u
LEFT JOIN posts p ON p.user_id = u.id
GROUP BY u.id, u.name;

-- RIGHT JOIN — all posts (rarely used; rewrite as LEFT JOIN)
-- FULL OUTER JOIN — all rows from both sides
SELECT u.name, p.title
FROM users u
FULL OUTER JOIN posts p ON p.user_id = u.id;

-- CROSS JOIN — cartesian product
SELECT a.name, b.name FROM teams a CROSS JOIN teams b WHERE a.id != b.id;

-- Self JOIN — join a table with itself
SELECT a.name AS employee, b.name AS manager
FROM employees a
JOIN employees b ON a.manager_id = b.id;

-- Multiple JOINs
SELECT u.name, p.title, c.body AS comment, t.name AS tag
FROM users u
JOIN posts p ON p.user_id = u.id
LEFT JOIN comments c ON c.post_id = p.id
LEFT JOIN post_tags pt ON pt.post_id = p.id
LEFT JOIN tags t ON t.id = pt.tag_id
WHERE p.published = true
  AND p.created_at > NOW() - INTERVAL '30 days';
```

### GROUP BY, HAVING, Aggregates
```sql
-- Aggregate functions: COUNT, SUM, AVG, MIN, MAX
SELECT
    user_id,
    COUNT(*) AS total_posts,
    COUNT(*) FILTER (WHERE published = true) AS published_posts,
    MAX(created_at) AS latest_post,
    AVG(view_count)::numeric(10,2) AS avg_views
FROM posts
GROUP BY user_id;

-- HAVING — filter groups (not individual rows)
SELECT user_id, COUNT(*) AS post_count
FROM posts
GROUP BY user_id
HAVING COUNT(*) > 10  -- only users with more than 10 posts
ORDER BY post_count DESC;

-- ROLLUP — subtotals
SELECT category, subcategory, SUM(amount)
FROM sales
GROUP BY ROLLUP(category, subcategory);

-- Multiple aggregates
SELECT
    DATE_TRUNC('month', created_at) AS month,
    status,
    COUNT(*) AS count,
    SUM(amount) AS total_amount
FROM orders
WHERE created_at >= '2024-01-01'
GROUP BY DATE_TRUNC('month', created_at), status
ORDER BY month, status;
```

### Subqueries
```sql
-- Subquery in WHERE
SELECT * FROM users
WHERE id IN (
    SELECT DISTINCT user_id FROM orders WHERE status = 'completed'
);

-- Correlated subquery (references outer query — runs once per row, can be slow)
SELECT u.name,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count
FROM users u;

-- Subquery in FROM (derived table)
SELECT category, avg_price
FROM (
    SELECT category, AVG(price) AS avg_price
    FROM products
    GROUP BY category
) subq
WHERE avg_price > 100;

-- EXISTS — more efficient than IN for large sets
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.total > 1000
);

-- NOT EXISTS
SELECT * FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

### Common Table Expressions (CTEs)
```sql
-- Basic CTE — improves readability
WITH active_users AS (
    SELECT id, name, email
    FROM users
    WHERE active = true AND last_login > NOW() - INTERVAL '90 days'
),
user_stats AS (
    SELECT user_id, COUNT(*) AS order_count, SUM(total) AS lifetime_value
    FROM orders
    GROUP BY user_id
)
SELECT au.name, au.email, us.order_count, us.lifetime_value
FROM active_users au
LEFT JOIN user_stats us ON us.user_id = au.id
ORDER BY us.lifetime_value DESC NULLS LAST;

-- Recursive CTE — hierarchical data (org chart, categories, graph traversal)
WITH RECURSIVE category_tree AS (
    -- base case: top-level categories
    SELECT id, name, parent_id, 0 AS depth, name::text AS path
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- recursive case
    SELECT c.id, c.name, c.parent_id, ct.depth + 1,
           (ct.path || ' > ' || c.name)::text
    FROM categories c
    JOIN category_tree ct ON ct.id = c.parent_id
)
SELECT * FROM category_tree ORDER BY path;
```

### Window Functions
Window functions compute a value for each row based on a "window" of related rows, without collapsing rows like GROUP BY.

```sql
-- ROW_NUMBER — unique sequential number
SELECT
    id, name, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rank_in_dept
FROM employees;

-- RANK / DENSE_RANK (ties get same rank; RANK skips after tie, DENSE_RANK doesn't)
SELECT
    name, score,
    RANK() OVER (ORDER BY score DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rank
FROM leaderboard;

-- LAG / LEAD — access adjacent rows
SELECT
    date, revenue,
    LAG(revenue) OVER (ORDER BY date) AS prev_revenue,
    revenue - LAG(revenue) OVER (ORDER BY date) AS day_over_day_change,
    LEAD(revenue) OVER (ORDER BY date) AS next_revenue
FROM daily_revenue;

-- SUM / AVG running totals
SELECT
    date, amount,
    SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS running_total,
    AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7day_avg
FROM transactions;

-- FIRST_VALUE / LAST_VALUE
SELECT
    product, category, price,
    FIRST_VALUE(price) OVER (PARTITION BY category ORDER BY price) AS category_min_price,
    price - FIRST_VALUE(price) OVER (PARTITION BY category ORDER BY price) AS above_min
FROM products;

-- NTILE — divide into N buckets (quartiles, deciles)
SELECT name, score, NTILE(4) OVER (ORDER BY score) AS quartile
FROM students;
```

### INSERT, UPDATE, DELETE, UPSERT
```sql
-- INSERT
INSERT INTO users (name, email, created_at)
VALUES ('Fahmi', 'f@example.com', NOW());

-- INSERT multiple rows
INSERT INTO tags (name) VALUES ('python'), ('fastapi'), ('ai')
RETURNING id, name;  -- PostgreSQL: return inserted rows

-- UPSERT (INSERT ON CONFLICT)
INSERT INTO user_stats (user_id, login_count, last_login)
VALUES (42, 1, NOW())
ON CONFLICT (user_id) DO UPDATE SET
    login_count = user_stats.login_count + 1,
    last_login = EXCLUDED.last_login;  -- EXCLUDED = the row that was rejected

-- UPDATE
UPDATE users
SET last_login = NOW(), login_count = login_count + 1
WHERE id = 42
RETURNING id, last_login;

-- UPDATE with JOIN (PostgreSQL syntax)
UPDATE orders o
SET status = 'verified'
FROM users u
WHERE o.user_id = u.id
  AND u.email_verified = true
  AND o.status = 'pending';

-- DELETE
DELETE FROM sessions WHERE expires_at < NOW();
DELETE FROM logs WHERE id IN (SELECT id FROM logs ORDER BY created_at ASC LIMIT 1000);

-- TRUNCATE — much faster than DELETE for full table clear
TRUNCATE TABLE temp_data RESTART IDENTITY CASCADE;
```

## Indexes

Indexes dramatically speed up reads at the cost of write overhead and storage.

### Index Types
```sql
-- B-tree (default) — equality, range, ORDER BY, IS NULL
CREATE INDEX idx_posts_created ON posts (created_at DESC);

-- Composite index — column ORDER matters!
-- (user_id, created_at) can serve: WHERE user_id = ?
--                                  WHERE user_id = ? AND created_at > ?
-- Cannot serve: WHERE created_at > ? (leading column missing)
CREATE INDEX idx_posts_user_date ON posts (user_id, created_at DESC);

-- Partial index — index subset of rows (smaller, faster)
CREATE INDEX idx_active_users ON users (email) WHERE active = true;
CREATE INDEX idx_unread_messages ON messages (user_id, created_at) WHERE read = false;

-- Covering index (INCLUDE) — include extra columns to avoid table lookup
CREATE INDEX idx_posts_author ON posts (user_id, created_at DESC)
    INCLUDE (title, published);
-- Query: SELECT title, published FROM posts WHERE user_id = ? ORDER BY created_at DESC
-- Can be answered from index alone — no heap access

-- Unique index
CREATE UNIQUE INDEX idx_users_email ON users (lower(email));  -- case-insensitive unique

-- GIN index for full-text search
CREATE INDEX idx_posts_fts ON posts USING GIN (to_tsvector('english', title || ' ' || body));

-- GIN index for JSONB
CREATE INDEX idx_metadata ON events USING GIN (metadata jsonb_path_ops);

-- BRIN index for very large tables with naturally ordered data (timestamp, sequential id)
-- Tiny size, good for range scans on ordered columns
CREATE INDEX idx_logs_created ON logs USING BRIN (created_at);
```

### Index Usage Analysis
```sql
-- EXPLAIN ANALYZE — see actual query plan and timing
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM posts WHERE user_id = 42 ORDER BY created_at DESC LIMIT 10;

-- Key terms in query plan:
-- Seq Scan: full table scan (no index used or not beneficial)
-- Index Scan: uses index, follows pointers to heap
-- Index Only Scan: uses covering index, no heap access (fastest)
-- Bitmap Heap Scan: collects matching rows then accesses heap
-- Nested Loop: joins via index lookup per row
-- Hash Join: builds hash table of smaller side
-- Merge Join: requires both inputs sorted

-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- Table and index sizes
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Transactions and ACID

### ACID Properties
- **Atomicity**: All operations in a transaction succeed or all fail (no partial updates)
- **Consistency**: Database moves from one valid state to another (constraints enforced)
- **Isolation**: Concurrent transactions don't interfere with each other
- **Durability**: Committed transactions survive crashes (WAL/redo log)

### Transaction Control
```sql
-- Basic transaction
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;  -- or ROLLBACK if any step failed

-- Savepoints — partial rollback
BEGIN;
INSERT INTO orders (user_id, total) VALUES (42, 99.99);
SAVEPOINT after_order;

INSERT INTO order_items (order_id, product_id, qty) VALUES (LASTVAL(), 7, 2);
-- if this fails:
ROLLBACK TO SAVEPOINT after_order;  -- undo item insert, keep order

COMMIT;

-- Isolation levels (trade-off: higher isolation = more locking = less concurrency)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;  -- default; see only committed data
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;  -- same data throughout transaction
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;     -- strictest; prevents all anomalies
```

### Concurrency Anomalies
```
Read Phenomena (from less to more severe):

Dirty Read       — read uncommitted data from another transaction
                   (prevented by READ COMMITTED and above)

Non-repeatable  — same row read twice gives different values
Read             (prevented by REPEATABLE READ and above)

Phantom Read    — new rows appear in range query between reads
                   (prevented by SERIALIZABLE)

Lost Update     — two transactions update same row, one overwrites other
                   (use SELECT FOR UPDATE to lock rows)
```

```sql
-- Optimistic locking (application-level, no DB lock)
-- Add version column
SELECT id, name, balance, version FROM accounts WHERE id = 1;
-- Returns version = 5

UPDATE accounts
SET balance = 150, version = 6
WHERE id = 1 AND version = 5;  -- fails if someone else updated
-- If 0 rows updated → retry or fail

-- Pessimistic locking (FOR UPDATE)
BEGIN;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;  -- lock row
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

## Query Optimization

```sql
-- 1. Use indexes on WHERE, JOIN, ORDER BY columns
-- 2. Avoid functions on indexed columns in WHERE (prevents index use)
-- BAD:
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
-- GOOD: create functional index
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';  -- now uses index

-- 3. Avoid SELECT *
-- 4. Use LIMIT to avoid fetching unnecessary data
-- 5. Use EXISTS instead of IN for large subqueries
-- 6. Use JOINs instead of correlated subqueries
-- 7. Use CTEs for readability but be aware they can be optimization fences in older PG

-- Pagination: cursor-based is better than OFFSET for large datasets
-- OFFSET N scans and discards N rows — gets slower as page increases
-- BAD for large tables:
SELECT * FROM posts ORDER BY id LIMIT 20 OFFSET 10000;

-- GOOD (cursor-based):
SELECT * FROM posts WHERE id > :last_seen_id ORDER BY id LIMIT 20;

-- ANALYZE to update table statistics (planner uses these)
ANALYZE users;
ANALYZE posts;
VACUUM ANALYZE;  -- reclaim space + update statistics
```

## PostgreSQL-Specific Features

### JSONB
```sql
-- Create table with JSONB column
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert JSON
INSERT INTO events (type, payload) VALUES
    ('user.login', '{"user_id": 42, "ip": "1.2.3.4", "tags": ["mobile", "ios"]}');

-- Query JSONB (-> returns JSONB, ->> returns text)
SELECT payload -> 'user_id' AS user_id_json,
       payload ->> 'ip' AS ip_text,
       payload -> 'tags' ->> 0 AS first_tag
FROM events;

-- Filter on JSONB
SELECT * FROM events WHERE payload ->> 'ip' = '1.2.3.4';
SELECT * FROM events WHERE (payload ->> 'user_id')::int = 42;
SELECT * FROM events WHERE payload ? 'error_code';  -- has key
SELECT * FROM events WHERE payload @> '{"user_id": 42}';  -- contains (uses GIN index)

-- Update JSONB
UPDATE events
SET payload = payload || '{"country": "ID"}'  -- merge/overwrite key
WHERE id = 1;

UPDATE events
SET payload = payload - 'sensitive_key'  -- remove key
WHERE id = 1;

-- GIN index for JSONB queries
CREATE INDEX idx_events_payload ON events USING GIN (payload);
```

### Full Text Search
```sql
-- tsvector and tsquery
SELECT to_tsvector('english', 'Python is great for web development');
-- 'develop':6 'great':3 'python':1 'web':5

SELECT to_tsquery('english', 'python & web');
-- 'python' & 'web'

-- Search
SELECT title, body
FROM articles
WHERE to_tsvector('english', title || ' ' || body) @@ to_tsquery('english', 'python & machine:*');

-- Materialized tsvector column (better performance)
ALTER TABLE articles ADD COLUMN search_vector tsvector;
UPDATE articles SET search_vector = to_tsvector('english', title || ' ' || body);
CREATE INDEX idx_articles_fts ON articles USING GIN (search_vector);

CREATE TRIGGER articles_search_update
BEFORE INSERT OR UPDATE ON articles
FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(search_vector, 'pg_catalog.english', title, body);

-- Search with ranking
SELECT title, ts_rank(search_vector, query) AS rank
FROM articles, to_tsquery('english', 'database & optimization') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 10;
```

### pg_stat — Monitoring
```sql
-- Long running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state = 'active';

-- Table statistics
SELECT schemaname, tablename, n_live_tup, n_dead_tup,
       last_vacuum, last_autovacuum, last_analyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- Index hit rates (should be > 99%)
SELECT
    schemaname, tablename,
    ROUND(heap_blks_hit * 100.0 / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) AS cache_hit_ratio
FROM pg_statio_user_tables
ORDER BY cache_hit_ratio ASC;

-- Active locks
SELECT pid, relation::regclass, mode, granted
FROM pg_locks
WHERE NOT granted;

-- Kill stuck query
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE query LIKE '%expensive_table%'
  AND state = 'active'
  AND query_start < NOW() - INTERVAL '10 minutes';
```

## SQLAlchemy ORM

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func, Index
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker, mapped_column, Mapped
from sqlalchemy.sql import select, update, delete
from typing import Optional
from datetime import datetime

# Modern SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")
    
    __table_args__ = (
        Index("ix_users_email_lower", func.lower(email)),
    )

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    author: Mapped["User"] = relationship("User", back_populates="posts")

# Queries
with Session(engine) as session:
    # SELECT
    users = session.execute(select(User).where(User.active == True)).scalars().all()
    
    # JOIN
    stmt = (
        select(User, Post)
        .join(Post, Post.author_id == User.id)
        .where(Post.published == True)
        .order_by(Post.id.desc())
        .limit(20)
    )
    results = session.execute(stmt).all()
    
    # Eager loading (avoids N+1 queries)
    from sqlalchemy.orm import selectinload, joinedload
    users_with_posts = session.execute(
        select(User).options(selectinload(User.posts))
    ).scalars().all()
    
    # INSERT
    new_user = User(name="Fahmi", email="f@sidix.ai")
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # UPDATE
    session.execute(
        update(User).where(User.id == 1).values(active=False)
    )
    session.commit()
    
    # DELETE
    session.execute(delete(Post).where(Post.author_id == 1))
    session.commit()
```

## NoSQL Overview

### MongoDB Use Cases
```javascript
// Best for: flexible/evolving schema, document-oriented data, hierarchical data
// Database: MongoDB, Mongoose (Node.js ODM)

// Document structure (no rigid schema)
{
  "_id": ObjectId("..."),
  "user": { "id": 42, "name": "Fahmi" },
  "items": [
    { "product_id": 7, "qty": 2, "price": 29.99 },
    { "product_id": 8, "qty": 1, "price": 49.99 }
  ],
  "status": "completed",
  "metadata": { "source": "mobile", "referral": "email" },
  "created_at": ISODate("2024-01-15T10:30:00Z")
}

// Queries
db.orders.find({ "user.id": 42, status: "completed" })
db.orders.find({ "items.product_id": 7 })
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$user.id", total: { $sum: "$total" } } },
  { $sort: { total: -1 } }
])
```

### Redis Use Cases
```python
# Key-Value store with data structures and expiry
import redis
r = redis.Redis()

# 1. Caching — most common
r.setex("user:42", 3600, json.dumps(user_data))

# 2. Session storage
r.hset("session:abc123", mapping={"user_id": 42, "role": "admin"})
r.expire("session:abc123", 1800)

# 3. Rate limiting (fixed window)
def check_rate_limit(key: str, limit: int, window: int) -> bool:
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count <= limit

# 4. Distributed lock
lock = r.set("lock:payment:42", "1", nx=True, ex=30)  # nx=only if not exists
if lock:
    try:
        process_payment(42)
    finally:
        r.delete("lock:payment:42")

# 5. Pub/Sub for real-time events
# 6. Sorted sets for leaderboards
# 7. Streams for event queues (Redis Streams)
# 8. Bloom filter for duplicate detection (RedisBloom module)
```

## Database Migration Best Practices

```bash
# Alembic — SQLAlchemy migrations
pip install alembic

alembic init alembic              # initialize migration directory
alembic revision --autogenerate -m "add_user_table"  # auto-detect changes
alembic upgrade head              # apply all pending migrations
alembic downgrade -1              # rollback last migration
alembic history                   # show migration history

# Rules for safe migrations in production:
# 1. Never DROP column directly — make it nullable first, deploy, then drop
# 2. Never rename column directly — add new column, backfill, deploy, drop old
# 3. Large table migrations: use concurrent index creation
#    CREATE INDEX CONCURRENTLY idx_users_email ON users (email);
# 4. Always test rollback (alembic downgrade)
# 5. Migrations should be idempotent when possible
```

## Referensi & Sumber Lanjut
- https://www.postgresql.org/docs/current/
- https://use-the-index-luke.com/ — SQL indexing best practices
- https://docs.sqlalchemy.org/en/20/
- https://alembic.sqlalchemy.org/
- https://www.mongodb.com/docs/
- https://redis.io/docs/
- roadmap.sh/postgresql-dba
- roadmap.sh/mongodb
