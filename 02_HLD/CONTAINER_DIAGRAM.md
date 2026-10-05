# Stage 2: Container Diagram (C4 Level 2)

## 1. Container Architecture Overview

```mermaid
flowchart TD
    Customer["👤 Customer\n(E-Commerce User)"]

    subgraph Boundary["SALESTORM Boundary"]
        SPA["Single Page App / Mobile\n(React / React Native)"]
        GW["API Gateway\n(Kong / Spring Cloud)"]
        InvSvc["Inventory Service\n(Go Microservices)"]
        PaySvc["Payment Service\n(Node.js / Go)"]
        OrderSvc["Order Service\n(Java Spring Boot)"]

        Redis[("Redis 7.x Cluster\n(Atomic Decr & Locks)")]
        PG[("PostgreSQL 16 Cluster\n(Transactional DB)")]
        Kafka[["Apache Kafka\n(Message Broker)"]]
    end

    PayGW["💳 Payment Gateway API\n(Stripe API)"]

    Customer -->|"Interacts via HTTPS"| SPA
    SPA -->|"API Calls (HTTPS / JSON)"| GW
    GW -->|"Reserves Stock (gRPC)"| InvSvc
    GW -->|"Initiates Payment (gRPC)"| PaySvc
    GW -->|"Queries Status (REST)"| OrderSvc

    InvSvc -->|"Atomic Lua DECRBY"| Redis
    InvSvc -->|"Persists Reservations"| PG
    InvSvc -->|"Publishes ReservationEvents"| Kafka

    PaySvc -->|"Acquires Idempotency Lock"| Redis
    PaySvc -->|"Authorizes Payment (HTTPS)"| PayGW
    PaySvc -->|"Publishes PaymentEvents"| Kafka

    Kafka -->|"Consumes Payment Events"| OrderSvc
    OrderSvc -->|"Updates Order State"| PG
```

---

## 2. Service Responsibilities & Protocols
- **API Gateway:** Protocol translation (HTTPS REST $\rightarrow$ internal gRPC for ultra-low latency).
- **Inventory Service:** High-performance Go microservice managing Redis Lua scripts and DB sync workers.
- **Payment Service:** Resilient microservice executing Strategy Pattern for Payment Gateways and Circuit Breaker logic.
- **Order Service:** State machine manager handling transactional updates and background reconciliation.
