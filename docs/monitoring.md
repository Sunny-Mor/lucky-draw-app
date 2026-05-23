# Monitoring Setup

## Deploy kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/kube-prometheus-stack-values.yaml \
  --set grafana.adminPassword=$GRAFANA_PASSWORD \
  --version 58.0.0 \
  --wait
```

## Access Grafana

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

Open http://localhost:3000 — default user: `admin`

## Useful Dashboards (pre-installed)

| Dashboard | ID |
|---|---|
| Kubernetes Cluster Overview | 7249 |
| Node Exporter Full | 1860 |
| Kubernetes Pods | 6781 |

## Check Stack Status

```bash
kubectl get pods -n monitoring
kubectl get pvc  -n monitoring
```

## Prometheus Targets

```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

Open http://localhost:9090/targets to verify all scrape targets are UP.

## Alertmanager

```bash
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n monitoring
```

Open http://localhost:9093 to view active alerts.
