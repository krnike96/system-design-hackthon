# Order Creation, Resilience & Recovery Sequence Diagram

## 1. Async Order Creation & Outage Recovery (30s Order Service Outage Handling)

This diagram details the transactional outbox pattern and Kafka buffering mechanism when the Order Service is temporarily unavailable for 30 seconds after payment success.

```mermaid
sequenceDiagram
    autonumber
    participant PaySvc as "Payment Service"
    participant DB as "PostgreSQL DB"
    participant OutboxWorker as "Outbox Relay Service"
    participant Kafka as "Kafka Event Bus"
    participant OrderSvc as "Order Service"
    participant ReconWorker as "Reconciliation Worker"

    Note over PaySvc, DB: Payment succeeds in Payment Service
    PaySvc->>DB: BEGIN TRANSACTION<br/>UPDATE payment SET status='SUCCESS'<br/>INSERT INTO outbox_events (event_type, payload)<br/>COMMIT
    DB-->>PaySvc: Transaction Committed

    OutboxWorker->>DB: SELECT * FROM outbox_events WHERE processed = false
    OutboxWorker->>Kafka: Publish PaymentSucceededEvent (partitioned by userId)
    OutboxWorker->>DB: UPDATE outbox_events SET processed = true

    Note over OrderSvc: Order Service is CRASHED / UNREACHABLE (t = 0s to t = 30s)
    Kafka--xOrderSvc: Event waiting in Kafka partition log offset 1042

    Note over Kafka: Kafka buffers message reliably in persistent disk log!

    Note over OrderSvc: Order Service RECOVERS & RESTARTS at t = 31s!
    OrderSvc->>Kafka: Connect & Resume Polling from Consumer Group Offset 1042
    Kafka-->>OrderSvc: Deliver PaymentSucceededEvent

    OrderSvc->>DB: BEGIN TRANSACTION<br/>INSERT INTO orders (id, user_id, status='CONFIRMED')<br/>INSERT INTO order_items (...)<br/>UPDATE inventory SET sold_quantity = sold_quantity + 1<br/>COMMIT
    DB-->>OrderSvc: Order Saved Successfully!

    OrderSvc->>Kafka: Commit Consumer Offset 1043 & Publish OrderConfirmedEvent

    opt Edge Case: If Kafka Event Fails Processing 5 times
        OrderSvc->>Kafka: Send payload to Dead-Letter Queue (DLQ: order-events-dlq)
        ReconWorker->>Kafka: Poll DLQ & Trigger Alert for Manual/Automated Compensation
    end
```
