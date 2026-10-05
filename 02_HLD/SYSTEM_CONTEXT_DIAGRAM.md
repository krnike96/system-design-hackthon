# Stage 2: System Context Diagram (C4 Level 1)

## 1. Context Overview
The **SALESTORM System Context** illustrates the external actors, clients, core platform boundaries, and third-party integrations (Payment Gateways, Logistics Providers, Notification Channels).

```mermaid
flowchart TD
    Customer["👤 Customer\n(E-Commerce User)"]
    Admin["👤 Store Administrator\n(Operations & Admin)"]

    subgraph Platform["SALESTORM Platform (System Boundary)"]
        CoreSystem["SALESTORM Core System\n(High-Scale Flash-Sale Engine)"]
    end

    subgraph ExternalSystems["External Third-Party Services"]
        PayGW["💳 Payment Gateway\n(Stripe / PayPal API)"]
        Logistics["🚚 Logistics Partner API\n(FedEx / DHL Tracking)"]
        NotifGW["📱 Notification Gateway\n(Twilio SMS / SendGrid)"]
    end

    Customer -->|"Browse, Reserve & Pay (HTTPS)"| CoreSystem
    Admin -->|"Manage Flash Sales & Inventory (HTTPS)"| CoreSystem

    CoreSystem -->|"Authorizes & Captures Payments"| PayGW
    CoreSystem -->|"Dispatches Shipment Requests"| Logistics
    CoreSystem -->|"Sends SMS / Email Alerts"| NotifGW
```

## 2. Context Interaction Rationale
- **Customer $\rightarrow$ SALESTORM:** Encrypted HTTPS requests routed through global Anycast CDN/WAF.
- **SALESTORM $\rightarrow$ Payment Gateway:** Outbound REST calls with Circuit Breaker protection.
- **SALESTORM $\rightarrow$ Logistics / Notifications:** Asynchronous event-driven integration to avoid blocking payment checkout flow.
