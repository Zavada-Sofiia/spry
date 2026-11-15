terraform {
  # 1.11+ for ephemeral values and write-only attributes: the database
  # password is generated, stored in Secret Manager and set on the user
  # without ever being written to Terraform state.
  required_version = ">= 1.11.0"

  # A second HCP Terraform workspace, separate from infra/ (spry-dev):
  # one plan cannot touch both clouds.
  # Remote execution; credentials are dynamic (Workload Identity Federation),
  # configured by gcp/bootstrap. No service account key exists.
  cloud {
    organization = "SprySZ"

    workspaces {
      name = "spry-gcp"
    }
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  default_labels = {
    project    = "spry"
    managed-by = "terraform"
  }
}
