locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  tags = {
    Project     = "luckydraw"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# -------------------------------------------------------
# Random passwords — generated once, stored in Secrets Manager
# -------------------------------------------------------
resource "random_password" "postgres" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}?"
}

resource "random_password" "app_secret_key" {
  length  = 48
  special = false  # Flask secret key — alphanumeric is safest
}

resource "random_password" "admin_password" {
  length           = 20
  special          = true
  override_special = "!#$%&*()-_=+[]{}?"
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.cluster_name}/app-secrets"
  recovery_window_in_days = 0  # allow immediate delete during dev
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    POSTGRES_PASSWORD = random_password.postgres.result
    ADMIN_USERNAME    = "admin"
    ADMIN_PASSWORD    = random_password.admin_password.result
    APP_SECRET_KEY    = random_password.app_secret_key.result
  })
}

# -------------------------------------------------------
# VPC
# -------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i + 4)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Required tags for ALB controller subnet auto-discovery
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  tags = local.tags
}

# -------------------------------------------------------
# EKS
# -------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  # AWS-managed EKS add-ons (these are the ones AWS supports natively)
  cluster_addons = {
    coredns            = { most_recent = true }
    kube-proxy         = { most_recent = true }
    vpc-cni            = { most_recent = true }
    aws-ebs-csi-driver = { most_recent = true }
  }

  eks_managed_node_groups = {
    # Short, descriptive node group name
    luckydraw-ng = {
      instance_types = [var.node_instance_type]
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size

      # EBS CSI driver needs this on the node role
      iam_role_additional_policies = {
        AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
      }

      labels = {
        role = "app"
      }
    }
  }

  tags = local.tags
}

# -------------------------------------------------------
# ECR repositories (one per service)
# -------------------------------------------------------
module "ecr" {
  source = "../../modules/ecr"

  cluster_name = var.cluster_name
  tags         = local.tags
}

# -------------------------------------------------------
# IAM — ALB Controller IRSA
# ALB controller is NOT an EKS managed addon (AWS doesn't offer it as one).
# The IRSA role is created here by Terraform.
# The Helm chart is installed by the infra.yml GitHub Actions workflow
# immediately after terraform apply, so no manual script is needed.
# -------------------------------------------------------
module "iam" {
  source = "../../modules/iam"

  cluster_name            = var.cluster_name
  cluster_oidc_issuer_url = module.eks.cluster_oidc_issuer_url
  oidc_provider_arn       = module.eks.oidc_provider_arn
  tags                    = local.tags
}
