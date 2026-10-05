# Stage 6: Design Patterns Mapping & Trade-Off Analysis

## 1. Applied Design Patterns Matrix

| Design Pattern | Category | Concrete SALESTORM Application | Problem Solved & Trade-Off Introduced |
| :--- | :--- | :--- | :--- |
| **Strategy Pattern** | Behavioral | `PaymentGatewayStrategy` with implementations (`StripeAdapter`, `PayPalAdapter`, `MockAdapter`). | **Problem Solved:** Decouples Payment Service from provider APIs.<br>**Trade-Off:** Small increase in class hierarchy complexity. |
| **Factory Pattern** | Creational | `PaymentGatewayFactory` instantiating provider adapters dynamically based on request header or geography. | **Problem Solved:** Centralizes creation logic and dependency injection.<br>**Trade-Off:** Dynamic lookup overhead. |
| **State Pattern** | Behavioral | `OrderState` managing transitions (`CREATED` $\rightarrow$ `CONFIRMED` $\rightarrow$ `SHIPPED`). | **Problem Solved:** Eliminates giant `if-else` / `switch` blocks; enforces valid state transitions.<br>**Trade-Off:** Requires separate state handler objects. |
| **Observer Pattern** | Behavioral | Kafka Event Bus subscriber model for `PaymentSucceededEvent`. | **Problem Solved:** Decouples payment execution from fulfillment and notifications.<br>**Trade-Off:** Eventual consistency window. |
| **Adapter Pattern** | Structural | Wrapping 3rd-party vendor SDKs to standard `PaymentResponse` domain DTOs. | **Problem Solved:** Shields domain model from external API breaking changes.<br>**Trade-Off:** Data conversion translation layer. |
| **Facade Pattern** | Structural | `CheckoutFacade` coordinating Reservation, Payment, and Event publishing. | **Problem Solved:** Simplifies API Gateway integration into a single entry point.<br>**Trade-Off:** Must avoid becoming a "God Class". |
| **Circuit Breaker** | Behavioral / Resilience | Resilience4j wrapping external Payment Gateway calls. | **Problem Solved:** Prevents thread pool starvation during 3rd party outage.<br>**Trade-Off:** Requires fallback configuration and monitoring. |
| **Outbox Pattern** | Architectural | `outbox_events` table written inside SQL transaction alongside reservation. | **Problem Solved:** Solves Dual-Write problem (DB + Kafka consistency).<br>**Trade-Off:** Requires background polling worker. |
