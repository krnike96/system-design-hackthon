# High-Level Architecture (HLD) & System Boundaries

## 1. Complete High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph Edge Layer ["Edge & Security Layer"]
        CDN["Cloudflare CDN / WAF\n(DDoS Protection & Static Asset Caching)"]
        LB["NGINX Ingress Load Balancer\n(Layer 7 Load Balancing & TLS Termination)"]
    end

    subgraph Gateway Layer ["API Gateway Layer"]
        GW["Kong / Spring Cloud API Gateway\n(Rate Limiting, JWT Auth, Idempotency Extraction)"]
    end

    subgraph Service Mesh ["Microservices Domain"]
        CatalogSvc["Catalog Service\n(Product Discovery & Read Replica Caching)"]
        CartSvc["Cart Service\n(Shopping Cart State)"]
        InvSvc["Inventory Service\n(Concurreny Control & Reservation)"]
        PaySvc["Payment Service\n(Idempotency & Gateway Adapter)"]
        OrderSvc["Order Service\n(Lifecycle & Saga Orchestration)"]
        ShipSvc["Fulfillment Service\n(Dispatch & Delivery Tracking)"]
        NotifSvc["Notification Service\n(Customer Alerts)"]
    end

    subgraph Storage Layer ["Data & Caching Infrastructure"]
        RedisCluster["Redis Cluster\n(Atomic Decr, Lua Scripts & Locks)"]
        PrimaryDB[(PostgreSQL Main DB Cluster\nMaster-Replica with Outbox Pattern)]
        KafkaBus[["Apache Kafka Event Bus\n(Distributed Log & Replay Stream)"]]
    end

    subgraph External ["External Services"]
        PayGW["3rd-Party Payment Gateway"]
        LogisticsPartner["Logistics Partner API"]
    end

    %% Flow Connections
    CDN --> LB
    LB --> GW
    GW --> CatalogSvc
    GW --> CartSvc
    GW --> InvSvc
    GW --> PaySvc
    GW --> OrderSvc

    InvSvc <-->|Atomic Lua / DECR| RedisCluster
    InvSvc -->|Persist Reservation| PrimaryDB
    InvSvc -->|Emit Reservation Event| KafkaBus

    PaySvc <-->|Check/Lock Key| RedisCluster
    PaySvc -->|Process Payment| PayGW
    PaySvc -->|Emit Payment Event| KafkaBus
    PaySvc -->|Write Outbox| PrimaryDB

    KafkaBus -->|Consume Payment Succeeded| OrderSvc
    KafkaBus -->|Consume Order Created| ShipSvc
    KafkaBus -->|Consume Order/Payment Events| NotifSvc

    OrderSvc -->|Write Order State| PrimaryDB
    ShipSvc -->|Dispatch| LogisticsPartner
```

---

## 2. Component Responsibility & Justification

| Component | Responsibility | Why it Exists & Trade-off |
| :--- | :--- | :--- |
| **Cloudflare CDN / WAF** | Absorbs invalid bot traffic, static image assets, and DDoS attempts. | **Why:** Protects internal load balancers from traffic saturation.<br>**Trade-off:** Adds minor latency for uncached dynamic requests. |
| **API Gateway** | Single entry point for routing, authentication, rate limiting, and extracting `X-Idempotency-Key`. | **Why:** Centralizes cross-cutting concerns.<br>**Trade-off:** Potential single point of failure if not scaled horizontally. |
| **Redis Cluster (L1 Stock)** | Manages atomic in-memory stock decrementing and reservation TTLs via Lua scripts. | **Why:** Can execute 100,000+ ops/sec per shard in sub-millisecond time. Protects relational DB from 10k concurrent lock requests.<br>**Trade-off:** Memory volatility requiring DB Write-Ahead persistence. |
| **PostgreSQL Main DB** | System of record for Orders, Payments, and Inventory snapshot durability. Uses ACID transactions and Outbox table. | **Why:** Ensures strict data durability, compliance, and relational queries.<br>**Trade-off:** Lower write throughput compared to in-memory caches. |
| **Apache Kafka Event Bus** | Asynchronous event backbone for decoupled communication (`ReservationCreated`, `PaymentSucceeded`, `OrderCreated`). | **Why:** Decouples Order Service from Payment Service. If Order Service is down for 30s, Kafka buffers events without data loss.<br>**Trade-off:** Eventual consistency complexity. |

---

## 3. Communication Patterns

```mermaid
matrix
    title Communication Pattern Matrix
```

- **Synchronous (REST/gRPC):**
  - Gateway $\rightarrow$ Inventory Service (User waiting for immediate reservation confirmation).
  - Payment Service $\rightarrow$ External Payment Gateway (Real-time card authorization).
- **Asynchronous (Event-Driven via Kafka):**
  - Payment Service $\rightarrow$ Order Service (Order creation after payment success).
  - Order Service $\rightarrow$ Fulfillment Service.
  - All Services $\rightarrow$ Notification Service.
