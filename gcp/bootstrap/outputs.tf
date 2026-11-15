# Paste these into the spry-gcp workspace as *environment* variables:
#   TFC_GCP_PROVIDER_AUTH             = true
#   TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL = <terraform_service_account>
#   TFC_GCP_WORKLOAD_PROVIDER_NAME    = <workload_provider_name>

output "project_number" {
  value = data.google_project.this.number
}

output "terraform_service_account" {
  value = google_service_account.terraform.email
}

output "api_service_account" {
  value = google_service_account.api.email
}

output "workload_provider_name" {
  value = google_iam_workload_identity_pool_provider.hcp.name
}

output "firebase_hosting_url" {
  value = "https://${var.project_id}.web.app"
}
