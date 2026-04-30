# System Design Roadmap — Topic Index

> Sumber: roadmap.sh/system-design (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/system-design

## Introduction
- What is System Design?
- How to approach System Design?
- Performance vs Scalability
- Latency vs Throughput
- Availability vs Consistency

## CAP Theorem
- CAP Theorem
- AP — Availability + Partition Tolerance
- CP — Consistency + Partition Tolerance

## Consistency Patterns
- Weak Consistency
- Eventual Consistency
- Strong Consistency

## Availability Patterns
- Fail-Over: Active-Active, Active-Passive
- Replication: Master-Slave, Master-Master
- Availability Numbers: 99.9% (three 9s), 99.99% (four 9s)
- Availability in Parallel vs Sequence
- Background Jobs: Event-Driven, Schedule-Driven

## DNS & CDN
- Domain Name System (DNS)
- Content Delivery Networks (CDN): Push CDN vs Pull CDN

## Load Balancing
- Load Balancers vs Reverse Proxy
- Load Balancing Algorithms
- Layer 7 (Application) Load Balancing
- Layer 4 (Transport) Load Balancing
- Horizontal Scaling

## Application Layer
- Microservices
- Service Discovery

## Databases
- SQL vs NoSQL
- Replication
- Sharding / Federation / Denormalization
- SQL Tuning
- Types: RDBMS, Key-Value Store, Document Store, Wide Column Store, Graph Databases

## Caching
- Cache Strategies: Cache-Aside, Write-through, Write-behind, Refresh-Ahead
- Cache Layers: Client, CDN, Web Server, Database, Application
- Types of Caching
- Idempotent Operations

## Asynchronism
- Back Pressure
- Task Queues / Message Queues

## Communication Protocols
- HTTP, TCP, UDP
- RPC, REST, gRPC, GraphQL

## Performance Anti-patterns
- Busy Database, Busy Frontend
- Chatty I/O, Extraneous Fetching
- Monolithic Persistence, No Caching
- Noisy Neighbor, Retry Storm, Synchronous I/O

## Monitoring
- Health Monitoring, Availability Monitoring
- Performance Monitoring, Security Monitoring
- Instrumentation, Visualization & Alerts

## Cloud Design Patterns

### Messaging Patterns
- Sequential Convoy, Scheduling Agent Supervisor
- Queue-Based Load Leveling
- Publisher/Subscriber, Priority Queue
- Pipes and Filters, Competing Consumers
- Choreography, Claim Check, Async Request Reply

### Data Management
- Valet Key, Static Content Hosting
- Sharding, Materialized View, Index Table
- Event Sourcing, CQRS, Cache-Aside

### Design & Implementation
- Strangler Fig, Sidecar, Pipes & Filters
- Leader Election, Gateway Routing/Offloading/Aggregation
- External Config Store, Compute Resource Consolidation
- Backends for Frontend, Anti-Corruption Layer, Ambassador

### Reliability Patterns
- Deployment Stamps, Geodesy
- Health Endpoint Monitoring, Throttling
- Bulkhead, Circuit Breaker
- Compensating Transaction, Retry, Scheduler Agent Supervisor

## Key Concepts Summary

| Concept | Use Case |
|---|---|
| Horizontal Scaling | Add more servers; no single point of failure |
| Vertical Scaling | Bigger server; simpler but has limits |
| Load Balancer | Distributes traffic; health checks; SSL termination |
| Cache | Reduce DB load; TTL; invalidation strategy matters |
| CDN | Serve static assets from edge; reduce latency |
| Message Queue | Decouple services; async processing; retry |
| Sharding | Partition data across DBs; avoid hotspot keys |
| Replication | High availability; read replicas; eventual consistency |
| Circuit Breaker | Fail fast; prevent cascade failures |
| Rate Limiting | Token bucket, Leaky bucket, Fixed window, Sliding window |

## Referensi Lanjut
- https://roadmap.sh/system-design
- https://github.com/donnemartin/system-design-primer
- https://aws.amazon.com/architecture/
