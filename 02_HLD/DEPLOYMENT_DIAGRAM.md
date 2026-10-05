# Stage 2: Deployment Diagram (Kubernetes Multi-AZ Production Cloud)

## 1. Cloud Infrastructure & Deployment Topology

```mermaid
deploymentView
    title Deployment Diagram for SALESTORM Production Cluster (AWS / EKS)

    deploymentNode(aws, "AWS Cloud Infrastructure", "AWS Cloud Region us-east-1") {
        deploymentNode(cdn_edge, "Cloudflare Anycast CDN & WAF", "Edge Network") {
            node(waf, "Cloudflare Edge Nodes", "DDoS Filter & SSL Termination")
        }

        deploymentNode(vpc, "AWS Virtual Private Cloud (VPC)", "10.0.0.0/16") {
            deploymentNode(public_subnet, "Public Subnet (Multi-AZ)", "10.0.1.0/24 & 10.0.2.0/24") {
                node(alb, "AWS Application Load Balancer (ALB)", "Cross-AZ Load Balancer")
            }

            deploymentNode(eks_cluster, "AWS EKS Kubernetes Cluster", "Private Subnet") {
                deploymentNode(k8s_ns, "Namespace: salestorm-prod", "Kubernetes Namespace") {
                    node(gw_pods, "API Gateway Pods (Auto-scaling HPA 5..50)", "Kong Ingress Controller")
                    node(inv_pods, "Inventory Service Pods (HPA 10..100)", "Go Microservices")
                    node(pay_pods, "Payment Service Pods (HPA 10..50)", "Node.js Microservices")
                    node(order_pods, "Order Service Pods (HPA 5..30)", "Java Spring Boot Pods")
                }
            }

            deploymentNode(data_subnet, "Isolated Data Subnet (Multi-AZ)", "10.0.10.0/24") {
                node(elasticache, "AWS ElastiCache Redis Cluster", "6 Shards, Multi-AZ Replication")
                node(rds, "AWS Aurora PostgreSQL Primary + Read Replica", "Multi-AZ Auto-failover")
                node(msk, "AWS MSK Managed Kafka Cluster", "3 Brokers across 3 AZs")
            }
        }
    }

    waf --> alb
    alb --> gw_pods
    gw_pods --> inv_pods
    gw_pods --> pay_pods
    gw_pods --> order_pods

    inv_pods --> elasticache
    inv_pods --> rds
    inv_pods --> msk

    pay_pods --> elasticache
    pay_pods --> msk

    order_pods --> rds
    order_pods --> msk
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
