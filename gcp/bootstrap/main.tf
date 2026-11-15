# One-time bootstrap for the Google Cloud project, run by a human owner from a
# laptop with `gcloud auth application-default login` (no key file anywhere).
#
# It creates the identities and their project-level grants, so that the
# workload configuration in ../ (run by HCP Terraform as spry-terraform) never
# needs Project IAM Admin and therefore cannot widen its own permissions.

terraform {
  required_version = ">= 1.11.0"

  # State lives in HCP Terraform, but this workspace uses *Local* execution:
  # the plan runs on the laptop with the owner's ADC, because the identity
  # HCP Terraform would use does not exist yet.
  cloud {
    organization = "SprySZ"

    workspaces {
      name = "spry-gcp-bootstrap"
    }
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

data "google_project" "this" {}

# ---------- APIs the bootstrap itself and keyless auth depend on ----------

locals {
  bootstrap_apis = [
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com", # short-lived SA tokens
    "sts.googleapis.com",            # OIDC token exchange (Workload Identity Federation)
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
  ]
}

resource "google_project_service" "bootstrap" {
  for_each           = toset(local.bootstrap_apis)
  service            = each.value
  disable_on_destroy = false
}

# ---------- Service accounts: one per program ----------

resource "google_service_account" "terraform" {
  account_id   = "spry-terraform"
  display_name = "Spry Terraform (HCP Terraform runs for gcp/)"
  depends_on   = [google_project_service.bootstrap]
}

resource "google_service_account" "api" {
  account_id   = "spry-api"
  display_name = "Spry API runtime (Cloud Run)"
  depends_on   = [google_project_service.bootstrap]
}

# Terraform: only the roles the workload config needs. No Owner/Editor and no
# Project IAM Admin.
locals {
  terraform_roles = [
    "roles/run.admin",
    "roles/cloudsql.admin",
    "roles/artifactregistry.admin",
    "roles/secretmanager.admin",
    "roles/serviceusage.serviceUsageAdmin",
  ]
}

resource "google_project_iam_member" "terraform" {
  for_each = toset(local.terraform_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.terraform.email}"
}

# "Service Account User" granted on the one SA Terraform deploys Cloud Run as,
# not on the whole project: Terraform cannot attach any other identity.
resource "google_service_account_iam_member" "terraform_acts_as_api" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.terraform.email}"
}

# API runtime: connect to Cloud SQL. Secret access is granted per secret in ../.
resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# ---------- Workload Identity Federation for HCP Terraform ----------

resource "google_iam_workload_identity_pool" "hcp" {
  workload_identity_pool_id = "hcp-terraform"
  display_name              = "HCP Terraform"
  description               = "Short-lived OIDC tokens from app.terraform.io"
  depends_on                = [google_project_service.bootstrap]
}

resource "google_iam_workload_identity_pool_provider" "hcp" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.hcp.workload_identity_pool_id
  workload_identity_pool_provider_id = "app-terraform-io"
  display_name                       = "app.terraform.io"

  attribute_mapping = {
    "google.subject"                      = "assertion.sub"
    "attribute.terraform_organization_id" = "assertion.terraform_organization_id"
    "attribute.terraform_workspace_id"    = "assertion.terraform_workspace_id"
    "attribute.terraform_run_phase"       = "assertion.terraform_run_phase"
  }

  # Immutable IDs, not names: an organisation or workspace name can be
  # deleted and re-registered by someone else.
  attribute_condition = join(" && ", [
    "assertion.terraform_organization_id == \"${var.hcp_organization_id}\"",
    "assertion.terraform_workspace_id == \"${var.hcp_workspace_id}\"",
  ])

  oidc {
    issuer_uri = "https://app.terraform.io"
    # Default allowed audience = this provider's full resource name, which is
    # what HCP Terraform sends when TFC_GCP_WORKLOAD_PROVIDER_NAME is set.
  }
}

resource "google_service_account_iam_member" "hcp_impersonates_terraform" {
  service_account_id = google_service_account.terraform.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.hcp.name}/attribute.terraform_workspace_id/${var.hcp_workspace_id}"
}

# ---------- Firebase (Hosting for the static frontend) ----------

resource "google_firebase_project" "this" {
  provider   = google-beta
  project    = var.project_id
  depends_on = [google_project_service.bootstrap]
}
