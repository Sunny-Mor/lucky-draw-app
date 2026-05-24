# Monitoring Setup

## Structure

```
monitoring/
└── kube-prometheus-stack/
    ├── Chart.yaml           # declares kube-prometheus-stack v58.0.0 as dependency
    └── values-override.yaml # all customisations (storage, retention, EKS tweaks)
```

## Deploy

```bash
# 1. Pull the chart dependency into the repo
cd monitoring/kube-prometheus-stack
helm dependency update

# 2. Get Grafana password from Secrets Manager (set by Terraform)
GRAFANA_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id luckydraw-prod/app-secrets \
  --query SecretString --output text | jq -r .ADMIN_PASSWORD)

# 3. Install
helm upgrade --install luckydraw-monitoring . \
  --namespace monitoring \
  --create-namespace \
  --values values-override.yaml \
  --set kube-prometheus-stack.grafana.adminPassword="$GRAFANA_PASSWORD" \
  --wait
```

## Access Grafana

```bash
kubectl port-forward svc/luckydraw-monitoring-grafana 3000:80 -n monitoring
```

Open http://localhost:3000 — user: `admin`, password: from Secrets Manager above.

## Access Prometheus

```bash
kubectl port-forward svc/luckydraw-monitoring-kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

## Access Alertmanager

```bash
kubectl port-forward svc/luckydraw-monitoring-kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
```

## Check Status

```bash
kubectl get pods -n monitoring
kubectl get pvc  -n monitoring
```
