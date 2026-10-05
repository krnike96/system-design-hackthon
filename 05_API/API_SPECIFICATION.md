# Stage 7: OpenAPI 3.0 API Specification & Messaging Contracts

## 1. RESTful OpenAPI Contracts

### 1.1 Reserve Inventory Endpoint (`POST /api/v1/reservations`)

- **Method:** `POST`
- **Path:** `/api/v1/reservations`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <jwt_token>`
  - `X-Idempotency-Key: <uuid_v4>` *(Mandatory)*

#### Request Body
```json
{
  "productId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "quantity": 1
}
```

#### Successful Response (`201 Created`)
```json
{
  "status": "SUCCESS",
  "data": {
    "reservationId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "productId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "quantity": 1,
    "status": "RESERVED",
    "expiresAt": "2026-10-05T10:45:00Z",
    "idempotencyKey": "req_key_10029384"
  }
}
```

#### Out of Stock Response (`409 Conflict`)
```json
{
  "status": "ERROR",
  "code": "OUT_OF_STOCK",
  "message": "The requested product is out of stock."
}
```

---

### 1.2 Process Payment Endpoint (`POST /api/v1/payments`)

- **Method:** `POST`
- **Path:** `/api/v1/payments`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <jwt_token>`
  - `X-Idempotency-Key: <uuid_v4>` *(Mandatory)*

#### Request Body
```json
{
  "reservationId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "amount": 499.99,
  "paymentMethod": "CREDIT_CARD",
  "paymentToken": "tok_visa_flash_sale"
}
```

#### Successful Response (`200 OK`)
```json
{
  "status": "SUCCESS",
  "data": {
    "paymentId": "pay_9988776655",
    "reservationId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "status": "SUCCESS",
    "transactionRef": "ch_stripe_99221100",
    "amount": 499.99,
    "timestamp": "2026-10-05T10:36:12Z"
  }
}
```

---

## 2. Asynchronous Domain Event Schemas (Kafka Topics)

### Topic: `salestorm.payment.events`

#### Event Type: `PaymentSucceededEvent`
```json
{
  "eventId": "evt_1122334455",
  "eventType": "PaymentSucceeded",
  "timestamp": "2026-10-05T10:36:12Z",
  "payload": {
    "paymentId": "pay_9988776655",
    "reservationId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "customerId": "usr_44556677",
    "productId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "amount": 499.99,
    "transactionRef": "ch_stripe_99221100"
  }
}
```

#### Event Type: `PaymentFailedEvent`
```json
{
  "eventId": "evt_9988776611",
  "eventType": "PaymentFailed",
  "timestamp": "2026-10-05T10:36:15Z",
  "payload": {
    "paymentId": "pay_00112233",
    "reservationId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "reason": "INSUFFICIENT_FUNDS"
  }
}
```
