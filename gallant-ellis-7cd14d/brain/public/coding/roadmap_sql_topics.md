# SQL Roadmap — Topics & Quick Reference

> Sumber: roadmap.sh/sql (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/sql

## Foundations
- Relational Databases: RDBMS benefits and limitations
- SQL vs NoSQL Databases
- PostgreSQL basics

## Basic SQL Syntax
- SQL Keywords, Data Types, Operators
- SELECT, INSERT, UPDATE, DELETE statements

## Data Definition Language (DDL)
- CREATE TABLE, ALTER TABLE, DROP TABLE, TRUNCATE TABLE

## Data Manipulation Language (DML)
- SELECT ... FROM ... WHERE ... ORDER BY ... GROUP BY ... HAVING
- INSERT, UPDATE, DELETE

## Aggregate Queries
- SUM, COUNT, AVG, MIN, MAX
- GROUP BY, HAVING

## Data Constraints
- PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK

## JOIN Queries

```sql
-- INNER JOIN: only matching rows in both tables
SELECT a.name, b.order_date
FROM customers a
INNER JOIN orders b ON a.id = b.customer_id;

-- LEFT JOIN: all rows from left, matched from right
SELECT a.name, b.order_date
FROM customers a
LEFT JOIN orders b ON a.id = b.customer_id;

-- RIGHT JOIN: all rows from right
-- FULL OUTER JOIN: all rows from both
-- SELF JOIN: join table with itself
-- CROSS JOIN: cartesian product
```

## Subqueries
- Scalar (returns single value), Column, Row, Table subqueries
- Nested Subqueries, Correlated Subqueries

## Advanced Functions

### Numeric
- FLOOR, ABS, MOD, ROUND, CEILING

### String
- CONCAT, LENGTH, SUBSTRING, REPLACE, UPPER, LOWER

### Conditional
- CASE ... WHEN ... THEN ... END
- NULLIF, COALESCE

### Date & Time
- DATE, TIME, TIMESTAMP
- DATEPART, DATEADD

## Views
- Creating Views: `CREATE VIEW v AS SELECT ...`
- Modifying Views: `CREATE OR REPLACE VIEW`
- Dropping Views: `DROP VIEW v`

## Indexes

```sql
-- Create index
CREATE INDEX idx_name ON table(column);

-- Composite index
CREATE INDEX idx_name ON table(col1, col2);

-- Partial index (PostgreSQL)
CREATE INDEX idx_active ON users(email) WHERE active = true;

-- Check index usage in PostgreSQL
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'a@b.com';
```

## Transactions

```sql
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;  -- or ROLLBACK if error

-- Savepoints
SAVEPOINT sp1;
ROLLBACK TO SAVEPOINT sp1;
```

## ACID Properties
- **Atomicity**: all or nothing
- **Consistency**: valid state before and after
- **Isolation**: concurrent transactions don't interfere
- **Durability**: committed data persists

## Transaction Isolation Levels (least → most isolated)
| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| Read Uncommitted | Yes | Yes | Yes |
| Read Committed | No | Yes | Yes |
| Repeatable Read | No | No | Yes |
| Serializable | No | No | No |

## Security
- Data Integrity Constraints
- GRANT and REVOKE permissions
- DB Security Best Practices (least privilege, parameterized queries)

## Stored Procedures & Functions

```sql
-- PostgreSQL function
CREATE OR REPLACE FUNCTION get_user_count() RETURNS INT AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM users);
END;
$$ LANGUAGE plpgsql;
```

## Performance Optimization
- Using Indexes (B-tree default in PostgreSQL)
- Optimizing JOINs (index on JOIN columns)
- Reducing Subqueries (prefer JOINs or CTEs)
- Selective Projection (SELECT only needed columns)
- Query Analysis: `EXPLAIN`, `EXPLAIN ANALYZE`

## Advanced SQL

### Common Table Expressions (CTEs)
```sql
WITH active_users AS (
    SELECT id, name FROM users WHERE active = true
),
user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders GROUP BY user_id
)
SELECT u.name, o.order_count
FROM active_users u
JOIN user_orders o ON u.id = o.user_id;
```

### Recursive CTEs
```sql
WITH RECURSIVE org_chart AS (
    SELECT id, name, manager_id, 0 as level
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY level;
```

### Window Functions
```sql
SELECT
    name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank_in_dept,
    RANK() OVER (ORDER BY salary DESC) as overall_rank,
    LAG(salary) OVER (ORDER BY hire_date) as prev_salary,
    LEAD(salary) OVER (ORDER BY hire_date) as next_salary,
    SUM(salary) OVER (PARTITION BY department) as dept_total
FROM employees;
```

### Pivot (PostgreSQL)
```sql
-- Using CROSSTAB from tablefunc extension
SELECT * FROM crosstab(
    'SELECT category, month, revenue FROM sales ORDER BY 1,2'
) AS ct(category TEXT, jan NUMERIC, feb NUMERIC, mar NUMERIC);
```

## Referensi Lanjut
- https://roadmap.sh/sql
- https://roadmap.sh/postgresql-dba
- https://www.postgresql.org/docs/current/
- https://mode.com/sql-tutorial/
- PostgreSQL specifics: JSONB, full-text search, pg_stat_statements
