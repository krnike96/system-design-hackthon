# Stage 2: Component Diagram (C4 Level 3 - Critical Services)

## 1. Inventory Service Internal Component Diagram

```mermaid
flowchart TD
    subgraph InvBoundary["Inventory Service Boundary"]
        InvController["Reservation Controller\n(REST/gRPC Endpoint)"]
        RateLimiter["Token Bucket Rate Limiter\n(In-Memory Traffic Filter)"]
        ResManager["Reservation Manager\n(Domain Core Service)"]
        LuaExecutor["Redis Lua Engine\n(Data Access Client)"]
        OutboxWriter["Transactional Outbox Writer\n(Persistence Module)"]
        ExpiryScheduler["Delay Queue Expiry Monitor\n(Background Worker)"]
    end

    Redis[("Redis Cluster\n(In-Memory)")]
    PG[("PostgreSQL DB\n(Relational Storage)")]
    Kafka[["Kafka Broker\n(Event Stream)"]]

    InvController -->|"Delegates request"| RateLimiter
    RateLimiter -->|"Passes allowed requests"| ResManager
    ResManager -->|"Executes atomic reserve script"| LuaExecutor
    LuaExecutor -->|"Atomic DECRBY & TTL Set"| Redis
    ResManager -->|"Saves reservation record"| OutboxWriter
    OutboxWriter -->|"INSERT INTO reservations & outbox"| PG
    ExpiryScheduler -->|"Releases stock on TTL expiration"| LuaExecutor
    OutboxWriter -->|"Publishes events"| Kafka
```

---

## 2. Payment Service Component Diagram

```mermaid
flowchart TD
    subgraph PayBoundary["Payment Service Boundary"]
        PayController["Payment API Controller\n(REST Endpoint)"]
        IdempotencyGuard["Idempotency Manager\n(Redis Distributed Lock)"]
        PayProcessor["Payment Processor Engine\n(Core Orchestrator)"]
        GWFactory["Payment Gateway Factory\n(Strategy / Adapter Pattern)"]
        CBGuard["Circuit Breaker Guard\n(Resilience4j Guard)"]
        PayRepo["Payment Repository\n(DAO Layer)"]
    end

    RedisLock[("Redis Lock Manager\n(In-Memory)")]
    Stripe["💳 External Stripe API\n(3rd-Party Gateway)"]
    Postgres[("PostgreSQL Database\n(Relational Storage)")]

    PayController -->|"Validates idempotency_key"| IdempotencyGuard
    IdempotencyGuard -->|"Acquires lock SET key EX NX"| RedisLock
    IdempotencyGuard -->|"Proceeds if lock acquired"| PayProcessor
    PayProcessor -->|"Gets adapter instance"| GWFactory
    GWFactory -->|"Calls gateway via circuit breaker"| CBGuard
    CBGuard -->|"Executes HTTPS Authorization"| Stripe
    PayProcessor -->|"Saves transaction result"| PayRepo
    PayRepo -->|"INSERT INTO payments"| Postgres
```
