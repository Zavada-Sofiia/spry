variable "project_id" {
  description = "Google Cloud project ID (permanent, globally unique)"
  type        = string
}

variable "region" {
  description = "Default region"
  type        = string
  default     = "us-central1"
}

variable "hcp_organization_id" {
  description = "HCP Terraform organization ID (org-...), from Organization settings > General"
  type        = string

  validation {
    condition     = startswith(var.hcp_organization_id, "org-")
    error_message = "Use the organization ID (org-...), not its name."
  }
}

variable "hcp_workspace_id" {
  description = "HCP Terraform workspace ID (ws-...) of spry-gcp, from Workspace > Settings > General"
  type        = string

  validation {
    condition     = startswith(var.hcp_workspace_id, "ws-")
    error_message = "Use the workspace ID (ws-...), not its name."
  }
}
