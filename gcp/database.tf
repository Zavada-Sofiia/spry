# Aurora Serverless v2 -> Cloud SQL for PostgreSQL, db-f1-micro.
# Unlike Aurora it does NOT pause on idle: it bills by the hour until stopped.
resource "google_sql_database_instance" "db" {
  name             = "spry-db"
  database_version = "POSTGRES_16" # same major as docker-compose (16.2)
  region           = var.region

  # Lets `terraform destroy` remove it at clean-up time. This is a lab copy of
  # the data, re-creatable from migrations.
  deletion_protection = false

  settings {
    # PostgreSQL 16 defaults to Enterprise Plus, which has no shared-core tiers.
    edition           = "ENTERPRISE"
    tier              = var.db_tier
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    # Storage only grows and is billed while stopped too: keep it fixed.
    disk_autoresize = false

    activation_policy = "ALWAYS"

    deletion_protection_enabled = false

    backup_configuration {
      enabled = false
    }

    ip_configuration {
      # Public IP with *no* authorised networks: nothing can reach it directly.
      # Cloud Run connects through the Cloud SQL connector (IAM + mTLS).
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }

    user_labels = {
      project = "spry"
    }
  }

  lifecycle {
    # Started and stopped with `make gcp-db-start` / `make gcp-db-stop`, not
    # through a pull request; Terraform must not flip it back.
    ignore_changes = [settings[0].activation_policy]
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "spry" {
  name     = "spry"
  instance = google_sql_database_instance.db.name
}

# Generated per run, never stored in state: written once to Secret Manager and
# to the database user through write-only attributes, re-sent only when
# db_password_version changes.
ephemeral "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_user" "spry" {
  name     = "spry"
  instance = google_sql_database_instance.db.name

  password_wo         = ephemeral.random_password.db.result
  password_wo_version = var.db_password_version
}
