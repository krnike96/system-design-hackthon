# Stage 5 & 6: Class Diagrams & Object-Oriented Domain Model

## 1. Core Domain Class Diagram (Inventory, Payment, Order Modules)

```mermaid
classDiagram
    class Inventory {
        +UUID inventoryId
        +UUID productId
        +int availableQuantity
        +int reservedQuantity
        +int soldQuantity
        +long version
        +Timestamp updatedAt
        +reserveStock(int qty) ReservationResult
        +confirmStock(UUID reservationId) void
        +releaseStock(UUID reservationId) void
    }

    class InventoryReservation {
        +UUID reservationId
        +UUID customerId
        +UUID productId
        +int quantity
        +ReservationStatus status
        +Timestamp createdAt
        +Timestamp expiresAt
        +String idempotencyKey
        +isExpired() boolean
        +markPaymentPending() void
        +markConfirmed() void
        +markReleased() void
    }

    class ReservationStatus {
        <<enumeration>>
        RESERVED
        PAYMENT_PENDING
        CONFIRMED
        EXPIRED
        RELEASED
    }

    class Payment {
        +UUID paymentId
        +UUID reservationId
        +UUID customerId
        +BigDecimal amount
        +PaymentStatus status
        +String idempotencyKey
        +String transactionRef
        +Timestamp createdAt
        +executePayment(PaymentGatewayStrategy strategy) PaymentResult
        +markSuccess(String txRef) void
        +markFailed(String reason) void
    }

    class PaymentStatus {
        <<enumeration>>
        INITIATED
        PENDING
        SUCCESS
        FAILED
        TIMED_OUT
    }

    class Order {
        +UUID orderId
        +UUID customerId
        +UUID reservationId
        +UUID paymentId
        +BigDecimal totalAmount
        +OrderStatus status
        +List~OrderItem~ items
        +Timestamp createdAt
        +Timestamp updatedAt
        +transitionTo(OrderStatus nextState) void
    }

    class OrderStatus {
        <<enumeration>>
        CREATED
        PAYMENT_PENDING
        CONFIRMED
        PROCESSING
        SHIPPED
        OUT_FOR_DELIVERY
        DELIVERED
        CANCELLED
    }

    class OrderItem {
        +UUID itemId
        +UUID productId
        +int quantity
        +BigDecimal price
    }

    Inventory "1" -- "0..*" InventoryReservation : manages
    InventoryReservation "1" -- "0..1" Payment : triggers
    Payment "1" -- "0..1" Order : confirms
    Order "1" *-- "1..*" OrderItem : contains
    InventoryReservation --> ReservationStatus
    Payment --> PaymentStatus
    Order --> OrderStatus
```

---

## 2. Design Pattern Class Hierarchy

### 2.1 Payment Gateway Adapter & Strategy Pattern

```mermaid
classDiagram
    class PaymentGatewayStrategy {
        <<interface>>
        +processPayment(PaymentRequest request) PaymentResponse
        +queryPaymentStatus(String txRef) PaymentStatus
    }

    class StripePaymentAdapter {
        -StripeClient stripeClient
        +processPayment(PaymentRequest request) PaymentResponse
        +queryPaymentStatus(String txRef) PaymentStatus
    }

    class PayPalPaymentAdapter {
        -PayPalSDK paypalSDK
        +processPayment(PaymentRequest request) PaymentResponse
        +queryPaymentStatus(String txRef) PaymentStatus
    }

    class MockPaymentAdapter {
        -double failureRate
        +processPayment(PaymentRequest request) PaymentResponse
        +queryPaymentStatus(String txRef) PaymentStatus
    }

    class PaymentGatewayFactory {
        +getStrategy(PaymentProvider provider) PaymentGatewayStrategy
    }

    PaymentGatewayStrategy <|.. StripePaymentAdapter
    PaymentGatewayStrategy <|.. PayPalPaymentAdapter
    PaymentGatewayStrategy <|.. MockPaymentAdapter
    PaymentGatewayFactory ..> PaymentGatewayStrategy : instantiates
```

---

### 2.2 Order State Machine (State Pattern)

```mermaid
classDiagram
    class OrderState {
        <<interface>>
        +confirmPayment(OrderContext context) void
        +startProcessing(OrderContext context) void
        +shipOrder(OrderContext context) void
        +cancelOrder(OrderContext context) void
    }

    class PendingPaymentState {
        +confirmPayment(OrderContext context) void
        +cancelOrder(OrderContext context) void
    }

    class ConfirmedState {
        +startProcessing(OrderContext context) void
        +cancelOrder(OrderContext context) void
    }

    class ProcessingState {
        +shipOrder(OrderContext context) void
    }

    class ShippedState {
        +deliverOrder(OrderContext context) void
    }

    class OrderContext {
        -OrderState currentState
        +setState(OrderState newState) void
        +confirmPayment() void
        +startProcessing() void
    }

    OrderState <|.. PendingPaymentState
    OrderState <|.. ConfirmedState
    OrderState <|.. ProcessingState
    OrderState <|.. ShippedState
    OrderContext o-- OrderState
```
