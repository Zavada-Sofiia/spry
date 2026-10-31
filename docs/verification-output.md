# Verification Evidence: Zero-Drift & State Reconciliation

## 1. State Reconciliation: 28 Resources in State vs. 26 Managed Resources

Executing `terraform -chdir=infra state list` confirms exactly **28** tracked items in HCP Terraform state:

```text
data.archive_file.mailer_zip
data.aws_caller_identity.current
aws_cognito_identity_provider.google
aws_cognito_managed_login_branding.branding
aws_cognito_user_pool.users
aws_cognito_user_pool_client.web
aws_cognito_user_pool_domain.domain
aws_iam_role.builder
aws_iam_role.mailer
aws_iam_role.parser
aws_iam_role.scheduler
aws_lambda_event_source_mapping.builder
aws_lambda_function.builder
aws_lambda_function.mailer
aws_lambda_function.parser
aws_lambda_function_url.parser
aws_lambda_permission.function_url
aws_lambda_permission.invoke
aws_lambda_permission.mailer
aws_s3_bucket.reports
aws_s3_bucket_lifecycle_configuration.reports
aws_s3_bucket_notification.reports
aws_s3_bucket_public_access_block.reports
aws_scheduler_schedule.weekly
aws_ses_email_identity.sender
aws_sqs_queue.dlq
aws_sqs_queue.requests
aws_vpc_endpoint.s3
```

### Breakdown:
- **26 Managed Resources** (`aws_*` blocks in HCL)
- **2 Tracked Data Sources**:
  1. `data.archive_file.mailer_zip`: Tracks the inline Python archive zip attributes in state.
  2. `data.aws_caller_identity.current`: Tracks the resolved AWS Account ID in state.
- **Total**: $26 + 2 = \mathbf{28}$ items reported in the HCP Terraform "Resources" widget.

---

## 2. Final Post-Cleanup Remote Plan Output (No changes)

- **HCP Run ID**: `run-qRCaKBu5AQU8x4Px`
- **HCP Run URL**: https://app.terraform.io/app/SprySZ/spry-dev/runs/run-qRCaKBu5AQU8x4Px
- **Trigger**: CLI remote plan executed against `spry-dev` workspace after merging PR #3 (parity fix) and removing legacy CloudFormation duplicate permissions in Part C.
- **Execution Date**: 2026-10-31

```text
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
https://app.terraform.io/app/SprySZ/spry-dev/runs/run-qRCaKBu5AQU8x4Px

Waiting for the plan to start...

Terraform v1.17.1
on linux_amd64

Initializing plugins and modules...
data.archive_file.mailer_zip: Refreshing...
data.archive_file.mailer_zip: Refresh complete after 0s [id=6265faa2920e5de11c86d4f809f2c8b955c58793]
data.aws_caller_identity.current: Refreshing...
aws_iam_role.parser: Refreshing state... [id=spry-agenda-parser-role]
aws_vpc_endpoint.s3: Refreshing state... [id=vpce-01808a1ce5f8eeea8]
aws_ses_email_identity.sender: Refreshing state... [id=zavada.sofia@gmail.com]
aws_sqs_queue.dlq: Refreshing state... [id=https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests-dlq]
aws_cognito_user_pool.users: Refreshing state... [id=eu-north-1_VArufRzST]
data.aws_caller_identity.current: Refresh complete after 0s [id=545769669518]
aws_iam_role.mailer: Refreshing state... [id=spry-reports-MailerRole-PEgFa4yIMAc0]
aws_s3_bucket.reports: Refreshing state... [id=spry-reports-545769669518]
aws_lambda_function.mailer: Refreshing state... [id=spry-report-mailer]
aws_sqs_queue.requests: Refreshing state... [id=https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests]
aws_cognito_identity_provider.google: Refreshing state... [id=eu-north-1_VArufRzST:Google]
aws_cognito_user_pool_domain.domain: Refreshing state... [id=spry-sofiia]
aws_iam_role.builder: Refreshing state... [id=spry-reports-BuilderRole-kmMmHDKBxIGt]
aws_iam_role.scheduler: Refreshing state... [id=spry-reports-SchedulerRole-IY98j7Hlhb3Y]
aws_cognito_user_pool_client.web: Refreshing state... [id=40q78hb988egmd17hs07hci1vh]
aws_scheduler_schedule.weekly: Refreshing state... [id=default/spry-weekly-report]
aws_lambda_function.builder: Refreshing state... [id=spry-report-builder]
aws_cognito_managed_login_branding.branding: Refreshing state...
aws_lambda_function.parser: Refreshing state... [id=spry-agenda-parser]
aws_lambda_event_source_mapping.builder: Refreshing state... [id=9af8cda3-d44f-47ce-a31c-437faac136f1]
aws_lambda_permission.function_url: Refreshing state... [id=FunctionURLAllowPublicAccess]
aws_lambda_function_url.parser: Refreshing state... [id=spry-agenda-parser]
aws_lambda_permission.invoke: Refreshing state... [id=AllowPublicInvoke]
aws_s3_bucket_lifecycle_configuration.reports: Refreshing state... [id=spry-reports-545769669518]
aws_s3_bucket_public_access_block.reports: Refreshing state... [id=spry-reports-545769669518]
aws_lambda_permission.mailer: Refreshing state... [id=AllowS3Invoke]
aws_s3_bucket_notification.reports: Refreshing state... [id=spry-reports-545769669518]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration and
found no differences, so no changes are needed.
```
