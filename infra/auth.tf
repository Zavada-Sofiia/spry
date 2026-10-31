# ---------- Cognito User Pool ----------
resource "aws_cognito_user_pool" "users" {
  name                     = "${var.project_name}-users"
  user_pool_tier           = "ESSENTIALS"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  tags = {
    PROJECT_NAME = var.project_name
  }
}

# ---------- Google Identity Provider ----------
resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.users.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "openid email profile"
  }

  attribute_mapping = {
    email          = "email"
    email_verified = "email_verified"
  }

  lifecycle {
    ignore_changes = [provider_details, attribute_mapping]
  }
}

# ---------- App Client ----------
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project_name}-web"
  user_pool_id = aws_cognito_user_pool.users.id

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO", "Google"]

  callback_urls = [
    "${var.site_url}/",
    "http://localhost:3000/"
  ]
  logout_urls = [
    "${var.site_url}/",
    "http://localhost:3000/"
  ]

  depends_on = [aws_cognito_identity_provider.google]
}

# ---------- Cognito Domain ----------
resource "aws_cognito_user_pool_domain" "domain" {
  domain                = var.domain_prefix
  user_pool_id          = aws_cognito_user_pool.users.id
  managed_login_version = 2
}

# ---------- Managed Login Branding ----------
resource "aws_cognito_managed_login_branding" "branding" {
  user_pool_id                = aws_cognito_user_pool.users.id
  client_id                   = aws_cognito_user_pool_client.web.id
  use_cognito_provided_values = true
}
