# ECS Fargate service -> Cloud Run. Same Docker image; scales to zero.
locals {
  # Created by gcp/bootstrap, together with its roles/cloudsql.client grant.
  api_service_account = "spry-api@${var.project_id}.iam.gserviceaccount.com"

  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"
}

resource "google_cloud_run_v2_service" "api" {
  name                = "spry-api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = local.api_service_account

    scaling {
      min_instance_count = 0
      max_instance_count = var.api_max_instances
    }

    containers {
      image = coalesce(var.api_image, local.placeholder_image)

      # Cloud Run sends HTTP to $PORT; the image's CMD listens on ${PORT:-8000}.
      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true # request-based billing: CPU only while serving
        startup_cpu_boost = true
      }

      env {
        name  = "CLOUD_SQL_CONNECTION_NAME"
        value = google_sql_database_instance.db.connection_name
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.spry.name
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.spry.name
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret = google_secret_manager_secret.db_password.secret_id
            # Pinned: rotating the password rolls out a new revision.
            version = google_secret_manager_secret_version.db_password.version
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.api_reads_db_password,
  ]
}

# Public, because Firebase Hosting's /api/** rewrite calls it as an anonymous
# client. NOTE: the API does not verify tokens yet (same as on AWS, where the
# ECS service is reachable through CloudFront). See ADR 0009.
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
