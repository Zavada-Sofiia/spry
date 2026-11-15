# ADR 0009: Running Spry's core on Google Cloud

## Status
Proposed (Lab 9). To be reviewed by a human.

## Context
Spry runs on AWS (`eu-north-1`). The React frontend sits on S3 + CloudFront. The FastAPI backend is an always-on container behind CloudFront, against Aurora Serverless v2 (PostgreSQL, IAM auth). Cognito handles sign-in, a Lambda pipeline (S3, SQS, EventBridge Scheduler, SES) builds the weekly report, and a Lambda calls Claude on Bedrock to parse agendas. `infra/` is Terraform in HCP Terraform workspace `spry-dev`.

The question is what it would take to run the same system on Google Cloud, and what it would cost. This ADR records a decision for every piece. The core of the app (frontend, API and database) moves in this lab. Sign-in, the weekly report and the agenda parser stay on AWS.

## Decision: one row per piece

| Spry on AWS | On Google Cloud | Decision | Why |
|---|---|---|---|
| S3 + CloudFront, static frontend | **Firebase Hosting** | **Replace** | CDN, HTTPS and a managed certificate are included. Free plan: 10 GB stored, 360 MB/day out. A `/api/**` rewrite to Cloud Run gives one origin and no CORS, as CloudFront did. A bare Cloud Storage bucket would need a load balancer, billed by the hour, for HTTPS. |
| ECS container + FastAPI (`spry-backend-service`) | **Cloud Run** `spry-api` | **Replace** | Runs the same Docker image, scales to 0 and has an HTTPS URL. Request-based billing (`cpu_idle = true`). `max_instance_count = 3` caps the bill and the connections to `db-f1-micro`. |
| ECR | **Artifact Registry** `spry` | **Replace** | 0.5 GB free. A cleanup policy keeps the last 2 images. |
| Aurora Serverless v2 (pauses) | **Cloud SQL for PostgreSQL 16**, `db-f1-micro`, 10 GB SSD | **Replace** | See *The database* below. |
| DynamoDB | Firestore | **Drop** | Spry never left SQL. Firestore was evaluated as the database option and rejected. |
| Cognito user pool + Google | Identity Platform | **Keep on AWS** (stretch) | See *Not moved*. |
| EventBridge Scheduler | Cloud Scheduler | **Keep on AWS** | Belongs to the weekly report. |
| SQS | Pub/Sub / Cloud Tasks | **Keep on AWS** | Belongs to the weekly report. Cloud Tasks would be the closer fit (a work queue, not fan-out). |
| S3 event → Lambda | Cloud Storage + Eventarc → Cloud Run | **Keep on AWS** | Belongs to the weekly report. |
| SES | no Google service | **Keep SES** | See *E-mail*. |
| Bedrock (Claude) | Vertex AI | **Keep on AWS** | See *Not moved*. |
| Secrets Manager / Parameter Store | **Secret Manager** | **Replace** | One secret, `spry-db-password`. Only `spry-api` can read it. |
| CloudWatch Logs | **Cloud Logging** | **Replace** (implicit) | Cloud Run sends stdout to Cloud Logging without any configuration. |
| IAM roles | **Service accounts + IAM** | **Replace** | One service account per program: `spry-terraform` and `spry-api`. Neither has Owner or Editor, and neither uses the default compute SA. |
| Terraform `aws` provider, workspace `spry-dev` | Terraform `google` provider, workspace **`spry-gcp`** | **Replace** | `gcp/` has its own state, so one plan cannot break both clouds. |

### The database

We weighed four options: Cloud SQL around the clock, Cloud SQL stopped at night, Firestore, or keeping Aurora and calling it across clouds.

| Option | Latency | Bill (idle month) | Code |
|---|---|---|---|
| **Cloud SQL, always on** | ~1 ms (same region, connector socket) | **$9.37** ($7.67 compute + $1.70 storage) | Small. `database.py` connects over `/cloudsql/...` with a password from Secret Manager instead of an RDS IAM token. Alembic, models and JSONB are unchanged. |
| Cloud SQL, stopped at night | Same while running. A start takes about a minute, so someone or something (Cloud Scheduler) has to start it. | **≈ $9.00 – $9.09**, not ≈ $1.70 | Same as above, plus a scheduler. |
| Firestore | Single-digit ms per document | **$0** | A rewrite. Joins and the `meetings → agendas` foreign key become documents, Alembic goes away, and the weekly report's SQL aggregation is reimplemented. Reads are billed per document, so a busy month can cost *more* than Cloud SQL (see `docs/lab9-answers.md`). |
| Keep Aurora on AWS | 100+ ms per query from `us-central1` to `eu-north-1`, several queries per request | $0 on GCP, plus AWS egress | Aurora sits in private subnets with IAM auth. Cloud Run would need a network path into the VPC *and* AWS credentials to sign RDS tokens. That is the worst of both clouds. |

**Decision: Cloud SQL `db-f1-micro`, always on while the GCP copy is needed, and `terraform destroy` once it is no longer needed.** We did not choose to stop it at night. The reason is **the idle IPv4 trap**. A stopped Cloud SQL instance still pays for storage *and for its public IPv4 address*: $0.01/h ≈ $7.30/month ([start/stop docs](https://docs.cloud.google.com/sql/docs/postgres/start-stop-restart-instance): "charges for storage and IP addresses continue to apply"). With a public IP, stopping saves about 4% ($9.37 → $9.00). The ≈ $1.70 "stopped" figure only holds for a private-IP-only instance. That needs a VPC, Private Services Access and Direct VPC egress from Cloud Run, which would be the next step if the GCP copy became permanent.

The instance has a public IP but **no authorised networks**. Only the Cloud SQL connector (IAM-checked, mTLS) can reach it.

Data loading: **migrations against the empty database, not `pg_dump`**. The container runs `alembic upgrade head` on start. Demo rows go in through the public API (`make gcp-seed`). Aurora is in private subnets behind IAM auth, and the SCP on the AWS account denies `rds:Describe*` to `spry-dev`, so a dump would have needed a bastion. It would also have copied student test data that has no place in a second cloud.

### E-mail
**Keep Amazon SES.** The weekly report stays on AWS, so SES is still called from a Lambda with an IAM role, and **no API key exists anywhere**.

If the report moves to GCP (stretch), there are two options in order of preference:
1. Keep SES and call it from Cloud Run **without a key**. An AWS role trusts `accounts.google.com` (a built-in web identity provider, so no `iam:CreateOpenIDConnectProvider`, which the SCP blocks). The Cloud Run job exchanges its Google-signed ID token through `sts:AssumeRoleWithWebIdentity`, with the role's condition pinned to the `spry-report` service account's unique ID. This still needs checking against the AWS organisation's SCP.
2. A transactional provider such as Mailgun or Resend. Its API key lives in **Secret Manager** (`spry-mail-api-key`), readable only by the report job's service account. It is put there with `gcloud secrets versions add` and is never in `tfvars`, state or the repository.

### Not moved, and why
- **Sign-in (Cognito).** User accounts live in the pool, and Cognito does not export password hashes. Moving means every password user resets, or a lazy-migration trigger. Identity Platform's 50,000 free MAU does not matter at Spry's size.
- **Weekly report.** It is six AWS services (Scheduler, SQS, S3, two Lambdas, SES), runs once a week, costs cents, and has no GCP counterpart for its last step (SES). Moving it is a rewrite of glue code for no gain.
- **Agenda parser (Bedrock).** The prompt, tool schema and tests were tuned on Claude via Bedrock (Lab 6). Claude on Vertex AI is the same model, but **the trial credit does not pay for partner models**. Gemini would mean re-validating the prompt and its tests. The browser calls the Lambda Function URL directly, so it works from any frontend origin once CORS allows it.

## Other decisions

- **Region `us-central1`.** It matches the lab's price list and the US-only always-free tiers (e.g. Cloud Storage), and it supports Firebase rewrites to Cloud Run. The latency-optimal region for users in Ukraine would be `europe-central2` (Warsaw), at higher list prices. Cloud SQL and Cloud Run *must* share a region either way.
- **Keyless Terraform.** HCP Terraform reaches GCP through **Workload Identity Federation** (pool `hcp-terraform`, provider for `https://app.terraform.io`). The attribute condition pins the **organisation and workspace IDs** (`org-…`, `ws-…`) rather than names, which can be re-registered. No service account key is ever created. This is what ADR 0007 wanted on AWS but could not have, because the SCP denies `iam:CreateOpenIDConnectProvider`.
- **Bootstrap split.** `gcp/bootstrap/` runs once from a laptop with the owner's ADC. It creates the service accounts, the WIF pool, Firebase, and every *project-level* role grant. The workload config in `gcp/` therefore runs as `spry-terraform` **without Project IAM Admin**, so it cannot grant itself more. "Service Account User" is granted on `spry-api` only, not project-wide.
- **The DB password never enters Terraform state.** It is an `ephemeral "random_password"` written through write-only attributes (`google_sql_user.password_wo`, `google_secret_manager_secret_version.secret_data_wo`). This closes the "secrets in plaintext state" gap ADR 0007 documented. Rotation means bumping `db_password_version`.
- **One image, three runtimes.** The API never ran on Lambda, so there is no Mangum or Web Adapter to remove. The same image runs on ECS, on two Lambdas (via `awslambdaric`, chosen only when `AWS_LAMBDA_RUNTIME_API` is set) and on Cloud Run. The only change is that `CMD` listens on `${PORT:-8000}`.
- **Image pinned by digest** in `gcp/terraform.tfvars`, as `infra/` does for the report builder. On the first apply Cloud Run runs Google's `hello` image until the backend has been pushed.

## Consequences

- **Known gap: the API is public and unauthenticated.** Firebase's `/api/**` rewrite calls Cloud Run as an anonymous client, so `spry-api` allows `allUsers`. This matches the AWS deployment (also reachable through CloudFront without a token), but anyone can `POST /api/meetings`. The fix is the stretch goal: verify an ID token (Cognito now, Identity Platform later) in FastAPI before accepting writes.
- **The GCP copy is a parallel deployment, not a split.** Its data lives in Cloud SQL. The AWS weekly report still reads Aurora, so it does not see meetings created on GCP.
- **Sign-in and "Parse with AI" do not work from `*.web.app` yet.** The Cognito app client's callback URLs and the parser Function URL's CORS list only the CloudFront origin. The fix is a one-line change in `infra/` (add the Firebase origin), made as a separate PR in the separate workspace.
- **Lock-in found.** Compute moved unchanged (same image). The database moved with a 15-line connection change because both clouds speak PostgreSQL. What did *not* move is the managed glue around the app (Cognito user store, SES, SQS/EventBridge wiring, Bedrock). That is where the lock-in is.
