# SSM Parameter Store / Secrets Manager -> Secret Manager (6 active versions free).
resource "google_secret_manager_secret" "db_password" {
  secret_id = "spry-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret = google_secret_manager_secret.db_password.id

  secret_data_wo         = ephemeral.random_password.db.result
  secret_data_wo_version = var.db_password_version
}

# Only the API's runtime identity can read it, and only this secret.
resource "google_secret_manager_secret_iam_member" "api_reads_db_password" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.api_service_account}"
}
