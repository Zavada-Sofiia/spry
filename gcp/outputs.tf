output "api_url" {
  description = "Cloud Run URL of the API"
  value       = google_cloud_run_v2_service.api.uri
}

output "site_url" {
  description = "Firebase Hosting URL (frontend, /api/** rewritten to Cloud Run)"
  value       = "https://${var.project_id}.web.app"
}

output "image_repository" {
  description = "Push backend images here"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.spry.repository_id}/backend"
}

output "db_instance" {
  value = google_sql_database_instance.db.name
}

output "db_connection_name" {
  value = google_sql_database_instance.db.connection_name
}

output "db_password_secret" {
  value = google_secret_manager_secret.db_password.secret_id
}
