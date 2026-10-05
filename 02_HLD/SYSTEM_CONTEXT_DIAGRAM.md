# Stage 2: System Context Diagram (C4 Level 1)

## 1. Context Overview
The **SALESTORM System Context** illustrates the external actors, clients, core platform boundaries, and third-party integrations (Payment Gateways, Logistics Providers, Notification Channels).

```mermaid
C4Context
    title System Context Diagram for SALESTORM Flash-Sale Platform

    Person(customer, "Customer", "E-Commerce User attempting to buy flash sale products.")
    Person(admin, "Store Administrator", "Manages inventory, flash sales, and order fulfillments.")

    System(salestorm, "SALESTORM Platform", "High-scale flash-sale e-commerce platform processing concurrent reservations, payments, and orders.")

    System_Ext(payment_gateway, "Payment Gateway", "Stripe / PayPal / Bank Gateway for payment authorization & capture.")
    System_Ext(logistics, "Logistics Partner API", "FedEx / DHL API for tracking & delivery assignment.")
    System_Ext(notification_gw, "Notification Gateway", "Twilio SMS / SendGrid Email service.")

    Rel(customer, salestorm, "Views catalog, places reservations, pays for orders", "HTTPS / WSS")
    Rel(admin, salestorm, "Configures flash sales & views live analytics", "HTTPS")

    Rel(salestorm, payment_gateway, "Authorizes & captures payments", "HTTPS / REST API")
    Rel(salestorm, logistics, "Dispatches shipment requests & fetches tracking", "HTTPS / REST API")
    Rel(salestorm, notification_gw, "Sends transactional SMS & email alerts", "HTTPS / Webhooks")
```

## 2. Context Interaction Rationale
- **Customer $\rightarrow$ SALESTORM:** Encrypted HTTPS requests routed through global Anycast CDN/WAF.
- **SALESTORM $\rightarrow$ Payment Gateway:** Outbound REST calls with Circuit Breaker protection.
- **SALESTORM $\rightarrow$ Logistics / Notifications:** Asynchronous event-driven integration to avoid blocking payment checkout flow.
