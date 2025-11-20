# OTP SMS Platform Helm Chart

Enterprise-grade SMS aggregator platform built on Jasmin SMS Gateway with intelligent routing, billing, and monitoring.

## Overview

This Helm chart deploys a complete SMS platform stack including:

- **Jasmin SMS Gateway** - Open-source SMPP gateway
- **API Gateway** - REST API with rate limiting and authentication
- **Billing Service** - CDR tracking, charging, and balance management
- **Routing Service** - Intelligent operator routing with LCR
- **Web Admin** - React-based administration dashboard
- **PostgreSQL** - Primary database
- **Redis** - Caching and rate limiting
- **RabbitMQ** - Message queueing for AMQP events
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- cert-manager (for TLS certificates)
- Nginx Ingress Controller

## Installation

### Add Bitnami Repository

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Install Chart

```bash
helm install otp-sms ./helm/otp-sms-platform \
  --namespace otp-sms \
  --create-namespace \
  --values values-production.yaml
```

### Verify Installation

```bash
kubectl get pods -n otp-sms
kubectl get svc -n otp-sms
kubectl get ingress -n otp-sms
```

## Configuration

### Required Configurations

Update the following values before deploying to production:

```yaml
# values-production.yaml
apiGateway:
  ingress:
    hosts:
      - host: api.yourdomain.com
    tls:
      - secretName: api-tls
        hosts:
          - api.yourdomain.com

webAdmin:
  ingress:
    hosts:
      - host: admin.yourdomain.com
    tls:
      - secretName: admin-tls
        hosts:
          - admin.yourdomain.com

postgresql:
  auth:
    password: <strong-password>

rabbitmq:
  auth:
    password: <strong-password>
```

### Horizontal Pod Autoscaling

The chart includes HPA configurations for autoscaling services based on CPU and memory usage:

**API Gateway:**
```yaml
apiGateway:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

**Billing Service:**
```yaml
billingService:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 6
    targetCPUUtilizationPercentage: 70
```

**Routing Service:**
```yaml
routingService:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5
    targetCPUUtilizationPercentage: 70
```

### Resource Limits

Default resource allocations:

| Service | CPU (req/limit) | Memory (req/limit) |
|---------|-----------------|-------------------|
| API Gateway | 250m/500m | 256Mi/512Mi |
| Billing Service | 250m/500m | 256Mi/512Mi |
| Routing Service | 100m/250m | 128Mi/256Mi |
| Jasmin | 500m/1000m | 512Mi/1Gi |
| PostgreSQL | 500m/1000m | 512Mi/1Gi |
| Redis | 250m/500m | 256Mi/512Mi |
| RabbitMQ | 500m/1000m | 512Mi/1Gi |

### Storage

Persistent volumes are created for:
- PostgreSQL: 10Gi (primary database)
- Redis: 5Gi (cache persistence)
- RabbitMQ: 5Gi (message persistence)
- Prometheus: 20Gi (metrics storage)
- Grafana: 5Gi (dashboard configs)

Adjust sizes based on expected load:

```yaml
postgresql:
  primary:
    persistence:
      size: 50Gi

prometheus:
  server:
    persistentVolume:
      size: 100Gi
```

## Post-Installation Setup

### 1. Initialize Database Schema

```bash
# Get PostgreSQL pod name
POSTGRES_POD=$(kubectl get pod -n otp-sms -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].metadata.name}')

# Run migrations for routing service
kubectl cp services/routing-service/migrations/001_initial_schema.sql $POSTGRES_POD:/tmp/schema.sql -n otp-sms
kubectl exec -it $POSTGRES_POD -n otp-sms -- psql -U otp -d otp -f /tmp/schema.sql
```

### 2. Access Web Admin

```bash
# Get admin URL
kubectl get ingress -n otp-sms otp-sms-web-admin -o jsonpath='{.spec.rules[0].host}'

# Default credentials (change immediately!)
# Check secrets for admin token
kubectl get secret otp-sms-secrets -n otp-sms -o jsonpath='{.data.admin-token}' | base64 -d
```

### 3. Configure SMPP Connectors

Connect to Jasmin jCli to configure SMPP connectors:

```bash
# Port-forward jCli
kubectl port-forward svc/otp-sms-jasmin 1401:1401 -n otp-sms

# Connect via telnet
telnet localhost 1401
# Username: jcliadmin
# Password: jclipwd
```

Add SMPP connectors matching the operators in routing database:

```
smppccm -a
cid: smpp-beeline-uz
host: beeline-smpp.example.com
port: 2775
username: beeline_user
password: beeline_pass
```

## Monitoring

### Prometheus

Access Prometheus:

```bash
kubectl port-forward svc/otp-sms-prometheus-server 9090:9090 -n otp-sms
# Open http://localhost:9090
```

### Grafana

Access Grafana:

```bash
kubectl port-forward svc/otp-sms-grafana 3000:3000 -n otp-sms
# Open http://localhost:3000
# Default: admin / admin
```

## Scaling

### Manual Scaling

```bash
# Scale API Gateway
kubectl scale deployment otp-sms-api-gateway --replicas=5 -n otp-sms

# Scale Billing Service
kubectl scale deployment otp-sms-billing-service --replicas=4 -n otp-sms
```

### Auto-Scaling Metrics

HPA scales based on:
- CPU utilization (70% threshold)
- Memory utilization (80% threshold for API Gateway)

Monitor HPA status:

```bash
kubectl get hpa -n otp-sms
kubectl describe hpa otp-sms-api-gateway -n otp-sms
```

## Troubleshooting

### Check Pod Logs

```bash
# API Gateway logs
kubectl logs -l app.kubernetes.io/component=api-gateway -n otp-sms --tail=100

# Billing Service logs
kubectl logs -l app.kubernetes.io/component=billing-service -n otp-sms --tail=100

# Routing Service logs
kubectl logs -l app.kubernetes.io/component=routing-service -n otp-sms --tail=100
```

### Check Service Health

```bash
# API Gateway health
kubectl run curl --image=curlimages/curl -i --rm --restart=Never -- \
  curl http://otp-sms-api-gateway:8080/health

# Billing Service health
kubectl run curl --image=curlimages/curl -i --rm --restart=Never -- \
  curl http://otp-sms-billing-service:8081/

# Routing Service health
kubectl run curl --image=curlimages/curl -i --rm --restart=Never -- \
  curl http://otp-sms-routing-service:8082/health
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
POSTGRES_POD=$(kubectl get pod -n otp-sms -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POSTGRES_POD -n otp-sms -- psql -U otp -d otp -c "SELECT 1;"
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade otp-sms ./helm/otp-sms-platform \
  --namespace otp-sms \
  --values values-production.yaml \
  --reuse-values

# Rollback if needed
helm rollback otp-sms -n otp-sms
```

## Uninstallation

```bash
helm uninstall otp-sms -n otp-sms
kubectl delete namespace otp-sms
```

**Note:** This will delete all data including PostgreSQL databases. Back up data before uninstalling.

## Security Considerations

1. **Change default passwords** in `values.yaml`:
   - PostgreSQL password
   - RabbitMQ password
   - Jasmin jCli password
   - Admin token

2. **Enable TLS** for all ingresses using cert-manager

3. **Use Kubernetes Secrets** for sensitive data:
   ```bash
   kubectl create secret generic otp-sms-secrets \
     --from-literal=jasmin-user=<user> \
     --from-literal=jasmin-password=<password> \
     -n otp-sms
   ```

4. **Network Policies** - Restrict pod-to-pod communication

5. **RBAC** - Use service accounts with minimal permissions

## License

This Helm chart is part of the Jasmin OTP SMS Platform.
