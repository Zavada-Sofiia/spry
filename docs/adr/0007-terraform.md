# ADR 0007: Migration from CloudFormation to Terraform with HCP Terraform

## Status
Draft, to be reviewed by a human

## Context
Spry previously managed its supplementary AWS infrastructure—Cognito authentication (Lab 4, `infra/auth.yml`), the weekly reports pipeline (Lab 5, `infra/reports.yml`), and the Bedrock AI agenda parser (Lab 6, `infra/ai.yml`)—via AWS CloudFormation stacks.

While functional, managing infrastructure through disparate CloudFormation templates introduced operational friction:
- **Circular Dependencies**: CloudFormation struggled with interdependent resources (e.g., S3 bucket notifications triggering a Lambda function that references the bucket), requiring manual workarounds.
- **Drift & Preview**: CloudFormation change sets are slow to generate and difficult to preview in pull requests.
- **Adoption Complexity**: Importing pre-existing AWS resources into running CloudFormation stacks requires brittle template synchronization and complex import operations.

We require a modern Infrastructure as Code (IaC) workflow that allows safe, previewable, and zero-downtime infrastructure changes.

## Decision
We adopt **Terraform** (>= 1.10) managed via **HCP Terraform** (Terraform Cloud) for `infra/`:
1. **Remote Execution & State**: HCP Terraform organization `SprySZ`, workspace `spry-dev` with Remote execution mode and `infra` as the working directory.
2. **AWS Authentication & SCP Fallback**: The original architectural target was dynamic OIDC credentials (`app.terraform.io` audience `aws.workload.identity`). However, the AWS Organization enforces a Service Control Policy (SCP `p-bpbjw0fa`) that explicitly denies `iam:CreateOpenIDConnectProvider` for student IAM accounts. Consequently, runner authentication in HCP Terraform utilizes dedicated IAM user credentials for `spry-dev` stored as **Sensitive** environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).
3. **Existing Resources Adopted**: All existing AWS resources from the three CloudFormation stacks were retained (`DeletionPolicy: Retain`) and cleanly adopted into Terraform state using declarative `import` blocks.
4. **Core Stacks Remain CloudFormation**: Baseline course infrastructure (network, VPC, database, ECS cluster) remains managed by CloudFormation; Terraform reads any necessary attributes via variables or data sources.

---

### 1. Why Terraform (and not CloudFormation, CDK, or OpenTofu)?
- **Over CloudFormation**: Terraform AWS Provider (v6.x) cleanly decomposes monolithic resources (such as decomposing an S3 bucket into `aws_s3_bucket`, `aws_s3_bucket_lifecycle_configuration`, `aws_s3_bucket_public_access_block`, and `aws_s3_bucket_notification`), eliminating the circular dependency that plagued Lab 5. Furthermore, declarative `import` blocks enable safe resource adoption without stack recreation.
- **Over AWS CDK**: CDK introduces an extra layer of code synthesis (TypeScript/Python compiling down to CloudFormation), inheriting all underlying CloudFormation limitations, slow rollback failures, and deployment opacity. Terraform provides a single declarative abstraction with direct API mappings.
- **Over OpenTofu**: While OpenTofu is open-source, HCP Terraform provides a fully managed remote state backend, turnkey speculative pull request plans, and managed workspace variables out of the box without requiring the team to self-host and maintain an S3 state bucket, DynamoDB lock table, and custom CI/CD runners.

### 2. Who changes infrastructure now, and how?
- **Workflow**:
  1. An engineer makes infrastructure changes on a feature branch in `infra/*.tf`.
  2. Opening a GitHub Pull Request triggers an automated **speculative plan** in HCP Terraform via GitHub VCS integration.
  3. Engineers review the exact resource diff in the PR discussion. Local plans can be run via `make infra-plan`.
  4. Merging the PR into `main` triggers a live run in the `spry-dev` workspace on HCP Terraform.
  5. The change is reviewed and applied in HCP Terraform.
- **Access Control**: Engineers do not run `terraform apply` locally. Direct workstation access to AWS is limited to read-only queries and testing. Infrastructure modifications are strictly mediated by git review and HCP Terraform.

### 3. Where do secrets end up, state included?
- **Application & Database Secrets**: Secrets (`google_client_secret`, `database_url`) are defined in `variables.tf` with `sensitive = true` and no default values. They are populated exclusively inside HCP Terraform workspace variables marked as **Sensitive**.
- **State File Reality**: Marking a Terraform variable `sensitive = true` prevents the secret from appearing in console logs, plan outputs, and PR comments. **However, Terraform state (`.tfstate`) always stores raw attribute values in plaintext JSON.** Consequently, `google_client_secret` and `database_url` are present in plaintext inside the `.tfstate` and in every historical state version retained in HCP Terraform.
- **Downstream AWS Services**:
  - `google_client_secret` is stored in the AWS Cognito User Pool Identity Provider configuration. Anyone with `cognito-idp:DescribeUserPoolIdentityProvider` API access can retrieve it. Note: `infra/auth.tf` sets `lifecycle { ignore_changes = [provider_details, attribute_mapping] }` to prevent Cognito metadata drift; this also means updating `google_client_secret` via Terraform requires manually updating Cognito or temporarily removing `ignore_changes`.
  - `database_url` is stored in the Lambda environment variables of `spry-report-builder`. Anyone with `lambda:GetFunctionConfiguration` or AWS Console access can view it in plaintext.
- **AWS Runner Credentials**: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` reside in HCP Terraform workspace environment variables marked as **Sensitive**. They are consumed in-memory by the Linux execution runner and are **not** written to the state file.
- **Protection**: State files are never stored locally and are excluded from git via `.gitignore`. The state is stored in HCP Terraform, encrypted at rest (AES-256 with HashiCorp Vault-managed keys) and in transit (TLS 1.3). Workspace access is restricted to authenticated team members.

### 4. What happens if HCP Terraform is down?
- **Running Infrastructure**: Zero impact. All deployed AWS resources (Cognito, S3, Lambdas, SQS, SES) run completely independently in AWS and do not maintain an active connection to HCP Terraform.
- **Deployments**: Infrastructure updates and pull request speculative plans will pause while HCP Terraform is unavailable.
- **Break-Glass Emergency Procedure**: If an urgent change is required during an extended HCP outage:
  1. An authorized operator configures local credentials with temporary administrative AWS access.
  2. Set workspace execution mode to Local (or download the latest state snapshot from HCP Terraform).
  3. Execute emergency `terraform plan` / `terraform apply` locally, documenting the incident and exact rationale.
  4. Once HCP Terraform recovers, push the updated state back to HCP Terraform and restore Remote execution mode.

---

## Consequences & Technical Trade-offs

### Security: Static Credentials vs. Dynamic OIDC
- **Security Downgrade**: Because SCP `p-bpbjw0fa` blocks `iam:CreateOpenIDConnectProvider` for student accounts, long-lived IAM access keys for `spry-dev` are stored in HCP Terraform instead of short-lived OIDC tokens.
- **Mitigations in Place**:
  - Dedicated IAM user (`spry-dev`) used exclusively for HCP Terraform automation, avoiding personal engineer credentials.
  - User permissions scoped down to project resources.
  - Access keys must be rotated and invalidated upon course evaluation completion.
- **Target State (OIDC)**: Once centralized organization administrators register the `app.terraform.io` OIDC provider, static keys should be replaced with dynamic credentials. The IAM role trust condition will be constrained by workspace:
  ```json
  "StringEquals": {
    "app.terraform.io:aud": "aws.workload.identity",
    "app.terraform.io:sub": "organization:SprySZ:project:Default:workspace:spry-dev:run_phase:*"
  }
  ```
  *(Note: HCP Terraform's OIDC `sub` claim does not include the Git branch; workspace-level scoping is the official mechanism for environment isolation).*

### Migration Side Effects & Corrections
- **Initial Apply Discrepancies**: During the initial import apply (PR #2), 15 resources were modified. Beyond `default_tags` additions, 5 functional parameters drifted from pre-migration CloudFormation templates:
  1. `max_message_size` on SQS queues (`requests` and `dlq`): dropped from 1048576 (1 MB) to Terraform AWS provider default 262144 (256 KB).
  2. `MOCK_AI` on `spry-agenda-parser`: inadvertently set to `"false"`, invoking Amazon Bedrock Mantle.
  3. `image_uri` on `spry-report-builder`: shifted from pinned digest `@sha256:1cd862...` to `:latest`.
  4. `target.input` on `aws_scheduler_schedule.weekly`: keys reordered by `jsonencode`.
  - **Correction**: Branch `fix/migration-parity` (PR #3) restored all 5 parameters to exact pre-migration parity with 0 additions and 0 destructions.
- **Residual Lambda Permissions**: Retaining Lambda functions during CloudFormation stack deletion (`DeletionPolicy: Retain`) left legacy statement IDs in function resource policies (`spry-reports-MailerInvokePermission-imvAfxvqJLpn`, `spry-ai-ParserFunctionUrlPermission-sUQKWhTdgMgm`, etc.) alongside Terraform's newly created statements (`AllowS3Invoke`, `FunctionURLAllowPublicAccess`, `AllowPublicInvoke`).
  - **Correction**: Legacy duplicate statements were safely removed using `aws lambda remove-permission`. Subsequent plan runs confirmed `No changes. Your infrastructure matches the configuration.`

### State Reconciliation
- Total items in HCP Terraform state widget: **28** (consisting of **26 managed `aws_*` resources** and **2 tracked data sources**: `data.archive_file.mailer_zip` and `data.aws_caller_identity.current`).
