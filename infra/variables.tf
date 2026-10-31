variable "project_name" {
  description = "Project name prefix for resources and tags"
  type        = string
  default     = "spry"
}

variable "aws_region" {
  description = "AWS region for deployments"
  type        = string
  default     = "eu-north-1"
}

# ---------- Auth Stack (Lab 4) ----------

variable "domain_prefix" {
  description = "Cognito hosted UI domain prefix"
  type        = string
  default     = "spry-sofiia"
}

variable "site_url" {
  description = "Frontend origin URL for CORS and OAuth redirects"
  type        = string
  default     = "https://d1pk13cbcfrq49.cloudfront.net"
}

variable "google_client_id" {
  description = "Google OAuth Client ID for Cognito Identity Provider"
  type        = string
  default     = null
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret for Cognito Identity Provider"
  type        = string
  sensitive   = true
}

# ---------- Reports Stack (Lab 5) ----------

variable "builder_image_uri" {
  description = "Container image URI for report builder Lambda"
  type        = string
  default     = "545769669518.dkr.ecr.eu-north-1.amazonaws.com/spry-backend:latest"
}

variable "vpc_id" {
  description = "VPC ID where Aurora and ECS run"
  type        = string
  default     = "vpc-0a4ba1d2c35976d63"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for report builder Lambda"
  type        = list(string)
  default     = ["subnet-0d7fd77e5bf73abbd", "subnet-0e2cdde417e0aa0ce", "subnet-0b67c45fba56f734d"]
}

variable "private_route_table_ids" {
  description = "Private route table IDs for S3 gateway endpoint"
  type        = list(string)
  default     = ["rtb-0a2a44e48d6ac2f03"]
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda VPC connectivity"
  type        = string
  default     = "sg-07172fe5ea15a237c"
}

variable "sender_email" {
  description = "Verified SES sender email address"
  type        = string
  default     = "zavada.sofia@gmail.com"
}

variable "recipient_emails" {
  description = "Comma-separated list of recipient email addresses for reports"
  type        = string
  default     = "zavada.sofia@gmail.com"
}

variable "database_url" {
  description = "PostgreSQL connection URL for Aurora Serverless v2"
  type        = string
  sensitive   = true
}

# ---------- AI Agenda Parser Stack (Lab 6) ----------

variable "parser_image_uri" {
  description = "Container image URI for agenda parser Lambda"
  type        = string
  default     = "545769669518.dkr.ecr.eu-north-1.amazonaws.com/spry-backend:latest"
}

variable "parser_model" {
  description = "Bedrock model ID for agenda parser"
  type        = string
  default     = "anthropic.claude-opus-5-5"
}

variable "mock_ai" {
  description = "Whether agenda parser Lambda runs in mock mode ('true' or 'false')"
  type        = string
  default     = "true"
}
