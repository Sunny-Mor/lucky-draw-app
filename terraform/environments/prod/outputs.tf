output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "EKS cluster CA data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "ecr_participate_url" {
  value = module.ecr.repository_urls["participate"]
}

output "ecr_submissions_url" {
  value = module.ecr.repository_urls["submissions"]
}

output "ecr_pick_winner_url" {
  value = module.ecr.repository_urls["pick-winner"]
}

output "ecr_sync_worker_url" {
  value = module.ecr.repository_urls["sync-worker"]
}

output "alb_controller_role_arn" {
  value = module.iam.alb_controller_role_arn
}
