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

## Google Cloud (Lab 9)

The core of Spry (frontend, API, database) also runs on Google Cloud, in project `spry-sofiia-2026`, region `us-central1`. Decisions are in [ADR 0009](docs/adr/0009-google-cloud.md). Costs and answers are in [docs/lab9-answers.md](docs/lab9-answers.md).

```
Browser ──HTTPS──▶ Firebase Hosting (static build)
                    └─ /api/** rewrite ──▶ Cloud Run spry-api (min 0, as SA spry-api)
                                            └─ Cloud SQL connector ──▶ Cloud SQL spry-db (PostgreSQL 16, db-f1-micro)
                                                DB password: Secret Manager spry-db-password
```

| Piece | Runs on |
|---|---|
| Frontend, API, database | **Google Cloud** (`gcp/`, workspace `spry-gcp`) |
| Sign-in (Cognito), weekly report (Scheduler → SQS → Lambda → S3 → SES), agenda parser (Lambda → Bedrock) | **AWS** (`infra/`, workspace `spry-dev`) |

The GCP copy has its own data. Sign-in and "Parse with AI" from `*.web.app` need the Firebase origin added to the Cognito callback URLs and the parser CORS in `infra/`; this is not done yet.

### First-time setup (once)
1. Install `gcloud` (`brew install --cask google-cloud-sdk`). Create the project, link billing, and **create a budget alert** (Billing → Budgets & alerts, e.g. $5).
2. `gcloud auth login && gcloud auth application-default login`. Your own account, through ADC. **No service account keys.**
3. `terraform -chdir=gcp init` creates the HCP workspace `spry-gcp`. In HCP, connect it to this GitHub repo (VCS) with working directory `gcp`, as `spry-dev` uses `infra`. Note its ID (`ws-…`) and the organization ID (`org-…`).
4. Put both IDs in `gcp/bootstrap/terraform.tfvars`. Run `terraform -chdir=gcp/bootstrap init`, set workspace `spry-gcp-bootstrap` to **Local** execution in HCP, then `make gcp-bootstrap`. This creates the service accounts `spry-terraform` and `spry-api`, their roles, Workload Identity Federation for HCP Terraform, and Firebase.
5. In workspace `spry-gcp`, add **environment** variables from the bootstrap outputs: `TFC_GCP_PROVIDER_AUTH=true`, `TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL=<terraform_service_account>`, `TFC_GCP_WORKLOAD_PROVIDER_NAME=<workload_provider_name>`.

### Deploy
1. **Infrastructure:** PR → speculative plan in `spry-gcp` → merge → apply. The first apply runs Google's `hello` image on Cloud Run.
2. **API image:** `make gcp-push-api`, then paste the printed `api_image = "...@sha256:..."` into `gcp/terraform.tfvars`, and PR → apply. Migrations run on container start (`alembic upgrade head`).
3. **Demo data:** `make gcp-seed`.
4. **Frontend:** `make auth-env && make gcp-deploy-frontend` (Firebase CLI; run `npx firebase-tools login` once if it asks).
5. **Check:** `make gcp-smoke`, then open `https://spry-sofiia-2026.web.app` in a private window.

### Stop the database (Cloud SQL does not pause)
```bash
make gcp-db-stop     # activation policy NEVER: compute stops billing
make gcp-db-start    # back on; takes about a minute
make gcp-db-status
```
A stopped instance **still bills storage ($1.70) and its idle public IPv4 ($0.01/h ≈ $7.30/month)**, so stopping saves little. To stop paying, delete it: `terraform destroy` in the `spry-gcp` workspace (Settings → Destruction and Deletion) removes everything `gcp/` created. Delete BigQuery demo tables too, and check *Billing → Reports* a day later.

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
| `make gcp-push-api` | Builds the backend for Cloud Run, pushes it to Artifact Registry, prints the digest |
| `make gcp-deploy-frontend` | Builds the frontend and deploys it to Firebase Hosting |
| `make gcp-db-stop` / `gcp-db-start` | Stops or starts the Cloud SQL instance |
| `make gcp-seed` / `gcp-smoke` | Adds demo meetings / checks frontend + one DB-reading API call on GCP |
