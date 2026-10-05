# Stage 2: Deployment Diagram (Kubernetes Multi-AZ Production Cloud)

## 1. Cloud Infrastructure & Deployment Topology

```mermaid
flowchart TD
    subgraph AWS["AWS Cloud Infrastructure (Region us-east-1)"]
        subgraph Edge["Edge Security Layer"]
            WAF["Cloudflare Edge WAF & Anycast CDN\n(DDoS Filter & SSL Termination)"]
        end

        subgraph VPC["AWS Virtual Private Cloud (VPC: 10.0.0.0/16)"]
            subgraph PublicSubnet["Public Subnet (Multi-AZ)"]
                ALB["AWS Application Load Balancer (ALB)\n(Layer 7 Load Balancer)"]
            end

            subgraph EKS["AWS EKS Kubernetes Cluster (Private Subnet)"]
                subgraph K8sNS["Namespace: salestorm-prod"]
                    GWPods["API Gateway Pods\n(Kong Ingress, HPA: 5..50)"]
                    InvPods["Inventory Service Pods\n(Go Microservices, HPA: 10..100)"]
                    PayPods["Payment Service Pods\n(Node.js Microservices, HPA: 10..50)"]
                    OrderPods["Order Service Pods\n(Java Spring Boot, HPA: 5..30)"]
                end
            end

            subgraph DataSubnet["Isolated Data Subnet (Multi-AZ)"]
                ElastiCache[("AWS ElastiCache Redis Cluster\n(6 Shards, Multi-AZ Replication)")]
                RDS[("AWS Aurora PostgreSQL Primary + Read Replica\n(Multi-AZ Auto-Failover)")]
                MSK[["AWS MSK Managed Kafka Cluster\n(3 Brokers across 3 AZs)"]]
            end
        end
    end

    WAF --> ALB
    ALB --> GWPods
    GWPods --> InvPods
    GWPods --> PayPods
    GWPods --> OrderPods

    InvPods --> ElastiCache
    InvPods --> RDS
    InvPods --> MSK

    PayPods --> ElastiCache
    PayPods --> MSK

    OrderPods --> RDS
    OrderPods --> MSK
```

---

## 2. Infrastructure Scaling & High-Availability Policies
- **Kubernetes Horizontal Pod Autoscaler (HPA):**
  - **Inventory Service:** Scales based on CPU ($>60\%$) and custom metric `http_requests_per_second`. Pre-scaled to 50 pods 15 minutes before flash sale launch!
- **Data Subnet Isolation:**
  - Database and Cache instances operate inside private subnets accessible only via Security Group rules from the EKS worker node security group.
- **Redundancy & Failover:**
  - Multi-AZ deployment across 3 availability zones (`us-east-1a`, `us-east-1b`, `us-east-1c`).
  - Redis Primary-Replica with automatic failover (< 10 seconds).
  - PostgreSQL Aurora Multi-AZ with zero-data-loss failover (< 15 seconds).
