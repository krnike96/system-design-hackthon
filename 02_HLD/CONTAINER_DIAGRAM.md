# Stage 2: Container Diagram (C4 Level 2)

## 1. Container Architecture Overview

```mermaid
C4Container
    title Container Diagram for SALESTORM Platform

    Person(customer, "Customer", "E-Commerce User")

    Container_Boundary(salestorm_boundary, "SALESTORM Boundary") {
        Container(spa, "Single Page App / Mobile", "React / React Native", "Client interface for browsing & purchasing.")
        Container(gw, "API Gateway", "Kong / Spring Cloud", "Authenticates, rate limits, routes REST/gRPC traffic.")
        Container(inv_svc, "Inventory Service", "Go / Java Spring Boot", "Handles inventory check, reservation lock, and stock updates.")
        Container(pay_svc, "Payment Service", "Node.js / Go", "Handles idempotency, gateway communication, and retry policy.")
        Container(order_svc, "Order Service", "Java Spring Boot", "Orchestrates order state machine and outbox events.")
        
        ContainerDb(redis, "Redis In-Memory Store", "Redis 7.x Cluster", "Holds atomic stock counters, reservation TTL keys, and idempotency locks.")
        ContainerDb(pg, "Relational Database", "PostgreSQL 16 Cluster", "Stores customers, catalog, transactional orders, payments, and outbox logs.")
        ContainerDb(kafka, "Message Broker", "Apache Kafka", "Handles distributed domain events across microservices.")
    }

    System_Ext(pay_gw, "Payment Gateway API", "Stripe API")

    Rel(customer, spa, "Interacts via", "HTTPS")
    Rel(spa, gw, "API Calls", "HTTPS / JSON")
    Rel(gw, inv_svc, "Reserves stock", "gRPC / HTTP2")
    Rel(gw, pay_svc, "Initiates payment", "gRPC / HTTP2")
    Rel(gw, order_svc, "Queries order status", "REST / JSON")

    Rel(inv_svc, redis, "Atomic Lua Decrement", "RESP")
    Rel(inv_svc, pg, "Persists reservations", "SQL / TLS")
    Rel(inv_svc, kafka, "Publishes ReservationEvents", "Kafka Protocol")

    Rel(pay_svc, redis, "Acquires Idempotency Locks", "RESP")
    Rel(pay_svc, pay_gw, "Authorizes Payment", "HTTPS / REST")
    Rel(pay_svc, kafka, "Publishes PaymentEvents", "Kafka Protocol")

    Rel(kafka, order_svc, "Consumes Payment Events", "Kafka Protocol")
    Rel(order_svc, pg, "Updates Order State", "SQL / TLS")
```

---

## 2. Service Responsibilities & Protocols
- **API Gateway:** Protocol translation (HTTPS REST $\rightarrow$ internal gRPC for ultra-low latency).
- **Inventory Service:** High-performance Go microservice managing Redis Lua scripts and DB sync workers.
- **Payment Service:** Resilient microservice executing Strategy Pattern for Payment Gateways and Circuit Breaker logic.
- **Order Service:** State machine manager handling transactional updates and background reconciliation.
