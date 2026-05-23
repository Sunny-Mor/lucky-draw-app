# Infrastructure Setup

## Prerequisites

- AWS CLI v2 configured with admin credentials
- Terraform >= 1.6.0
- kubectl
- helm >= 3.0
- git

## Step 1 — Bootstrap Terraform Backend

Run once before the first `terraform init`. Creates the S3 bucket and DynamoDB table.

```bash
chmod +x scripts/bootstrap-backend.sh
./scripts/bootstrap-backend.sh us-east-1
```

## Step 2 — Configure GitHub Actions OIDC

Create an IAM role that GitHub Actions can assume via OIDC (no long-lived keys needed).

```bash
# Replace YOUR_GITHUB_ORG and YOUR_REPO_NAME
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create the trust policy (save as trust.json):
cat > /tmp/trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO_NAME:*"
      }
    }
  }]
}
EOF

aws iam create-role \
  --role-name luckydraw-github-actions \
  --assume-role-policy-document file:///tmp/trust.json

aws iam attach-role-policy \
  --role-name luckydraw-github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

> For production, replace AdministratorAccess with a scoped policy covering EKS, ECR, VPC, IAM.

## Step 3 — Set GitHub Actions Secrets

In your GitHub repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `AWS_ROLE_ARN` | ARN of the role created above |
| `ECR_PARTICIPATE_URL` | From `terraform output ecr_participate_url` |
| `ECR_SUBMISSIONS_URL` | From `terraform output ecr_submissions_url` |
| `ECR_PICK_WINNER_URL` | From `terraform output ecr_pick_winner_url` |
| `ECR_SYNC_WORKER_URL` | From `terraform output ecr_sync_worker_url` |
| `POSTGRES_PASSWORD` | Strong password for PostgreSQL |
| `ADMIN_USERNAME` | Admin username for pick-winner panel |
| `ADMIN_PASSWORD` | Admin password for pick-winner panel |
| `APP_SECRET_KEY` | Random string for Flask session signing |

## Step 4 — Deploy Infrastructure

```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

EKS cluster creation takes ~15 minutes.

## Step 5 — Install ALB Controller

```bash
ALB_ROLE_ARN=$(terraform output -raw alb_controller_role_arn)
./scripts/install-alb-controller.sh luckydraw-prod us-east-1 $ALB_ROLE_ARN
```

## Step 6 — Deploy Application

Push to `main` branch or trigger the `Application Deploy` workflow manually.

The workflow will:
1. Build and push all 4 Docker images to ECR
2. Apply Kubernetes manifests via Kustomize
3. Wait for all rollouts to complete
4. Print the ALB DNS name

## Architecture Overview

```
GitHub Actions
    │
    ├── infra.yml ──► Terraform ──► VPC + EKS + ECR + IAM
    │
    └── deploy.yml ─► ECR (4 images)
                   └► kubectl apply -k k8s/
                          │
                          ▼
                    EKS Cluster (luckydraw-prod)
                    namespace: luckydraw
                    ├── participate (2 pods, HPA 2-6)
                    ├── submissions (2 pods, HPA 2-4)
                    ├── pick-winner (1 pod)
                    ├── sync-worker (1 pod)
                    ├── redis StatefulSet + EBS PVC
                    ├── postgres StatefulSet + EBS PVC
                    └── ALB Ingress
                           ├── /participate → participate:80
                           ├── /submissions → submissions:80
                           └── /           → pick-winner:80
```
