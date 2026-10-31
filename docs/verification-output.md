Running plan in HCP Terraform. Output will stream here. Pressing Ctrl-C
will stop streaming the logs, but will not stop the plan running remotely.

Preparing the remote plan...

The remote workspace is configured to work with configuration at
infra relative to the target repository.

Terraform will upload the contents of the following directory,
excluding files or directories as defined by a .terraformignore file
at /Users/sofiia_zavada/spry/.terraformignore (if it is present),
in order to capture the filesystem context the remote workspace expects:
    /Users/sofiia_zavada/spry

To view this run in a browser, visit:
https://app.terraform.io/app/SprySZ/spry-dev/runs/run-pki6Jf7QpydDZXA4

Waiting for the plan to start...

Terraform v1.17.1
on linux_amd64

Initializing plugins and modules...
data.archive_file.mailer_zip: Refreshing...
data.archive_file.mailer_zip: Refresh complete after 0s [id=6265faa2920e5de11c86d4f809f2c8b955c58793]
aws_ses_email_identity.sender: Refreshing state... [id=zavada.sofia@gmail.com]
aws_iam_role.parser: Refreshing state... [id=spry-agenda-parser-role]
aws_sqs_queue.dlq: Refreshing state... [id=https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests-dlq]
aws_vpc_endpoint.s3: Refreshing state... [id=vpce-01808a1ce5f8eeea8]
data.aws_caller_identity.current: Refreshing...
aws_cognito_user_pool.users: Refreshing state... [id=eu-north-1_VArufRzST]
data.aws_caller_identity.current: Refresh complete after 0s [id=545769669518]
aws_iam_role.mailer: Refreshing state... [id=spry-reports-MailerRole-PEgFa4yIMAc0]
aws_s3_bucket.reports: Refreshing state... [id=spry-reports-545769669518]
aws_lambda_function.mailer: Refreshing state... [id=spry-report-mailer]
aws_sqs_queue.requests: Refreshing state... [id=https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests]
aws_cognito_user_pool_domain.domain: Refreshing state... [id=spry-sofiia]
aws_cognito_identity_provider.google: Refreshing state... [id=eu-north-1_VArufRzST:Google]
aws_iam_role.builder: Refreshing state... [id=spry-reports-BuilderRole-kmMmHDKBxIGt]
aws_iam_role.scheduler: Refreshing state... [id=spry-reports-SchedulerRole-IY98j7Hlhb3Y]
aws_cognito_user_pool_client.web: Refreshing state... [id=40q78hb988egmd17hs07hci1vh]
aws_lambda_function.builder: Refreshing state... [id=spry-report-builder]
aws_scheduler_schedule.weekly: Refreshing state... [id=default/spry-weekly-report]
aws_cognito_managed_login_branding.branding: Refreshing state...
aws_lambda_function.parser: Refreshing state... [id=spry-agenda-parser]
aws_lambda_event_source_mapping.builder: Refreshing state... [id=9af8cda3-d44f-47ce-a31c-437faac136f1]
aws_lambda_permission.invoke: Refreshing state... [id=AllowPublicInvoke]
aws_lambda_permission.function_url: Refreshing state... [id=FunctionURLAllowPublicAccess]
aws_lambda_function_url.parser: Refreshing state... [id=spry-agenda-parser]
aws_s3_bucket_public_access_block.reports: Refreshing state... [id=spry-reports-545769669518]
aws_s3_bucket_lifecycle_configuration.reports: Refreshing state... [id=spry-reports-545769669518]
aws_lambda_permission.mailer: Refreshing state... [id=AllowS3Invoke]
aws_s3_bucket_notification.reports: Refreshing state... [id=spry-reports-545769669518]
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.parser,
│   on ai.tf line 2, in resource "aws_iam_role" "parser":
│    2: resource "aws_iam_role" "parser" {
│
│ inline_policy is deprecated. Use the aws_iam_role_policy resource instead.
│ If Terraform should exclusively manage all inline policy associations (the
│ current behavior of this argument), use the aws_iam_role_policies_exclusive
│ resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.parser,
│   on ai.tf line 18, in resource "aws_iam_role" "parser":
│   18:   managed_policy_arns = [
│   19:     "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
│   20:   ]
│
│ managed_policy_arns is deprecated. Use the aws_iam_role_policy_attachment
│ resource instead. If Terraform should exclusively manage all managed policy
│ attachments (the current behavior of this argument), use the
│ aws_iam_role_policy_attachments_exclusive resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.builder,
│   on reports.tf line 107, in resource "aws_iam_role" "builder":
│  107:   managed_policy_arns = [
│  108:     "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
│  109:   ]
│
│ managed_policy_arns is deprecated. Use the aws_iam_role_policy_attachment
│ resource instead. If Terraform should exclusively manage all managed policy
│ attachments (the current behavior of this argument), use the
│ aws_iam_role_policy_attachments_exclusive resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.mailer,
│   on reports.tf line 229, in resource "aws_iam_role" "mailer":
│  229:   managed_policy_arns = [
│  230:     "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
│  231:   ]
│
│ managed_policy_arns is deprecated. Use the aws_iam_role_policy_attachment
│ resource instead. If Terraform should exclusively manage all managed policy
│ attachments (the current behavior of this argument), use the
│ aws_iam_role_policy_attachments_exclusive resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.builder,
│   on reports.tf line 91, in resource "aws_iam_role" "builder":
│   91: resource "aws_iam_role" "builder" {
│
│ inline_policy is deprecated. Use the aws_iam_role_policy resource instead.
│ If Terraform should exclusively manage all inline policy associations (the
│ current behavior of this argument), use the aws_iam_role_policies_exclusive
│ resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.scheduler,
│   on reports.tf line 165, in resource "aws_iam_role" "scheduler":
│  165: resource "aws_iam_role" "scheduler" {
│
│ inline_policy is deprecated. Use the aws_iam_role_policy resource instead.
│ If Terraform should exclusively manage all inline policy associations (the
│ current behavior of this argument), use the aws_iam_role_policies_exclusive
│ resource as well.
╵
╷
│ Warning: Argument is deprecated
│
│   with aws_iam_role.mailer,
│   on reports.tf line 213, in resource "aws_iam_role" "mailer":
│  213: resource "aws_iam_role" "mailer" {
│
│ inline_policy is deprecated. Use the aws_iam_role_policy resource instead.
│ If Terraform should exclusively manage all inline policy associations (the
│ current behavior of this argument), use the aws_iam_role_policies_exclusive
│ resource as well.
╵

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.
