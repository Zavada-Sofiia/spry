# Migration Runbook: CloudFormation to Terraform (HCP Terraform)

This runbook guides the human operator through the zero-downtime, zero-destruction migration of Spry's Auth, Reports, and AI stacks from AWS CloudFormation to Terraform managed by HCP Terraform.

> **CRITICAL**: Every command below requires human execution or confirmation. Commands marked **[HUMAN]** must be run by you.
> Do NOT delete any CloudFormation stack until Step 3a has been verified in the AWS Console.

---

## Prerequisites & HCP Terraform Setup

1. **HCP Terraform Workspace**:
   - Organization: `SprySZ`
   - Workspace: `spry-dev`
   - Execution Mode: **Remote**
   - Working Directory: `infra`
   - VCS Provider: Connected to GitHub repository `Zavada-Sofiia/spry` (or current repository).

2. **HCP Terraform Variables**:
   Under **Workspace -> Variables**:
   - **Environment Variables** (Category: `env`):
     - `TFC_AWS_PROVIDER_AUTH` = `true`
     - `TFC_AWS_RUN_ROLE_ARN` = `arn:aws:iam::545769669518:role/spry-tfc-role`
   - **Terraform Variables** (Category: `terraform`):
     - `google_client_secret` = `<your-google-oauth-client-secret>` (Sensitive: `true`)
     - `database_url` = `postgresql://postgres@database-1.cluster-c7oceugkgaxi.eu-north-1.rds.amazonaws.com:5432/postgres` (Sensitive: `true`)

---

## Step 3a: Deploy Retain Policies and Delete CloudFormation Stacks

All resources in `infra/auth.yml`, `infra/reports.yml`, and `infra/ai.yml` have already been edited to include:
```yaml
DeletionPolicy: Retain
UpdateReplacePolicy: Retain
```

### 1. Update the running CloudFormation stacks to apply the Retain policies:

**[HUMAN]** Run AWS CloudFormation update for `spry-auth`:
```bash
aws cloudformation update-stack \
  --region eu-north-1 \
  --stack-name spry-auth \
  --use-previous-template \
  --template-body file://infra/auth.yml \
  --parameters ParameterKey=GoogleClientSecret,UsePreviousValue=true ParameterKey=GoogleClientId,UsePreviousValue=true ParameterKey=ProjectName,UsePreviousValue=true ParameterKey=DomainPrefix,UsePreviousValue=true ParameterKey=SiteUrl,UsePreviousValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```
*(Wait until stack status is `UPDATE_COMPLETE`)*

**[HUMAN]** Run AWS CloudFormation update for `spry-reports`:
```bash
aws cloudformation update-stack \
  --region eu-north-1 \
  --stack-name spry-reports \
  --template-body file://infra/reports.yml \
  --parameters ParameterKey=DatabaseUrl,UsePreviousValue=true ParameterKey=BuilderImageUri,UsePreviousValue=true ParameterKey=VpcId,UsePreviousValue=true ParameterKey=PrivateSubnetIds,UsePreviousValue=true ParameterKey=PrivateRouteTableIds,UsePreviousValue=true ParameterKey=LambdaSecurityGroupId,UsePreviousValue=true ParameterKey=SenderEmail,UsePreviousValue=true ParameterKey=RecipientEmails,UsePreviousValue=true ParameterKey=ProjectName,UsePreviousValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```
*(Wait until stack status is `UPDATE_COMPLETE`)*

**[HUMAN]** Run AWS CloudFormation update for `spry-ai`:
```bash
aws cloudformation update-stack \
  --region eu-north-1 \
  --stack-name spry-ai \
  --template-body file://infra/ai.yml \
  --parameters ParameterKey=ParserImageUri,UsePreviousValue=true ParameterKey=SiteUrl,UsePreviousValue=true ParameterKey=UserPoolId,UsePreviousValue=true ParameterKey=UserPoolClientId,UsePreviousValue=true ParameterKey=CognitoRegion,UsePreviousValue=true ParameterKey=ParserModel,UsePreviousValue=true ParameterKey=MockAi,UsePreviousValue=true ParameterKey=ProjectName,UsePreviousValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```
*(Wait until stack status is `UPDATE_COMPLETE`)*

### 2. Verify Retain Policy in AWS Console:
**[HUMAN]** Open CloudFormation in AWS Console (`eu-north-1`). Inspect the "Resources" tab of each stack (`spry-auth`, `spry-reports`, `spry-ai`) and verify that every resource has `Deletion Policy: Retain`.

### 3. Delete the CloudFormation stacks:
Since `DeletionPolicy: Retain` is set on every resource, deleting the CloudFormation stacks only deletes the CloudFormation stack metadata; the underlying AWS resources (Cognito, S3 bucket, Lambdas, SQS, IAM roles, etc.) remain untouched and fully running.

**[HUMAN]** Delete the three stacks:
```bash
aws cloudformation delete-stack --region eu-north-1 --stack-name spry-auth
aws cloudformation delete-stack --region eu-north-1 --stack-name spry-reports
aws cloudformation delete-stack --region eu-north-1 --stack-name spry-ai
```
*(Wait until all three stacks reach `DELETE_COMPLETE` in the AWS console)*

---

## Step 3b: Confirm `imports.tf` Resource IDs

Verify that the IDs configured in `infra/imports.tf` match the live AWS resources:

| Terraform Resource Address | AWS Resource Physical ID | Verification Command |
|---|---|---|
| `aws_cognito_user_pool.users` | `eu-north-1_VArufRzST` | `aws cognito-idp list-user-pools --max-results 10 --region eu-north-1` |
| `aws_cognito_identity_provider.google` | `eu-north-1_VArufRzST:Google` | `aws cognito-idp describe-identity-provider --user-pool-id eu-north-1_VArufRzST --provider-name Google --region eu-north-1` |
| `aws_cognito_user_pool_client.web` | `eu-north-1_VArufRzST/40q78hb988egmd17hs07hci1vh` | `aws cognito-idp describe-user-pool-client --user-pool-id eu-north-1_VArufRzST --client-id 40q78hb988egmd17hs07hci1vh --region eu-north-1` |
| `aws_cognito_user_pool_domain.domain` | `spry-sofiia` | `aws cognito-idp describe-user-pool-domain --domain spry-sofiia --region eu-north-1` |
| `aws_cognito_managed_login_branding.branding` | `eu-north-1_VArufRzST,6e1ea8e1-4795-41d6-ade8-7ad8cdfd2b64` | `aws cognito-idp describe-managed-login-branding --user-pool-id eu-north-1_VArufRzST --region eu-north-1` |
| `aws_s3_bucket.reports` | `spry-reports-545769669518` | `aws s3api head-bucket --bucket spry-reports-545769669518 --region eu-north-1` |
| `aws_s3_bucket_public_access_block.reports` | `spry-reports-545769669518` | `aws s3api get-public-access-block --bucket spry-reports-545769669518 --region eu-north-1` |
| `aws_s3_bucket_lifecycle_configuration.reports` | `spry-reports-545769669518` | `aws s3api get-bucket-lifecycle-configuration --bucket spry-reports-545769669518 --region eu-north-1` |
| `aws_vpc_endpoint.s3` | `vpce-01808a1ce5f8eeea8` | `aws ec2 describe-vpc-endpoints --vpc-endpoint-ids vpce-01808a1ce5f8eeea8 --region eu-north-1` |
| `aws_sqs_queue.dlq` | `https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests-dlq` | `aws sqs get-queue-attributes --queue-url https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests-dlq --attribute-names QueueArn --region eu-north-1` |
| `aws_sqs_queue.requests` | `https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests` | `aws sqs get-queue-attributes --queue-url https://sqs.eu-north-1.amazonaws.com/545769669518/spry-report-requests --attribute-names QueueArn --region eu-north-1` |
| `aws_lambda_event_source_mapping.builder` | `9af8cda3-d44f-47ce-a31c-437faac136f1` | `aws lambda get-event-source-mapping --uuid 9af8cda3-d44f-47ce-a31c-437faac136f1 --region eu-north-1` |
| `aws_iam_role.builder` | `spry-reports-BuilderRole-kmMmHDKBxIGt` | `aws iam get-role --role-name spry-reports-BuilderRole-kmMmHDKBxIGt` |
| `aws_lambda_function.builder` | `spry-report-builder` | `aws lambda get-function --function-name spry-report-builder --region eu-north-1` |
| `aws_iam_role.scheduler` | `spry-reports-SchedulerRole-IY98j7Hlhb3Y` | `aws iam get-role --role-name spry-reports-SchedulerRole-IY98j7Hlhb3Y` |
| `aws_scheduler_schedule.weekly` | `default/spry-weekly-report` | `aws scheduler get-schedule --name spry-weekly-report --region eu-north-1` |
| `aws_iam_role.mailer` | `spry-reports-MailerRole-PEgFa4yIMAc0` | `aws iam get-role --role-name spry-reports-MailerRole-PEgFa4yIMAc0` |
| `aws_lambda_function.mailer` | `spry-report-mailer` | `aws lambda get-function --function-name spry-report-mailer --region eu-north-1` |
| `aws_ses_email_identity.sender` | `zavada.sofia@gmail.com` | `aws sesv2 get-email-identity --email-identity zavada.sofia@gmail.com --region eu-north-1` |
| `aws_iam_role.parser` | `spry-agenda-parser-role` | `aws iam get-role --role-name spry-agenda-parser-role` |
| `aws_lambda_function.parser` | `spry-agenda-parser` | `aws lambda get-function --function-name spry-agenda-parser --region eu-north-1` |
| `aws_lambda_function_url.parser` | `spry-agenda-parser` | `aws lambda get-function-url-config --function-name spry-agenda-parser --region eu-north-1` |

> **Note on Non-Imported Child Resources**:
> - `aws_lambda_permission.mailer` & `aws_s3_bucket_notification.reports`: Not imported. Terraform creates them fresh cleanly and idempotently, resolving the legacy CFN circular dependency.
> - `aws_lambda_permission.function_url` & `aws_lambda_permission.invoke`: Not imported. Safely recreated fresh by Terraform to grant public access to the agenda parser Lambda URL.

---

## Step 3c: Run Plan and Apply in HCP Terraform

1. **Commit and Push branch**:
   **[HUMAN]** Commit the migration branch and push to GitHub:
   ```bash
   git checkout -b migrate/terraform-infra
   git add infra/ Makefile README.md docs/adr/0007-terraform.md .gitignore
   git commit -m "feat(infra): migrate auth, reports, ai from CloudFormation to Terraform"
   git push origin migrate/terraform-infra
   ```

2. **Trigger Plan in HCP Terraform**:
   - Open a Pull Request from `migrate/terraform-infra` to `main`.
   - HCP Terraform will run a speculative plan.
   - Or run locally via CLI:
     ```bash
     make infra-plan
     ```
   - **Review Plan output carefully**:
     Verify that the plan shows:
     ```
     Plan: 22 to import, 4 to add, 0 to change, 0 to destroy.
     ```
     *(4 to add are the fresh child permission/notification resources: `aws_lambda_permission.mailer`, `aws_s3_bucket_notification.reports`, `aws_lambda_permission.function_url`, `aws_lambda_permission.invoke`).*
     
     > **CRITICAL RULE**: If you see `# forces replacement` or `-/+` on `aws_cognito_user_pool.users` or `aws_s3_bucket.reports`, **STOP IMMEDIATELY**. Do not proceed with apply!

3. **Merge Pull Request**:
   **[HUMAN]** Merge the Pull Request to `main`.
   This triggers a Run in the `spry-dev` workspace on HCP Terraform.

4. **Confirm Apply in HCP Terraform**:
   **[HUMAN]** In HCP Terraform Console (`SprySZ / spry-dev`), review the plan and click **Confirm & Apply**.
   Wait for the run status to display `Apply finished`. Take a screenshot for project documentation.

5. **Verify Clean Plan**:
   **[HUMAN]** Run plan again (either in HCP Terraform or via `make infra-plan`):
   Verify that it reports:
   ```
   No changes. Your infrastructure matches the configuration.
   ```

---

## Cleanup (Post-Migration)

Once the initial apply completes with `Apply finished` and `No changes`:

1. **[HUMAN]** Remove the temporary import blocks:
   ```bash
   rm infra/imports.tf
   ```

2. **[HUMAN]** Remove the deprecated CloudFormation templates:
   ```bash
   rm infra/auth.yml infra/reports.yml infra/ai.yml
   ```

3. **[HUMAN]** Commit and merge the cleanup:
   ```bash
   git add infra/
   git commit -m "chore(infra): cleanup temporary imports and legacy CloudFormation templates"
   git push origin main
   ```
4. Verify HCP Terraform runs the clean plan with `No changes`.
