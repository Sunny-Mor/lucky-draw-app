# Kubernetes Deployment

## Namespace

All application resources live in the `luckydraw` namespace.

## Services

| Service | Replicas | HPA | Port | Path |
|---|---|---|---|---|
| participate | 2 (min) | 2–6 | 5000 | /participate |
| submissions | 2 (min) | 2–4 | 5000 | /submissions |
| pick-winner | 1 | none | 5000 | / |
| sync-worker | 1 | none | 5000 | internal only |
| redis | 1 | none | 6379 | internal only |
| postgres | 1 | none | 5432 | internal only |

## Manual Deploy (without CI/CD)

```bash
# 1. Update kubeconfig
aws eks update-kubeconfig --name luckydraw-prod --region us-east-1

# 2. Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD=your-password \
  --namespace=luckydraw --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic app-secret \
  --from-literal=ADMIN_USERNAME=admin \
  --from-literal=ADMIN_PASSWORD=your-admin-password \
  --from-literal=SECRET_KEY=your-flask-secret \
  --namespace=luckydraw --dry-run=client -o yaml | kubectl apply -f -

# 3. Set image tags
IMAGE_TAG=latest
ECR_BASE=123456789.dkr.ecr.us-east-1.amazonaws.com/luckydraw-prod

sed -i "s|PARTICIPATE_IMAGE|${ECR_BASE}/participate:${IMAGE_TAG}|g" k8s/base/participate/participate.yaml
sed -i "s|SUBMISSIONS_IMAGE|${ECR_BASE}/submissions:${IMAGE_TAG}|g" k8s/base/submissions/submissions.yaml
sed -i "s|PICK_WINNER_IMAGE|${ECR_BASE}/pick-winner:${IMAGE_TAG}|g" k8s/base/pick-winner/pick-winner.yaml
sed -i "s|SYNC_WORKER_IMAGE|${ECR_BASE}/sync-worker:${IMAGE_TAG}|g" k8s/base/sync-worker/sync-worker.yaml

# 4. Apply
kubectl apply -k k8s/

# 5. Watch rollout
kubectl rollout status deployment/participate -n luckydraw
kubectl rollout status deployment/submissions -n luckydraw
kubectl rollout status deployment/pick-winner -n luckydraw
kubectl rollout status deployment/sync-worker -n luckydraw
```

## Check Status

```bash
kubectl get all -n luckydraw
kubectl get ingress -n luckydraw
kubectl get pvc -n luckydraw
kubectl get hpa -n luckydraw
```

## View Logs

```bash
kubectl logs -l app=participate  -n luckydraw --tail=50
kubectl logs -l app=submissions  -n luckydraw --tail=50
kubectl logs -l app=pick-winner  -n luckydraw --tail=50
kubectl logs -l app=sync-worker  -n luckydraw --tail=50
```

## Rollback

```bash
kubectl rollout undo deployment/participate -n luckydraw
```

## Data Flow

```
User submits form
    │
    ▼
participate-app ──► Redis hash (lucky_draw_entries)
                          │
                    sync-worker polls every 5s
                          │
                          ▼
                     PostgreSQL (luckydraw table)
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       submissions-app          pick-winner-app
    (view all entries)       (admin picks winner)
```
