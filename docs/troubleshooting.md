# Troubleshooting

## Pods stuck in Pending

```bash
kubectl describe pod <pod-name> -n luckydraw
```

Common causes:
- PVC not bound → check `kubectl get pvc -n luckydraw`. EBS CSI driver must be installed.
- Insufficient node resources → check `kubectl describe nodes`.

## Pods in CrashLoopBackOff

```bash
kubectl logs <pod-name> -n luckydraw --previous
```

Common causes:
- `participate` / `submissions` / `sync-worker`: cannot connect to Redis or Postgres. Check secrets and ConfigMaps.
- `sync-worker`: Postgres table creation fails → check Postgres pod is Ready first.

## ALB not provisioned (Ingress ADDRESS is empty)

```bash
kubectl describe ingress luckydraw-ingress -n luckydraw
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

Common causes:
- ALB controller not installed → run `scripts/install-alb-controller.sh`
- Subnet tags missing → verify `kubernetes.io/role/elb=1` on public subnets
- IRSA role not attached → check ServiceAccount annotation

## Terraform apply fails on EKS

- EKS cluster creation can take 15–20 min. If it times out, re-run `terraform apply`.
- If node group fails, check IAM role has `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly`.

## ECR push fails in GitHub Actions

- Verify `AWS_ROLE_ARN` secret is set correctly.
- Verify the OIDC provider is created in IAM.
- Verify the trust policy `sub` condition matches your repo path.

## Redis connection refused

```bash
kubectl exec -it redis-0 -n luckydraw -- redis-cli ping
```

Should return `PONG`. If not, check StatefulSet and PVC status.

## Postgres connection refused

```bash
kubectl exec -it postgres-0 -n luckydraw -- pg_isready -U postgres
```

## Force restart a deployment

```bash
kubectl rollout restart deployment/participate -n luckydraw
```

## Check HPA status

```bash
kubectl get hpa -n luckydraw
kubectl describe hpa participate -n luckydraw
```

If HPA shows `<unknown>` for CPU, metrics-server may not be installed:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
