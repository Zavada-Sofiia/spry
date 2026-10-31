# Lab 7: Supplementary Infrastructure Migration — Submission Evidence

This document contains the required three submission deliverables for the CloudFormation to Terraform migration lab.

---

## 1. Commit and Pull Request Links

- **Initial Migration PR (CloudFormation Adoption & Cleanup)**:
  - **Pull Request #2**: [https://github.com/Zavada-Sofiia/spry/pull/2](https://github.com/Zavada-Sofiia/spry/pull/2)
  - **Merge Commit**: [`b5d0afd`](https://github.com/Zavada-Sofiia/spry/commit/b5d0afd)
  - **Cleanup Commit (Removal of `.yml` templates & temporary imports)**: [`ee90d9f`](https://github.com/Zavada-Sofiia/spry/commit/ee90d9f)
  - **Summary**: Adopted 22 pre-existing AWS resources via `import` blocks, created 4 child resources fresh (`notification` and 3 Lambda permissions), and verified zero destruction (`22 imported, 4 added, 0 destroyed`).

- **Parity Fix PR (Part A — Restoration of Pre-Migration Settings)**:
  - **Pull Request #3**: [https://github.com/Zavada-Sofiia/spry/pull/3](https://github.com/Zavada-Sofiia/spry/pull/3)
  - **Merge Commit**: [`feaf415`](https://github.com/Zavada-Sofiia/spry/commit/feaf415)
  - **Summary**: Restored SQS `max_message_size` to 1048576 (1 MB), restored parser Lambda `MOCK_AI` to `"true"`, restored exact WeeklySchedule payload string, and pinned builder Lambda image digest to `@sha256:1cd862...`.

---

## 2. Screenshot Instructions

Please take a screenshot of the HCP Terraform execution run page for the merge-triggered apply:

- **HCP Run URL**: [https://app.terraform.io/app/SprySZ/spry-dev/runs/run-d6vZNzFWxDxksQud](https://app.terraform.io/app/SprySZ/spry-dev/runs/run-d6vZNzFWxDxksQud)
- **What the screenshot must show**:
  1. Trigger source clearly indicating GitHub VCS: **`Zavada-Sofiia triggered a run from GitHub`** (Merge pull request #2).
  2. Status: **`Applied`** (green badge).
  3. Resource Summary: **`22 to import, 4 to add, 15 to change, 0 to destroy`**.
  4. Diagnostics / Warnings: Deprecation warnings for inline policies / managed policy ARNs.

*(Alternative: You may also capture the parity apply run page: [https://app.terraform.io/app/SprySZ/spry-dev/runs/run-ZBB9rEJ29AM36uYZ](https://app.terraform.io/app/SprySZ/spry-dev/runs/run-ZBB9rEJ29AM36uYZ) showing `Merge pull request #3`, `Applied`, `0 to add, 5 to change, 0 to destroy`).*

---

## 3. Fresh "No Changes" Plan Proof (Post-Cleanup)

- **HCP Run URL**: [https://app.terraform.io/app/SprySZ/spry-dev/runs/run-qRCaKBu5AQU8x4Px](https://app.terraform.io/app/SprySZ/spry-dev/runs/run-qRCaKBu5AQU8x4Px)
- **Execution Date**: 2026-10-31
- **Context**: Plan only executed in workspace `spry-dev` after merging PR #3 and removing residual duplicate CloudFormation statement IDs from Lambda function resource policies.

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
