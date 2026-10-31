# Lab 7: Supplementary Infrastructure Migration Answers & Discussion

This document contains detailed engineering answers to the Lab 7 Step 7 questions, drift demonstration documentation, and architectural discussion topics for the Spry project.

---

## Part 1: Step 7 Answers (Specific to Spry Infrastructure)

### 1. Resource Reconciliation: 22 Imported vs. 4 Created Fresh
- **CloudFormation Baseline**: The original supplementary stacks (`auth.yml`, `reports.yml`, `ai.yml`) contained 23 logical CloudFormation resources.
- **Decomposition in Terraform**: In Terraform AWS Provider v6.x, monolithic resources are decomposed into independent child resources (specifically, the S3 bucket's inline configurations).
- **Imported (22 Resources)**:
  - 20 resources directly mapped from CloudFormation (Cognito User Pool, Client, Domain, IdP, Branding, S3 Bucket, VPC Endpoint, 2 SQS queues, EventSourceMapping, Builder IAM Role, Builder Lambda, Scheduler IAM Role, Weekly Schedule, Mailer IAM Role, Mailer Lambda, SES Email Identity, Parser IAM Role, Parser Lambda, Parser Function URL).
  - 2 decomposed S3 resources imported cleanly: `aws_s3_bucket_public_access_block.reports` and `aws_s3_bucket_lifecycle_configuration.reports`.
- **Created Fresh (4 Resources)**:
  - `aws_s3_bucket_notification.reports`: Created fresh to decouple bucket configuration from Lambda permissions, cleanly eliminating the CloudFormation circular dependency from Lab 5.
  - `aws_lambda_permission.mailer`: Created fresh (`AllowS3Invoke`) to authorize S3 to invoke the mailer Lambda.
  - `aws_lambda_permission.function_url`: Created fresh (`FunctionURLAllowPublicAccess`) to permit public unauthenticated invocation of the parser Function URL.
  - `aws_lambda_permission.invoke`: Created fresh (`AllowPublicInvoke`) for Lambda invoke permissions.
- **Why Re-creation was Safe**:
  - `aws_s3_bucket_notification` is a purely declarative AWS API call against the pre-existing bucket and does not modify stored report files.
  - `aws_lambda_permission` statements are idempotent IAM resource policies. Adding them with distinct statement IDs (`Sid`) does not interrupt running functions, delete compute resources, or cause downtime.

### 2. Attributes Forcing Replacement
- **On Cognito User Pool (`aws_cognito_user_pool.users`)**:
  - Changing the `name` attribute or immutable schema properties (such as `username_attributes = ["email"]`).
  - **Consequence**: The existing user pool is destroyed and recreated with a new pool ID. **All registered user accounts, passwords, federated OAuth links, and active authentication tokens are permanently destroyed.**
- **On Reports Bucket (`aws_s3_bucket.reports`)**:
  - Changing the `bucket` name.
  - **Consequence**: S3 bucket names are globally unique and immutable. Terraform will attempt to destroy the old bucket. Because AWS forbids deleting non-empty buckets, the apply will fail unless force-destroyed—which would **permanently delete all historical weekly CSV reports**.
- **On Cognito Client (`aws_cognito_user_pool_client.web`)**:
  - Altering `generate_secret` (transitioning between `false`/null and `true`).
  - **Consequence**: Forces creation of a new Client ID, breaking the frontend single-page application until reconfigured and rebuilt.

### 3. Every Location Where Google Client Secret is Stored or Shown
1. **HCP Terraform Workspace Variables**: Stored encrypted in HashiCorp Vault, marked `Sensitive`, masked in UI. Leaked by workspace admins or users with variable edit access.
2. **Terraform State File (`.tfstate`) in HCP**: **Stored in plaintext JSON.** Anyone with state read/download access in HCP Terraform can view the raw secret.
3. **State Version History in HCP**: Every historical `.tfstate` revision retains the secret in plaintext.
4. **AWS Cognito Service**: Passed via AWS API and stored in the User Pool Identity Provider configuration. Anyone with `cognito-idp:DescribeUserPoolIdentityProvider` permission in AWS can read the secret via AWS Console or CLI.
5. **Runner Memory**: Present in Linux process memory during plan/apply execution.
*(Note: `infra/auth.tf` sets `ignore_changes = [provider_details, attribute_mapping]`. This prevents ongoing drift from Cognito metadata but means changes to the secret in HCP variables are ignored by Terraform after initial creation).*

### 4. Concurrent Applies: Remote State vs. Local `.tfstate` in Git
- **Remote State in HCP Terraform**:
  - Uses centralized **State Locking** and a sequential **Run Queue**.
  - When Run A starts planning or applying, HCP locks the workspace state. If Run B is triggered simultaneously, it is placed in `Queued` status. Run B cannot execute until Run A releases the lock, at which point Run B refreshes state before applying. Race conditions and state corruption are prevented completely.
- **Local State in Git (Anti-Pattern)**:
  - If two engineers run `terraform apply` locally and commit `.tfstate` to Git, Git cannot intelligently merge JSON state files.
  - One engineer's commit will overwrite the other's state, leading to **orphaned cloud resources** (resources created in AWS but deleted from state) or accidental destructions.
  - Committing `.tfstate` to Git exposes raw database passwords, tokens, and OAuth secrets in Git commit history.

### 5. Narrower OIDC Trust Policy and Permissions
- **Trust Condition Constraint**:
  HCP Terraform's OIDC subject claim format is:
  `organization:<ORG>:project:<PROJECT>:workspace:<WORKSPACE>:run_phase:<PHASE>`
  **The `sub` claim does NOT include the Git branch.** Restricting by branch directly in the IAM trust policy is impossible. The narrowest possible condition scopes access to the project and workspace:
  ```json
  "Condition": {
    "StringEquals": {
      "app.terraform.io:aud": "aws.workload.identity",
      "app.terraform.io:sub": "organization:SprySZ:project:Default:workspace:spry-dev:run_phase:*"
    }
  }
  ```
- **Real Permissions Needed (Least Privilege)**:
  - `s3:*` on `arn:aws:s3:::spry-reports-545769669518` (bucket configuration, notifications, lifecycle).
  - `sqs:*` on `arn:aws:sqs:eu-north-1:545769669518:spry-report-requests*`.
  - `lambda:*` on `arn:aws:lambda:eu-north-1:545769669518:function:spry-*`.
  - `cognito-idp:*` on `arn:aws:cognito-idp:eu-north-1:545769669518:userpool/*`.
  - `scheduler:*` on `arn:aws:scheduler:eu-north-1:545769669518:schedule/default/spry-weekly-report`.
  - `ses:*` on `arn:aws:ses:eu-north-1:545769669518:identity/zavada.sofia@gmail.com`.
  - `ec2:*` for S3 Gateway Endpoint routing (`DescribeVpcEndpoints`, `ModifyVpcEndpoint`).
  - Scoped `iam:*` (`GetRole`, `PassRole`, `CreateRole`, `PutRolePolicy`) restricted to roles prefixed with `spry-*`.

### 6. Staging Environment with Claude Code
- **What Claude Code SHOULD Produce**:
  - A feature branch containing `infra/environments/staging.tfvars` with non-colliding resource names (`spry-staging-*`).
  - Code changes creating or parametrizing modules for multi-environment deployment.
  - A Pull Request with an automated speculative plan for human engineering review.
- **What Claude Code Must NEVER Do**:
  - Never execute `terraform apply` directly.
  - Never modify or delete production state files.
  - Never use administrator credentials or bypass organization SCPs.
  - Never auto-merge pull requests into `main`.
  - Never access or deploy against the production workspace (`spry-prod`).

---

## Part 2: Drift Demonstration (Step 5)

### Procedure
1. In the AWS Lambda Console, manually update the `spry-agenda-parser` configuration (e.g., increase `Timeout` from 30 seconds to 45 seconds).
2. Trigger a speculative `Plan only` run in HCP Terraform (`make infra-plan` or HCP Console).
3. **Observation**: Terraform detects configuration drift between the real cloud resource and the HCL code, displaying `~ update in-place` proposing to revert `timeout` from 45 back to 30.
4. **Screenshot Placeholder**:
   ```
   [PLACEHOLDER: Insert screenshot of HCP Terraform Drift Plan showing ~ timeout = 45 -> 30]
   ```

### Operational Question: The 23:00 Emergency Console Fix
*If a production outage occurs at 23:00 and an engineer changes an AWS setting directly in the AWS Console to restore service, what must the team do next?*
- **Answer**: Making an emergency change in the console during a sev-1 incident is acceptable for rapid recovery, but the fix is incomplete. The engineer must immediately open a Pull Request updating the HCL code in Git to match the emergency configuration. If the code is not updated, the next routine merge or pipeline run will detect drift and revert the emergency fix back to the old failing state. In GitOps, **Git remains the single authoritative source of truth**.

---

## Part 3: Discussion Questions

1. **Undocumented Lambda Found in Cloud Account**:
   Inspect CloudWatch logs and tags to identify the function's owner and traffic. If it is active and belongs to the application, adopt it into Terraform using an `import` block. If it is an abandoned test artifact, delete it after confirmation. If it is owned by another team, document it in the architectural README as an external dependency and do not touch it in Terraform.

2. **Console Fix Before Product Launch**:
   Hotfixing via console right before launch risks silent regressions on subsequent automated deployments. If a last-minute console fix is unavoidable, immediately backport the change to HCL in a pull request and run a speculative plan to ensure zero drift before launch.

3. **State Management: CloudFormation vs. Terraform**:
   - *CloudFormation*: State is managed transparently on AWS servers (no state locking or storage to manage), but it is slow, opaque, cannot easily decompose interdependent resources, and rollback failures can lock stacks.
   - *Terraform*: State is an explicit JSON representation decoupled from the cloud. This enables ultra-fast planning, modular resource composition, and declarative adoption, but requires managing remote state security and concurrency locking.

4. **What is Lost if the State File is Deleted?**:
   Deleting `.tfstate` does not delete resources in AWS; they continue running normally. However, Terraform loses all awareness of existing infrastructure. On the next plan, Terraform will attempt to recreate all 26 resources from scratch, causing duplicate creation errors, collision crashes (e.g. S3 bucket name already exists), or costly duplicate deployments.

5. **Why State Must NEVER be Committed to Git**:
   Terraform state files store all resource attributes—including database connection strings, passwords, and API secrets—in unencrypted plaintext JSON. Committing state to Git permanently exposes credentials in Git history and causes fatal concurrency race conditions without distributed state locking.

6. **Harmless-Looking Diff with a Dangerous Plan**:
   Renaming a resource block in HCL (e.g., changing `resource "aws_s3_bucket" "reports"` to `resource "aws_s3_bucket" "weekly_reports"` without a `moved` block) looks like a harmless refactoring. In the plan, Terraform interprets this as destroying the old bucket and creating a new empty one, permanently deleting all existing data.

7. **Uses of `-target` and `state rm`**:
   `-target` isolates execution to a single resource, useful for breaking chicken-and-egg dependency deadlocks during initial bootstrapping, but dangerous for regular use because it ignores dependency graphs. `state rm` removes a resource from Terraform tracking without issuing an API delete to AWS, useful when transferring resource ownership or decommissioning IaC.

8. **Automate vs. Never in the AI Agent Chain**:
   Automate read-only discovery, code refactoring, HCL generation, linting, formatting (`terraform fmt`), syntax validation, and speculative planning in pull requests. **NEVER automate live applies (`terraform apply`), state manipulation (`state rm/mv`), or administrative credential handling without explicit human authorization.**

9. **White-Label Architecture with Modules and Workspaces**:
   Package the core infrastructure into versioned, reusable Terraform modules (`module "spry_core"`). Create separate HCP Terraform workspaces for each customer tenant (`spry-customer-a`, `spry-customer-b`), each with its own state file, tenant-specific `terraform.tfvars`, and dedicated IAM boundaries.

10. **A Run Failing Halfway Through Apply**:
    Terraform writes every successfully provisioned resource to the state file immediately upon completion. If an apply fails on resource 15 of 26, the first 14 resources remain safely recorded in state. To recover, correct the failure in HCL and re-apply; Terraform resumes idempotently from resource 15 without touching the first 14.
