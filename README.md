# LuckyDraw App — Production Deployment on AWS EKS

A microservices Lucky Draw application deployed on AWS EKS with GitHub Actions CI/CD.

## Architecture

```
User
 │
 ▼
AWS ALB (internet-facing)
 ├── /participate  → participate-app  (Flask + Redis write)
 ├── /submissions  → submissions-app  (Flask + Postgres read)
 └── /             → pick-winner-app  (Flask + Postgres admin)

Background:
  sync-worker  (Redis → Postgres sync, every 5s)

Storage:
  Redis     StatefulSet + EBS PVC (2Gi)
  Postgres  StatefulSet + EBS PVC (10Gi)
```

## Repository Structure

```
.github/workflows/
  infra.yml          # Terraform infrastructure deploy
  deploy.yml         # Docker build + ECR push + EKS deploy

terraform/
  environments/prod/ # Root module (VPC, EKS, ECR, IAM)
  modules/
    ecr/             # ECR repositories
    iam/             # ALB controller IRSA role

docker/
  participate/       # Dockerfile + requirements.txt
  submissions/
  pick-winner/
  sync-worker/

k8s/
  base/              # All Kubernetes manifests
  kustomization.yaml

monitoring/
  kube-prometheus-stack-values.yaml

jenkins/
  Jenkinsfile
  JENKINS_SETUP.md

scripts/
  bootstrap-backend.sh    # Create S3 + DynamoDB for Terraform state
  install-alb-controller.sh

docs/
  infrastructure.md
  kubernetes-deployment.md
  monitoring.md
  troubleshooting.md
```

## Quick Start

```bash
# 1. Bootstrap Terraform backend (run once)
./scripts/bootstrap-backend.sh us-east-1

# 2. Deploy infrastructure
cd terraform/environments/prod
terraform init && terraform apply

# 3. Install ALB controller
ALB_ROLE=$(terraform output -raw alb_controller_role_arn)
./scripts/install-alb-controller.sh luckydraw-prod us-east-1 $ALB_ROLE

# 4. Deploy application (or push to main to trigger GitHub Actions)
# See docs/infrastructure.md for GitHub Actions setup
```

## Local Development

```bash
docker-compose up
```

Services available at:
- http://localhost:8081/participate
- http://localhost:8082/submissions
- http://localhost:5000/ (pick-winner admin)

## Documentation

- [Infrastructure Setup](docs/infrastructure.md)
- [Kubernetes Deployment](docs/kubernetes-deployment.md)
- [Monitoring](docs/monitoring.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Jenkins Setup](jenkins/JENKINS_SETUP.md)
