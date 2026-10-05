# Purchase & Inventory Reservation Sequence Diagram

## 1. High-Concurrency Purchase & Reservation Workflow

This sequence traces what happens when a customer clicks **"Buy Now"** during the flash sale, demonstrating L1 Redis Lua execution, protection against overselling, and creation of a 10-minute inventory reservation.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant GW as "API Gateway"
    participant InvSvc as "Inventory Service"
    participant Redis as "Redis Cluster (L1 Cache)"
    participant DB as "PostgreSQL DB (L2 DB)"
    participant DelayQ as "Kafka / Redis Expiry Queue"

    Customer->>GW: POST /api/v1/reservations (productId, qty=1, idempotencyKey)
    GW->>GW: Validate JWT Token & Extract Idempotency Key
    GW->>InvSvc: ReserveInventoryRequest(productId, userId, idempotencyKey)

    alt Duplicate Request Detected in Redis
        InvSvc->>Redis: GET idempotency:reservation:{idempotencyKey}
        Redis-->>InvSvc: Existing reservationId
        InvSvc-->>GW: HTTP 200 OK (Return Existing Reservation)
        GW-->>Customer: Return Existing Reservation Details
    else New Request Processing
        InvSvc->>Redis: EVALSHA reserve_stock.lua (product_id, qty=1)
        
        alt Stock Available (Current Stock > 0)
            Redis-->>Redis: Decr stock counter & Store TTL key reservation:{resId} (600s)
            Redis-->>InvSvc: SUCCESS (Remaining Stock: 99)
            
            InvSvc->>DB: INSERT INTO inventory_reservations (id, product_id, user_id, status='RESERVED', expires_at=NOW()+10m)
            DB-->>InvSvc: DB Commit OK
            
            InvSvc->>DelayQ: Schedule ReservationExpiryEvent (reservationId, ttl=600s)
            
            InvSvc-->>GW: HTTP 201 Created (reservationId, expiresAt)
            GW-->>Customer: 201 Created (Reservation Confirmed, 10 min to pay)
        else Out of Stock (Stock == 0)
            Redis-->>InvSvc: OUT_OF_STOCK (Stock = 0)
            InvSvc-->>GW: HTTP 409 Conflict / Out of Stock
            GW-->>Customer: HTTP 409 (Sold Out! Please try again later.)
        end
    end
```

---

## 2. Low-Level Lua Script Logic (Executing inside Redis)
```lua
-- KEYS[1]: product_stock_key (e.g. "stock:product_101")
-- KEYS[2]: reservation_key (e.g. "reservation:uuid_xyz")
-- ARGV[1]: requested_quantity (e.g. 1)
-- ARGV[2]: ttl_seconds (e.g. 600)

local current_stock = tonumber(redis.call('GET', KEYS[1]) or '0')
local req_qty = tonumber(ARGV[1])

if current_stock >= req_qty then
    redis.call('DECRBY', KEYS[1], req_qty)
    redis.call('SETEX', KEYS[2], tonumber(ARGV[2]), "RESERVED")
    return {1, current_stock - req_qty} -- Success code 1
else
    return {0, current_stock} -- Failure code 0 (Out of Stock)
end
```
