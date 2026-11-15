variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, Cloud SQL and Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "api_image" {
  description = <<-EOT
    Backend image in Artifact Registry, pinned by digest
    (us-central1-docker.pkg.dev/<project>/spry/backend@sha256:...).
    Null on the very first apply: Cloud Run then runs Google's hello
    container until the real image has been pushed (`make gcp-push-api`).
  EOT
  type        = string
  default     = null
}

variable "db_tier" {
  description = "Cloud SQL machine tier (smallest shared core)"
  type        = string
  default     = "db-f1-micro"
}

variable "db_password_version" {
  description = "Bump to rotate the database password (write-only attributes are only re-sent when this changes)"
  type        = number
  default     = 1
}

variable "api_max_instances" {
  description = "Upper bound on Cloud Run instances; also bounds connections to db-f1-micro (max_connections = 25)"
  type        = number
  default     = 3
}
