# Stage 3 & 4: Database ER Diagram & Concurrency Schema Design

## 1. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    CUSTOMER ||--o{ INVENTORY_RESERVATION : "places"
    CUSTOMER ||--o{ ORDER : "owns"
    PRODUCT ||--|| INVENTORY : "has"
    PRODUCT ||--o{ INVENTORY_RESERVATION : "reserved in"
    INVENTORY_RESERVATION ||--o| PAYMENT : "initiates"
    PAYMENT ||--o| ORDER : "fulfills"
    ORDER ||--|{ ORDER_ITEM : "contains"
    PRODUCT ||--o{ ORDER_ITEM : "ordered as"
    ORDER ||--o| SHIPMENT : "dispatched via"
    ORDER ||--o{ NOTIFICATION : "triggers"

    CUSTOMER {
        uuid customer_id PK
        string email UK
        string name
        string phone
        timestamp created_at
    }

    PRODUCT {
        uuid product_id PK
        string title
        decimal price
        string sku UK
        boolean is_flash_sale
    }

    INVENTORY {
        uuid inventory_id PK
        uuid product_id FK, UK
        int available_quantity
        int reserved_quantity
        int sold_quantity
        bigint version
        timestamp updated_at
    }

    INVENTORY_RESERVATION {
        uuid reservation_id PK
        uuid customer_id FK
        uuid product_id FK
        int quantity
        string status
        string idempotency_key UK
        timestamp expires_at
        timestamp created_at
    }

    PAYMENT {
        uuid payment_id PK
        uuid reservation_id FK
        uuid customer_id FK
        decimal amount
        string status
        string idempotency_key UK
        string transaction_ref UK
        timestamp created_at
    }

    ORDER {
        uuid order_id PK
        uuid customer_id FK
        uuid reservation_id FK
        uuid payment_id FK
        decimal total_amount
        string status
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEM {
        uuid order_item_id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price
    }

    SHIPMENT {
        uuid shipment_id PK
        uuid order_id FK
        string tracking_number
        string carrier
        string status
        timestamp dispatched_at
    }

    NOTIFICATION {
        uuid notification_id PK
        uuid customer_id FK
        string type
        string message
        timestamp sent_at
    }
```

---

## 2. DDL SQL Schema (PostgreSQL with Concurrency & Index Optimization)

```sql
-- 1. Inventory Table with Concurrency Versioning and Non-Negative Constraint
CREATE TABLE inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL UNIQUE REFERENCES product(product_id),
    available_quantity INT NOT NULL CHECK (available_quantity >= 0),
    reserved_quantity INT NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    sold_quantity INT NOT NULL DEFAULT 0 CHECK (sold_quantity >= 0),
    version BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for instant lookup during flash sale
CREATE INDEX idx_inventory_product ON inventory(product_id);

-- 2. Inventory Reservation Table with Idempotency & Expiry Indexing
CREATE TABLE inventory_reservation (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    product_id UUID NOT NULL REFERENCES product(product_id),
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    status VARCHAR(30) NOT NULL DEFAULT 'RESERVED', -- RESERVED, PAYMENT_PENDING, CONFIRMED, RELEASED
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for background reconciliation of expired reservations
CREATE INDEX idx_reservation_expiry ON inventory_reservation(status, expires_at) 
WHERE status = 'RESERVED';

-- 3. Payment Table with Idempotency Key & Provider Transaction Reference
CREATE TABLE payment (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reservation_id UUID NOT NULL REFERENCES inventory_reservation(reservation_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(30) NOT NULL, -- INITIATED, SUCCESS, FAILED, TIMED_OUT
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    transaction_ref VARCHAR(128) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payment_idempotency ON payment(idempotency_key);

-- 4. Transactional Outbox Table for Async Event Reliability
CREATE TABLE outbox_event (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_outbox_unprocessed ON outbox_event(created_at) WHERE processed = FALSE;
```
