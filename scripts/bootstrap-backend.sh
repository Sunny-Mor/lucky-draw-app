#!/usr/bin/env bash
# Run this ONCE before the first `terraform init`.
# Creates the S3 bucket for Terraform remote state.
# Native S3 locking is used (Terraform >= 1.10) — no DynamoDB needed.
set -euo pipefail

REGION="${1:-us-east-1}"
BUCKET="luckydraw-tfstate"

echo "==> Creating S3 backend bucket: $BUCKET in $REGION"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "    Bucket already exists, skipping."
else
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET" \
      --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi

  aws s3api put-bucket-versioning \
    --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled

  aws s3api put-bucket-encryption \
    --bucket "$BUCKET" \
    --server-side-encryption-configuration \
      '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

  aws s3api put-public-access-block \
    --bucket "$BUCKET" \
    --public-access-block-configuration \
      "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

  echo "    Bucket created and secured."
fi

echo ""
echo "==> Bootstrap complete."
echo "    Next: cd terraform/environments/prod && terraform init"
