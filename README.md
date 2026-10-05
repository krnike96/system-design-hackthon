# SALESTORM — High-Scale E-Commerce Flash Sale Platform
## System Architecture & Engineering Blueprint

**Team Name:** TEAM DEBUGGERS  
**Event:** SYSCRAFTERS 2026 — Design-First, AI-Assisted System Design Hackathon  
**Role:** Senior System Architecture & Engineering Consulting Unit  

---

## 📌 Executive Summary
**SALESTORM** is an enterprise-grade system architecture designed to solve the high-concurrency flash sale problem: **10,000 concurrent customers competing simultaneously for 100 available stock units** of a limited item.

The architecture guarantees:
1. **Zero Overselling:** Under no condition can more than 100 stock units be reserved or sold.
2. **Ultra-Low Latency:** In-memory atomic reservation ($p99 < 50\text{ms}$) via Redis single-threaded Lua scripts.
3. **Complete Payment Idempotency:** Duplicate request prevention (2% network duplicate payloads) using distributed Redis locks.
4. **Order Fault Tolerance:** Event-driven Saga architecture using Apache Kafka + Transactional Outbox pattern, retaining 100% data integrity during a 30-second Order Service crash.

---

## 📂 Repository Deliverables Index

All hackathon deliverables have been organized according to **Section 15 of the SALESTORM Brief**:

| Stage / Module | Deliverable File Link | Description |
| :--- | :--- | :--- |
| **01 Requirements** | [01_Requirements/REQUIREMENTS_AND_ASSUMPTIONS.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/01_Requirements/REQUIREMENTS_AND_ASSUMPTIONS.md) | Functional & Non-Functional Requirements, Traffic Assumptions, RTM. |
| **02 HLD** | [02_HLD/SYSTEM_CONTEXT_DIAGRAM.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/02_HLD/SYSTEM_CONTEXT_DIAGRAM.md) | C4 Level 1 Context Diagram & External Integrations. |
| **02 HLD** | [02_HLD/HLD_ARCHITECTURE.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/02_HLD/HLD_ARCHITECTURE.md) | Complete HLD Diagram, Component Justification & Communication Matrix. |
| **02 HLD** | [02_HLD/CONTAINER_DIAGRAM.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/02_HLD/CONTAINER_DIAGRAM.md) | C4 Level 2 Container Diagram & Service Protocols. |
| **02 HLD** | [02_HLD/COMPONENT_DIAGRAM.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/02_HLD/COMPONENT_DIAGRAM.md) | C4 Level 3 Component Diagrams for Inventory & Payment Services. |
| **02 HLD** | [02_HLD/DEPLOYMENT_DIAGRAM.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/02_HLD/DEPLOYMENT_DIAGRAM.md) | Multi-AZ AWS EKS Kubernetes & Data Subnet Deployment Infrastructure. |
| **03 LLD** | [03_LLD/CLASS_DIAGRAMS.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/03_LLD/CLASS_DIAGRAMS.md) | Domain Model Class Diagrams, Interfaces & Design Pattern Hierarchies. |
| **03 LLD** | [03_LLD/PURCHASE_RESERVATION_SEQUENCE.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/03_LLD/PURCHASE_RESERVATION_SEQUENCE.md) | Purchase & Reservation Sequence Diagram & Redis Lua Script. |
| **03 LLD** | [03_LLD/PAYMENT_SEQUENCE.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/03_LLD/PAYMENT_SEQUENCE.md) | Payment Success, Failure & Timeout Idempotency Sequence Diagram. |
| **03 LLD** | [03_LLD/ORDER_SEQUENCE.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/03_LLD/ORDER_SEQUENCE.md) | Order Creation & 30s Service Outage Recovery Sequence Diagram. |
| **03 LLD** | [03_LLD/STATE_DIAGRAMS.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/03_LLD/STATE_DIAGRAMS.md) | Inventory Reservation & Order Lifecycle State Machines. |
| **04 Database** | [04_Database/DATABASE_ER_DIAGRAM.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/04_Database/DATABASE_ER_DIAGRAM.md) | Database ER Diagram & Production DDL SQL Schema with Indexes. |
| **05 API** | [05_API/API_SPECIFICATION.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/05_API/API_SPECIFICATION.md) | OpenAPI 3.0 Endpoints & Kafka Async Domain Event Schemas. |
| **06 SOLID** | [06_SOLID/SOLID_MAPPING.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/06_SOLID/SOLID_MAPPING.md) | Concrete SOLID Principles Mapping & Code Examples. |
| **07 Patterns** | [07_Design_Patterns/DESIGN_PATTERN_MAPPING.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/07_Design_Patterns/DESIGN_PATTERN_MAPPING.md) | Strategy, Factory, State, Observer, Adapter & Outbox Patterns. |
| **08 Scalability**| [08_Scalability_Reliability/SCALABILITY_AND_RELIABILITY_DESIGN.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/08_Scalability_Reliability/SCALABILITY_AND_RELIABILITY_DESIGN.md) | 500k RPS Scale-Out, Concurrency Comparison & Failure Matrix. |
| **09 Security** | [09_Security_Observability/SECURITY_AND_OBSERVABILITY_DESIGN.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/09_Security_Observability/SECURITY_AND_OBSERVABILITY_DESIGN.md) | OAuth2/JWT, Rate Limiting, OpenTelemetry & Prometheus Metrics. |
| **10 ADR** | [10_ADR/ARCHITECTURE_DECISION_RECORDS.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/10_ADR/ARCHITECTURE_DECISION_RECORDS.md) | Key Architecture Decision Records (Redis L1, Kafka Saga, Idempotency). |
| **11 AI Harness** | [11_AI_Assisted_Validation/SIMULATION_EVIDENCE.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/11_AI_Assisted_Validation/SIMULATION_EVIDENCE.md) | Simulation Results Transcript & Architectural Proof. |
| **11 Simulation**| [11_AI_Assisted_Validation/flash_sale_simulation.py](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/11_AI_Assisted_Validation/flash_sale_simulation.py) | Runnable Async Python Simulation Harness for 10k Concurrency Test. |
| **12 Defense** | [12_Presentation/FINAL_5MIN_PITCH.md](file:///home/niket/Projects/SALESTORM_TEAM_DEBUGGERS/12_Presentation/FINAL_5MIN_PITCH.md) | Final 5-Minute Technical Defense Presentation Script & Timings. |

---

## 🛠️ Running the Practical Simulation
To execute the concurrency and outage simulation locally:
```bash
python3 11_AI_Assisted_Validation/flash_sale_simulation.py
```
