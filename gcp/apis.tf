# APIs are off by default in a new project. Enabling them here keeps a fresh
# project reproducible from code. disable_on_destroy = false so a destroy does
# not switch off an API something outside this config still uses.
locals {
  apis = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}
