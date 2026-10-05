# Stage 8 & 10: Architecture Decision Records (ADRs)

## ADR-001: L1 Redis In-Memory Counter vs Relational DB Row Locking for Flash Sale Inventory

- **Status:** Accepted
- **Context:** SALESTORM flash sale must process 10,000 concurrent purchase requests for 100 available units of Product X. RDBMS row-level pessimistic locking (`SELECT ... FOR UPDATE`) saturates connection pools and causes lock timeouts at high concurrency.
- **Decision:** We select **Redis Cluster with Single-Threaded Atomic Lua Scripts** as the primary (L1) inventory reservation engine, combined with **PostgreSQL Transactional Outbox** (L2) for durable record keeping.
- **Consequences & Trade-Offs:**
  - *Positive:* Ultra-fast sub-5ms response time; exact 100 reservations granted, 9,900 requests rejected instantly at edge; zero database lock contention.
  - *Negative:* Cache volatility requirement. Addressed by asynchronously writing reservation audit logs to PostgreSQL via background workers.

---

## ADR-002: Asynchronous Event-Driven Order Processing (Kafka) vs Synchronous REST

- **Status:** Accepted
- **Context:** Third-party payment gateways introduce variable latency (200ms–1500ms), and internal downstream services (e.g. Order Service) may undergo temporary outages (e.g. 30-second crash/deployment restart).
- **Decision:** We separate Payment execution from Order Creation using **Apache Kafka Event Bus with Transactional Outbox Pattern**.
- **Consequences & Trade-Offs:**
  - *Positive:* High fault isolation. If Order Service crashes for 30s, payment events are buffered in Kafka with zero lost orders. Once Order Service restarts, it catches up automatically.
  - *Negative:* Order creation is eventually consistent (typically 50ms–2000ms delay). The UI displays a "Processing Order" spinner to handle this transition gracefully.

---

## ADR-003: Redis Distributed Lock with TTL for Payment Idempotency

- **Status:** Accepted
- **Context:** Up to 2% of incoming user requests during flash sales are retries or duplicate network transmissions with the same `X-Idempotency-Key`.
- **Decision:** Enforce mandatory `X-Idempotency-Key` headers on all mutating endpoints. Payment Service acquires a Redis key lock (`SET lock:payment:{key} EX 30 NX`) prior to calling external payment gateways.
- **Consequences & Trade-Offs:**
  - *Positive:* Completely prevents double-charging customers and duplicate payment API submissions.
  - *Negative:* Requires client SDKs to generate robust UUIDv4 idempotency keys before API submission.
