# Stage 6: SOLID Principles Mapping to Code Architecture

## 1. Concrete Mapping of SOLID Principles in SALESTORM

| Principle | Architectural Application in SALESTORM | Component Implementation Example |
| :--- | :--- | :--- |
| **SRP** *(Single Responsibility Principle)* | Each microservice and class has one single, well-defined business reason to change. | **PaymentService** is strictly responsible for payment authorization and idempotency; it delegates stock updates to **InventoryService** and order state to **OrderService**. |
| **OCP** *(Open/Closed Principle)* | Core execution pipelines are open for extension but closed for modification. | **PaymentGatewayFactory** allows adding new payment providers (e.g. ApplePay, Crypto) by implementing `PaymentGatewayStrategy` interface without altering checkout flow logic. |
| **LSP** *(Liskov Substitution Principle)* | Derived strategy implementations can be substituted seamlessly without breaking calling contracts. | `StripePaymentAdapter` and `PayPalPaymentAdapter` both honor `PaymentGatewayStrategy.processPayment()`, throwing consistent domain exceptions (`GatewayTimeoutException`, `InsufficientFundsException`). |
| **ISP** *(Interface Segregation Principle)* | Fine-grained, role-tailored interfaces instead of bloated monolithic contracts. | Split interfaces: `InventoryReadRepository` (for catalog browsing), `InventoryWriteRepository` (for atomic locks), and `InventoryExpiryListener` (for TTL callbacks). |
| **DIP** *(Dependency Inversion Principle)* | High-level business orchestrators depend on abstractions rather than low-level concrete infrastructure modules. | **OrderService** depends on `EventPublisher` interface, not concrete `KafkaEventPublisher`. Facilitates unit testing with `MockEventPublisher`. |

---

## 2. Refactoring Comparison: Violation vs SOLID Compliant

### Bad Code (Violating SRP & OCP):
```java
// Monolithic fat method that mixes Payment, Stock, DB and Notification logic
public void checkout(User user, Cart cart) {
    if (cart.item.stock > 0) {
        cart.item.stock--;
        // Hardcoded Stripe API call
        Stripe.charge(user.card, cart.total);
        // Direct DB Insert
        db.execute("INSERT INTO orders...");
        // Direct SendGrid Email Call
        SendGrid.sendEmail(user.email, "Order confirmed!");
    }
}
```

### Clean SOLID Code (SALESTORM Architecture):
```java
public class CheckoutFacade {
    private final InventoryReservationService reservationService;
    private final PaymentProcessor paymentProcessor;
    private final EventPublisher eventPublisher;

    public CheckoutResult processCheckout(CheckoutCommand cmd) {
        Reservation res = reservationService.reserve(cmd.toReservationCmd());
        PaymentResult payResult = paymentProcessor.execute(cmd.toPaymentCmd(res.getId()));
        eventPublisher.publish(new PaymentSucceededEvent(payResult));
        return CheckoutResult.success(res, payResult);
    }
}
```
