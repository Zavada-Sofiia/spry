# Spry

Spry is a modern team calendar and meeting management application featuring automated weekly meeting reports and AI-assisted agenda parsing.

---

## Infrastructure Management with Terraform

Infrastructure for Spry's supplementary services (Cognito Authentication, S3/SQS/SES Weekly Reports pipeline, and Bedrock AI Agenda Parser) is managed as code using **Terraform** and deployed via **HCP Terraform** (Terraform Cloud).

- **HCP Organization**: `SprySZ`
- **HCP Workspace**: `spry-dev` (Working Directory: `infra`)
- **AWS Region**: `eu-north-1`
- **Architecture Decision Record**: [ADR 0007: Migration from CloudFormation to Terraform](file:///Users/sofiia_zavada/spry/docs/adr/0007-terraform.md)
- **Detailed Answers to Lab 7 Questions**: [docs/lab7-answers.md](file:///Users/sofiia_zavada/spry/docs/lab7-answers.md)
- **Submission Pack**: [SUBMISSION.md](file:///Users/sofiia_zavada/spry/SUBMISSION.md)

### How Infrastructure Changes are Deployed

1. **Pull Request & Speculative Plan**:
   - Any modification to `infra/*.tf` is submitted via a Git pull request against `main`.
   - HCP Terraform automatically triggers a speculative `terraform plan` and reports the results back to the pull request checks.
   - Engineers can also test and verify plans locally using:
     ```bash
     make infra-plan
     ```
2. **Review & Merge**:
   - The pull request is reviewed by team members.
   - Once approved, the branch is merged into `main`.
3. **Remote Apply in HCP Terraform**:
   - The merge to `main` triggers a live deployment in HCP Terraform.
   - HCP Terraform executes the plan using credentials configured in the workspace (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` for the dedicated `spry-dev` project user, as OIDC provider creation is restricted by organization SCP `p-bpbjw0fa`).
   - The plan is reviewed and confirmed in the HCP Terraform console.
   - **Local workstations never run `terraform apply`.**

### Which Runs First: Infrastructure vs. Application Deployments?

When a feature requires both infrastructure changes (e.g., a new SQS queue, a new S3 bucket, or a new Lambda environment variable) and application code updates:

- **Infrastructure MUST always be deployed first**:
  - The application code will crash or fail at runtime if it references a resource, queue URL, bucket, or environment variable that does not yet exist in AWS.
  - Terraform creates the infrastructure and establishes the necessary IAM permissions first. Once the infrastructure run succeeds, the application deployment can safely roll out and reference the new infrastructure.
- **Application Deployment Location**:
  - The application backend (`spry-backend-service` in ECS) and frontend are deployed directly via Makefile commands (`make deploy-backend`, `make deploy-frontend`), which build and push container images / bundles to AWS. There is no automated GitHub Actions CI/CD workflow committed in this repository; application deploys are operated via Makefile or external administrative scripts.

### Secret Handling

- **Zero Secrets in Code**: Secrets and cloud credentials are never committed to the repository, `terraform.tfvars`, or documentation.
- **Sensitive Variables**: Secrets (such as `google_client_secret` and `database_url`) are defined in `infra/variables.tf` as `sensitive = true` without defaults.
- **HCP Terraform Storage**: Secrets and AWS execution credentials are populated exclusively within HCP Terraform workspace variables marked as **Sensitive**. While Terraform state (`.tfstate`) records the resolved values for managed resources in plaintext JSON, the state file resides securely in HCP Terraform's encrypted backend (AES-256) and is never checked into source control.
- **Downstream Exposure**:
  - `google_client_secret` is stored within the AWS Cognito service configuration.
  - `database_url` is stored in the Lambda environment variables of `spry-report-builder`.
  - Static AWS access keys for `spry-dev` are stored as Sensitive workspace environment variables in HCP Terraform and must be rotated after grading.

---

## Local Development & Operations

### Developer Quickstart

1. Start all local services via Docker Compose:
   ```bash
   docker compose up
   ```
2. The frontend runs at `http://localhost:3000` and the backend API runs at `http://localhost:8000`.

### Useful Makefile Commands

| Command | Description |
|---|---|
| `make infra-plan` | Runs `terraform -chdir=infra plan` against HCP Terraform |
| `make auth-env` | Generates `frontend/.env.production` from Terraform stack outputs |
| `make report-now WEEK=2026-W39` | Sends a manual report trigger to the SQS queue read from Terraform |
| `make parse TEXT="..."` | Parses an unstructured meeting agenda locally using Bedrock |
| `make deploy-frontend` | Builds and syncs frontend assets to S3 and invalidates CloudFront |
| `make deploy-backend` | Builds and pushes backend container to ECR and updates ECS service |
