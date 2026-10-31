# ==============================================================================
# Temporary Import Blocks for CloudFormation -> Terraform Migration
# Delete this file after initial successful `terraform apply` in HCP Terraform.
# ==============================================================================

# ---------- Auth Stack (from spry-auth) ----------

import {
  to = aws_cognito_user_pool.users
  id = "eu-north-1_VArufRzST"
}

import {
  to = aws_cognito_identity_provider.google
  id = "eu-north-1_VArufRzST:Google"
}

import {
  to = aws_cognito_user_pool_client.web
  id = "eu-north-1_VArufRzST/40q78hb988egmd17hs07hci1vh"
}

import {
  to = aws_cognito_user_pool_domain.domain
  id = "spry-sofiia"
}

import {
  to = aws_cognito_managed_login_branding.branding
  id = "eu-north-1_VArufRzST,6e1ea8e1-4795-41d6-ade8-7ad8cdfd2b64"
}

# ---------- Reports Stack (from spry-reports) ----------

import {
  to = aws_s3_bucket.reports
  id = "spry-reports-545769669518"
}

import {
  to = aws_s3_bucket_public_access_block.reports
  id = "spry-reports-545769669518"
}

import {
  to = aws_s3_bucket_lifecycle_configuration.reports
  id = "spry-reports-545769669518"
}

import {
  to = aws_vpc_endpoint.s3
  id = "vpce-01808a1ce5f8eeea8"
}

import {
  to = aws_sqs_queue.dlq
  id = "https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests-dlq"
}

import {
  to = aws_sqs_queue.requests
  id = "https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests"
}

import {
  to = aws_lambda_event_source_mapping.builder
  id = "9af8cda3-d44f-47ce-a31c-437faac136f1"
}

import {
  to = aws_iam_role.builder
  id = "spry-reports-BuilderRole-kmMmHDKBxIGt"
}

import {
  to = aws_lambda_function.builder
  id = "spry-report-builder"
}

import {
  to = aws_iam_role.scheduler
  id = "spry-reports-SchedulerRole-IY98j7Hlhb3Y"
}

import {
  to = aws_scheduler_schedule.weekly
  id = "default/spry-weekly-report"
}

import {
  to = aws_iam_role.mailer
  id = "spry-reports-MailerRole-PEgFa4yIMAc0"
}

import {
  to = aws_lambda_function.mailer
  id = "spry-report-mailer"
}

import {
  to = aws_ses_email_identity.sender
  id = "zavada.sofia@gmail.com"
}

# ---------- AI Stack (from spry-ai) ----------

import {
  to = aws_iam_role.parser
  id = "spry-agenda-parser-role"
}

import {
  to = aws_lambda_function.parser
  id = "spry-agenda-parser"
}

import {
  to = aws_lambda_function_url.parser
  id = "spry-agenda-parser"
}
