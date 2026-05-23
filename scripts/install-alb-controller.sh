#!/usr/bin/env bash
# Run after `terraform apply` to install AWS Load Balancer Controller via Helm.
# Usage: ./scripts/install-alb-controller.sh <cluster-name> <region> <role-arn>
set -euo pipefail

CLUSTER_NAME="${1:-luckydraw-prod}"
REGION="${2:-us-east-1}"
ALB_ROLE_ARN="${3}"

echo "==> Updating kubeconfig"
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$REGION"

echo "==> Adding eks-charts Helm repo"
helm repo add eks https://aws.github.io/eks-charts
helm repo update

echo "==> Creating ServiceAccount for ALB controller"
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: "${ALB_ROLE_ARN}"
EOF

echo "==> Installing AWS Load Balancer Controller"
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --wait

echo "==> ALB Controller installed successfully"
kubectl get deployment -n kube-system aws-load-balancer-controller
