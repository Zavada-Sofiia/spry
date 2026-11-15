# Lab 9: One project, two clouds. Answers

Service choices and their reasons are in [ADR 0009](adr/0009-google-cloud.md). This file has the cost table (Part 3), the Part 4 answers and demo steps, and notes for the class discussion.

---

## Part 3: Spry's minimal setup on both clouds, and what it costs

### Assumptions
- On-demand list prices in USD from the lab (checked 5 Nov 2026): **AWS `us-east-1`**, **GCP `us-central1`**. 730 h/month, no tax, no credits. The $300 trial credit is deliberately ignored because it hides the bill.
- **AWS = the Lab 4 Stage 2 minimal stack**: CloudFront Free plan + Lambda + Aurora Serverless v2 (0–1 ACU, auto-pause) + ~1 GB storage.
  > Spry's *actual* AWS API is an always-on container behind CloudFront, not a Lambda. That adds an always-on compute line I could not size from here: the account's SCP denies `ecs:Describe*` to `spry-dev`. Take it from the console and add it to the AWS column. It only widens the gaps below.
- **GCP = what `gcp/` deploys**: Firebase Hosting (Spark) + Cloud Run (1 vCPU / 512 MiB, request-based, min 0) + Cloud SQL `db-f1-micro`, 10 GB SSD, public IP, no backups.
- **Free tiers used:** Cloud Run 2M requests, 180,000 vCPU-s and 360,000 GiB-s a month. Firebase Hosting 360 MB/day out. Secret Manager 6 versions and 10,000 accesses (the secret is read once per instance start). Artifact Registry 0.5 GB. Cloud Logging 50 GiB. Lambda 1M requests and 400,000 GB-s. CloudFront Free plan 1M requests and 100 GB.
- **Traffic per profile.** Hours the database is awake: nobody 0 h, class demos 10 × 2 h = 20 h, office hours 8 h × 22 = 176 h, busy 730 h. Request volume is negligible except for *busy*, assumed to be **1 request/s around the clock**: 2.63M requests, 100 ms each, ~2 KB responses.
- **Aurora:** $0.12 per ACU-hour, 0.5 ACU while awake, plus a 5-minute pause delay after each session (so 20.8 h and 177.8 h). For *busy*, 1 ACU. Storage $0.10/GB. I/O ≈ $0 (the working set fits in the buffer cache).
- **Cloud SQL:** $0.0105/h while running. SSD $0.17/GB-month, billed while stopped too. **Public IPv4 $0.01/h while the instance is stopped.**

### The table (Cloud SQL, always on)

| Piece | AWS: nobody | AWS: demos | AWS: office | AWS: busy | GCP: nobody | GCP: demos | GCP: office | GCP: busy |
|---|---|---|---|---|---|---|---|---|
| Frontend + CDN + HTTPS | $0 | $0 | $0 | **$15.00**¹ | $0 | $0 | $0 | $0² |
| API compute | $0 | $0 | $0 | $0.33³ | $0 | $0 | $0 | **$2.24**⁴ |
| Database compute | $0 | $1.25 | $10.67 | **$87.60** | **$7.67** | **$7.67** | **$7.67** | **$7.67** |
| Database storage | $0.10 | $0.10 | $0.10 | $0.10 | $1.70 | $1.70 | $1.70 | $1.70 |
| Registry, secrets, logs | $0.20 | $0.20 | $0.20 | $0.20 | $0 | $0 | $0 | $0 |
| **Total / month** | **$0.30** | **$1.55** | **$10.97** | **$103.23** | **$9.37** | **$9.37** | **$9.37** | **$11.61** |

1. 2.63M requests exceed the CloudFront Free plan's 1M, so the next flat-rate plan (Pro, $15) applies.
2. 2.63M × 2 KB ≈ 5.3 GB/month ≈ 175 MB/day, inside Firebase's 360 MB/day.
3. Lambda: (2.63M − 1M) × $0.20/M. Compute is 131,400 GB-s, inside the 400,000 free.
4. Cloud Run: active time 2.63M × 0.1 s = 262,800 s. vCPU (262,800 − 180,000) × $0.000024 = $1.99. Memory 131,400 GiB-s is free. Requests (2.63M − 2M) × $0.40/M = $0.25.

### The same GCP column if you stop Cloud SQL when nobody uses it

| | nobody | demos | office | busy |
|---|---|---|---|---|
| Compute (h × $0.0105) | $0 | $0.21 | $1.85 | $7.67 |
| Storage | $1.70 | $1.70 | $1.70 | $1.70 |
| **Idle public IPv4** ((730 − h) × $0.01) | **$7.30** | **$7.10** | **$5.54** | $0 |
| Cloud Run | $0 | $0 | $0 | $2.24 |
| **Total** | **$9.00** | **$9.01** | **$9.09** | **$11.61** |
| *without a public IP (private IP only)* | *$1.70* | *$1.91* | *$3.55* | *$11.61* |

### And with Firestore instead of Cloud SQL

| | nobody | demos | office | busy |
|---|---|---|---|---|
| Total | $0 | $0 | $0 | **≈ $17.56** |

At *busy*, `GET /api/meetings` returns every meeting. With 20 meetings that is 20 document reads per request: 52.6M reads/month, minus 1.5M free, × $0.03/100k = **$15.32**, plus $2.24 for Cloud Run. The bill follows the code: at busy traffic, Firestore costs more than Cloud SQL.

### Which cloud is cheaper, and which single line decides it?

| Profile | Cheaper | By | Deciding line |
|---|---|---|---|
| Nobody | **AWS** ($0.30 vs $9.37) | $9 | Database compute. Aurora pauses to $0, Cloud SQL bills every hour. |
| Class demos | **AWS** ($1.55 vs $9.37) | $8 | Database compute (20 h of Aurora vs 730 h of Cloud SQL). |
| Office hours | **GCP** (≈ $9.37 vs $10.97) | $1.60, roughly a tie | Database compute: 177.8 h × 0.5 ACU × $0.12 overtakes a whole month of `db-f1-micro`. |
| Busy 24/7 | **GCP** ($11.61 vs $103.23) | ~9× | Database compute: 1 ACU × $0.12 × 730 h = $87.60 vs $7.67. |

The same line decides every profile: **database compute**. Everything else is under $3 on both sides. Two caveats. First, it is not like-for-like: 1 ACU is ~2 GiB of memory, while `db-f1-micro` is a 0.6 GB shared core that would struggle well before 1 request/s of heavy queries. A fair busy comparison is `db-g1-small` ($0.035/h → $25.55, GCP total ≈ $29.50), which is still about 3.5× cheaper. Second, the real AWS bill is higher by the always-on API container.

### Lab 4's Aurora trap, and where the GCP equivalent is

On AWS the trap was *something keeps Aurora awake* (a health check or a polling page), so "serverless" bills 730 h of ACUs.

On GCP the database has nothing to keep awake. It is **always** awake. The traps are elsewhere:

1. **"Stopped" is not free: the idle IPv4 address.** A stopped Cloud SQL instance with a public IP bills $0.01/h for the address ($7.30/month) on top of storage. Stopping it saves $0.37 of $9.37. The lab's "≈ $1.70 with the instance stopped" only holds for a private-IP-only instance. This is the closest equivalent: the action you take to save money barely does.
2. **Cloud Run settings that turn off scale-to-zero.** `min_instance_count = 1`, or instance-based billing (`cpu_idle = false`, "CPU always allocated"), bills an instance 730 h/month even with no users. That is the same failure mode as an Aurora kept awake. `gcp/cloudrun.tf` sets `min = 0` and `cpu_idle = true` for this reason.
3. **Firestore reads that follow the code.** A list page that reads N documents per visit spends the 50,000 free reads after 50,000/N visits (see the busy column).
4. **Storage only grows.** With `disk_autoresize` on, a one-off import can grow the SSD for good (it never shrinks), and SSD is billed while stopped. `gcp/database.tf` turns it off.

---

## Part 4: What else Google Cloud is good at

### Demo 1: BigQuery (you)
In the BigQuery console (the sandbox needs no card), run this query and note **bytes processed** before running (top right) and after (*Job information*):

```sql
-- Monthly revenue and order count by status, from Google's public e-commerce sample.
-- The same shape as the Lab 8 payments query, here with no crawler, catalog or result bucket.
SELECT
  DATE_TRUNC(DATE(created_at), MONTH) AS month,
  status,
  COUNT(DISTINCT order_id)            AS orders,
  ROUND(SUM(sale_price), 2)           AS revenue_usd
FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= TIMESTAMP('2025-01-01')
GROUP BY month, status
ORDER BY month, status;
```

Only the four referenced columns are scanned (columnar storage), so the job processes a few MB of the free 1 TiB. `SELECT *` on the same table would scan every column. Bytes scanned is the bill.

Save the result: *Save results → BigQuery table* (`spry_lab9.monthly_revenue`, sandbox tables expire after 60 days) or open it directly in Looker Studio.

### Demo 2: Looker Studio (you)
*Explore data → Looker Studio* from the query result, or *Create → Data source → BigQuery → spry_lab9.monthly_revenue*. Add a **time series**: dimension `month`, metric `revenue_usd`, breakdown `status`. Take a screenshot of the chart.

### Demo 3: Document AI OCR or Vision OCR (you)
- **Document AI:** *Document AI → Create processor → Enterprise Document OCR* (or *Form Parser*), region `us`. Upload one PDF (a scanned meeting agenda fits the Spry story), then screenshot the extracted text and blocks. The first 1,000 OCR pages a month are free; Form Parser costs $30 per 1,000 pages.
- **or Vision API:** enable `vision.googleapis.com` and use the *Try it* panel on the Vision product page with a photo of a handwritten page. `TEXT_DETECTION` / `DOCUMENT_TEXT_DETECTION`, 1,000 units a month free.

### When is Document AI the better tool than an LLM (Lab 6), and when not?
- **Document AI is better when the input is a *document image*** (scans, photos, PDFs without a text layer), when you need **positions** (bounding boxes, tables, key-value pairs with page coordinates), and when the output must be **deterministic and auditable** at volume. OCR costs $1.50 per 1,000 pages with no prompt to maintain, no hallucination of fields that are not on the page, and a confidence score per token.
- **An LLM is better when the input is already text and the task is *interpretation***. Spry's agenda parser turns "sync w/ design next Tue after lunch, ~45 min" into a start time relative to *today* and a timezone, splits items, and assigns owners. No OCR processor does that, and Lab 6 needed `today` and `tz` in the prompt for exactly this reason.
- **They compose:** OCR → text → LLM for meaning. For a photographed agenda, Document AI would be step 1 and the existing Claude parser step 2.

### Link to Lab 8: Athena + Glue → BigQuery, Dataflow, Looker Studio
| Lab 8 on AWS | Here | What you no longer manage |
|---|---|---|
| S3 raw files | Cloud Storage | (same idea) |
| Glue crawler + Data Catalog tables | BigQuery tables / external tables | Crawler runs, schema drift fixes, partition registration (`MSCK REPAIR` or partition projection) |
| Glue ETL job (Spark) | **Dataflow** (Apache Beam), or just BigQuery SQL for SQL-shaped transforms | Spark cluster sizing, DPUs, job bookmarks. The same Beam code also runs as a stream. |
| Athena queries | **BigQuery** | The query-results S3 bucket, workgroups, and file-format/compression tuning to cut bytes scanned (BigQuery's own storage is already columnar and compressed) |
| QuickSight | **Looker Studio** | SPICE capacity and per-user licences. It is free. |

The pricing model is the same: both bill **bytes scanned** (Athena $5/TB, BigQuery $6.25/TiB after the free 1 TiB). The difference is that BigQuery owns the storage format, so there is less to tune.

---

## Notes for the class discussion

- **Lock-in.** The compute moved unchanged (same image, `CMD` now honours `$PORT`). The database moved with a small connection change because PostgreSQL is PostgreSQL. The lock-in is in the **managed services around the app**: Cognito's user store (no password hash export), SES, the SQS/EventBridge/S3-event wiring, and Bedrock's SDK path. That is where the "keep on AWS" rows in ADR 0009 come from.
- **Multicloud.** As run here it is a **migration state, not an architecture**. The two copies have separate data, and the weekly report on AWS cannot see GCP meetings. A real split would put cross-cloud calls on the request path: 100+ ms transatlantic RTT per query, AWS egress at $0.09/GB, two IAM models, two on-call runbooks and two bills. It is worth it only for a service one cloud does uniquely well (e.g. Bedrock or BigQuery), called asynchronously.
- **Scale to zero.** Giving up SQL to save ~$9/month is worth it when the data really is key-value or document-shaped and read patterns are known and bounded. For Spry it is a bad trade: relational data (meetings → agendas), Alembic migrations, a weekly aggregation report, and a read-per-document bill that grows with the list size. At 1 request/s Firestore is already the more expensive option.
- **Choosing a cloud.** At Spry's size the bill differs by ~$9/month either way, and the $300 credit swamps it. What decides is **what the team already knows**, plus the one service you can't easily replace. Here that is Claude on Bedrock today. If the product grew an analytics side, BigQuery would be the reason to pick GCP.
