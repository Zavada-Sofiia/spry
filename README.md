# Spry

Spry is a modern team calendar and meeting management application featuring automated weekly meeting reports and AI-assisted agenda parsing.

---

## Infrastructure Management with Terraform

Infrastructure for Spry's supplementary services (Cognito Authentication, S3/SQS/SES Weekly Reports pipeline, and Bedrock AI Agenda Parser) is managed as code using **Terraform** and deployed via **HCP Terraform** (Terraform Cloud).

- **HCP Organization**: `SprySZ`
- **HCP Workspace**: `spry-dev` (Working Directory: `infra`)
- **AWS Region**: `eu-north-1`
- **Architecture Decision Record**: [ADR 0007: Migration from CloudFormation to Terraform](file:///Users/sofiia_zavada/spry/docs/adr/0007-terraform.md)
- **Migration Runbook**: [infra/MIGRATION_RUNBOOK.md](file:///Users/sofiia_zavada/spry/infra/MIGRATION_RUNBOOK.md)

### How Infrastructure Changes are Deployed

1. **Pull Request & Speculative Plan**:
   - Any modification to `infra/*.tf` is submitted via a Git pull request.
   - HCP Terraform automatically triggers a speculative `terraform plan` and reports the results back to the pull request.
   - Engineers can also test and verify plans locally using:
     ```bash
     make infra-plan
     ```
2. **Review & Merge**:
   - The pull request is reviewed by team members.
   - Once approved, the branch is merged into `main`.
3. **Remote Apply in HCP Terraform**:
   - The merge to `main` triggers a live deployment in HCP Terraform.
   - HCP Terraform executes the plan using credentials configured in the workspace (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` for the dedicated `spry-dev` project user, as OIDC provider creation is restricted by organization SCP).
   - The plan is reviewed and confirmed in the HCP Terraform console.
   - **Local workstations never run `terraform apply`.**

### Secret Handling

- **Zero Secrets in Code**: Secrets and cloud credentials are never committed to the repository, `terraform.tfvars`, or documentation.
- **Sensitive Variables**: Secrets (such as `google_client_secret` and `database_url`) are defined in `infra/variables.tf` as `sensitive = true` without defaults.
- **HCP Terraform Storage**: Secrets and AWS execution credentials are populated exclusively within HCP Terraform workspace variables marked as **Sensitive**. While Terraform state (`.tfstate`) records the resolved values for managed resources, the state file resides securely in HCP Terraform's encrypted backend (AES-256) and is never checked into source control or stored unencrypted on developer laptops.

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
