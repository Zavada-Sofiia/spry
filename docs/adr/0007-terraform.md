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
2. **Zero Hardcoded Credentials (OIDC)**: HCP Terraform authenticates to AWS via OpenID Connect (OIDC) assuming the dedicated role `arn:aws:iam::545769669518:role/spry-tfc-role`.
3. **Existing Resources Adopted**: All existing AWS resources from the three CloudFormation stacks are retained (`DeletionPolicy: Retain`) and cleanly adopted into Terraform state using declarative `import` blocks.
4. **Core Stacks Remain CloudFormation**: Baseline course infrastructure (network, VPC, database, ECS cluster) remains managed by CloudFormation; Terraform reads any necessary attributes via variables or data sources.

---

### 1. Why Terraform (and not CloudFormation, CDK, or OpenTofu)?
- **Over CloudFormation**: Terraform AWS Provider (v6.x) cleanly decomposes monolithic resources (such as decomposing an S3 bucket into `aws_s3_bucket`, `aws_s3_bucket_lifecycle_configuration`, `aws_s3_bucket_public_access_block`, and `aws_s3_bucket_notification`), eliminating the circular dependency that plagued Lab 5. Furthermore, declarative `import` blocks enable safe resource adoption without stack recreation.
- **Over AWS CDK**: CDK introduces an extra layer of code synthesis (TypeScript/Python compiling down to CloudFormation), inheriting all underlying CloudFormation limitations, slow rollback failures, and deployment opacity. Terraform provides a single declarative abstraction with direct API mappings.
- **Over OpenTofu**: While OpenTofu is open-source, HCP Terraform provides a fully managed remote state backend, turnkey speculative pull request plans, and managed OIDC credentials out of the box without requiring the team to self-host and maintain an S3 state bucket, DynamoDB lock table, and custom CI/CD runner runners.

### 2. Who changes infrastructure now, and how?
- **Workflow**:
  1. An engineer makes infrastructure changes on a feature branch in `infra/*.tf`.
  2. Opening a GitHub Pull Request triggers an automated **speculative plan** in HCP Terraform.
  3. Engineers review the exact resource diff in the PR discussion. Local plans can be run via `make infra-plan`.
  4. Merging the PR into `main` triggers a live run in the `spry-dev` workspace on HCP Terraform.
  5. The change is reviewed and applied in HCP Terraform (or auto-applied based on workspace configuration).
- **Access Control**: Engineers do not run `terraform apply` locally. Direct workstation access to AWS is limited to read-only queries and testing. Infrastructure modifications are strictly mediated by git review and HCP Terraform.

### 3. Where do secrets end up, state included?
- **Sensitive Variables**: Secrets (`google_client_secret`, `database_url`) are defined in `variables.tf` with `sensitive = true` and no default values. They are populated exclusively inside HCP Terraform workspace variables marked as **Sensitive**.
- **State File Reality**: Marking a variable `sensitive = true` prevents the secret from appearing in console logs, plan outputs, and PR comments. **However, Terraform state (`.tfstate`) always stores raw attribute values in plaintext JSON.**
- **Protection**: State files are never stored locally and are excluded from git via `.gitignore`. The state is stored in HCP Terraform, encrypted at rest (AES-256 with HashiCorp Vault-managed keys) and in transit (TLS 1.3). Workspace access is restricted to authenticated team members.

### 4. What happens if HCP Terraform is down?
- **Running Infrastructure**: Zero impact. All deployed AWS resources (Cognito, S3, Lambdas, SQS, SES) run completely independently in AWS and do not maintain an active connection to HCP Terraform.
- **Deployments**: Infrastructure updates and pull request speculative plans will pause while HCP Terraform is unavailable.
- **Break-Glass Emergency Procedure**: If an urgent change is required during an extended HCP outage:
  1. An authorized operator can configure local credentials with temporary administrative AWS access.
  2. Temporarily comment out the `cloud {}` block in `infra/versions.tf`.
  3. Download the last known state from HCP Terraform (or use the AWS provider to inspect live state) and run `terraform plan` / `terraform apply` locally.
  4. Once HCP Terraform recovers, reconcile the state and restore the `cloud {}` block.

---

## Consequences
- **Positive**:
  - Fine-grained control over AWS resources without CloudFormation circular dependency traps.
  - Transparent plan reviews directly in pull requests before anything changes in AWS.
  - No long-lived AWS IAM access keys stored in CI or developer machines (OIDC provider).
- **Negative / Operational Considerations**:
  - Requires maintaining the HCP Terraform workspace and OIDC trust policy.
  - State file inspection requires HCP Terraform permissions.
- **TODO(me)**: Confirm whether auto-apply or manual apply confirmation in HCP Terraform `spry-dev` workspace is preferred for merges to `main`.
