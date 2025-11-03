variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "nim-rag-agent-cluster"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
