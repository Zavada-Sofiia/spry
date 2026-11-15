# ECR -> Artifact Registry. 0.5 GB is free, then $0.10/GB-month. The backend
# image is ~800 MB unpacked (a few hundred MB compressed, base layers shared),
# so keep only the two most recent images: current + one to roll back to.
resource "google_artifact_registry_repository" "spry" {
  repository_id = "spry"
  location      = var.region
  format        = "DOCKER"
  description   = "Spry backend images"

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-latest-2"
    action = "KEEP"
    most_recent_versions {
      keep_count = 2
    }
  }

  cleanup_policies {
    id     = "delete-older"
    action = "DELETE"
    condition {
      older_than = "86400s"
    }
  }

  depends_on = [google_project_service.apis]
}
