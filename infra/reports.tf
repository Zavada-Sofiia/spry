data "aws_caller_identity" "current" {}

# ---------- Reports Bucket ----------
resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "expire-reports-90d"
    status = "Enabled"

    filter {
      prefix = "reports/"
    }

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket_notification" "reports" {
  bucket = aws_s3_bucket.reports.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.mailer.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "reports/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.mailer]
}

# ---------- S3 Gateway Endpoint ----------
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids
}

# ---------- SQS Queues ----------
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-report-requests-dlq"
  message_retention_seconds = 1209600 # 14 days
  max_message_size          = 1048576

  tags = {
    Project = var.project_name
  }
}

resource "aws_sqs_queue" "requests" {
  name                       = "${var.project_name}-report-requests"
  visibility_timeout_seconds = 360 # >= 6 x builder timeout (60 s)
  max_message_size           = 1048576

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = var.project_name
  }
}

# ---------- Builder Lambda Queue Mapping ----------
resource "aws_lambda_event_source_mapping" "builder" {
  event_source_arn = aws_sqs_queue.requests.arn
  function_name    = aws_lambda_function.builder.arn
  batch_size       = 1
}

# ---------- Report Builder Role & Lambda ----------
resource "aws_iam_role" "builder" {
  name = "spry-reports-BuilderRole-kmMmHDKBxIGt"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  inline_policy {
    name = "builder"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect   = "Allow"
          Action   = "s3:PutObject"
          Resource = "arn:aws:s3:::${var.project_name}-reports-${data.aws_caller_identity.current.account_id}/reports/*"
        },
        {
          Effect = "Allow"
          Action = [
            "sqs:ReceiveMessage",
            "sqs:DeleteMessage",
            "sqs:GetQueueAttributes"
          ]
          Resource = aws_sqs_queue.requests.arn
        },
        {
          Effect   = "Allow"
          Action   = "rds-db:connect"
          Resource = "arn:aws:rds-db:${var.aws_region}:${data.aws_caller_identity.current.account_id}:dbuser:cluster-JNMT4I3SCKAVPZXHHCXBZAM2ZI/postgres"
        }
      ]
    })
  }
}

resource "aws_lambda_function" "builder" {
  function_name = "${var.project_name}-report-builder"
  package_type  = "Image"
  image_uri     = var.builder_image_uri
  role          = aws_iam_role.builder.arn
  timeout       = 60
  memory_size   = 512

  image_config {
    command = ["app.reports.lambda_handler.handler"]
  }

  environment {
    variables = {
      REPORTS_BUCKET = "${var.project_name}-reports-${data.aws_caller_identity.current.account_id}"
      DATABASE_URL   = var.database_url
    }
  }

  tags = {
    Project = var.project_name
  }
}

# ---------- Scheduler Role & Weekly Schedule ----------
resource "aws_iam_role" "scheduler" {
  name = "spry-reports-SchedulerRole-IY98j7Hlhb3Y"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })

  inline_policy {
    name = "invoke-queue"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect   = "Allow"
          Action   = "sqs:SendMessage"
          Resource = aws_sqs_queue.requests.arn
        }
      ]
    })
  }
}

resource "aws_scheduler_schedule" "weekly" {
  name                         = "${var.project_name}-weekly-report"
  schedule_expression          = "cron(0 7 ? * MON *)"
  schedule_expression_timezone = "Europe/Kyiv"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.requests.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = "{\"week\": null, \"source\": \"schedule\"}"
  }
}

# ---------- Report Mailer Role, Code, & Lambda ----------
resource "aws_iam_role" "mailer" {
  name = "spry-reports-MailerRole-PEgFa4yIMAc0"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  inline_policy {
    name = "mailer"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect   = "Allow"
          Action   = "s3:GetObject"
          Resource = "arn:aws:s3:::${var.project_name}-reports-${data.aws_caller_identity.current.account_id}/reports/*"
        },
        {
          Effect = "Allow"
          Action = [
            "ses:SendRawEmail",
            "ses:SendEmail"
          ]
          Resource = "*"
        }
      ]
    })
  }
}

data "archive_file" "mailer_zip" {
  type        = "zip"
  output_path = "${path.module}/mailer_build.zip"

  source {
    filename = "index.py"
    content  = <<-PY
      import os, urllib.parse
      from email.message import EmailMessage
      import boto3

      s3 = boto3.client("s3")
      ses = boto3.client("sesv2")

      def handler(event, context):
          rec = event["Records"][0]
          bucket = rec["s3"]["bucket"]["name"]
          key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])
          print(f"report-mailer triggered trigger=s3 bucket={bucket} key={key}")

          body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
          week = key.rsplit("/", 1)[-1].removesuffix(".csv")
          recipients = [r.strip() for r in os.environ["RECIPIENTS"].split(",") if r.strip()]

          msg = EmailMessage()
          msg["Subject"] = f"Weekly meetings report {week}"
          msg["From"] = os.environ["SENDER"]
          msg["To"] = ", ".join(recipients)
          msg.set_content(f"Your weekly meetings report for {week} is attached.")
          msg.add_attachment(body, maintype="text", subtype="csv", filename=f"{week}.csv")

          ses.send_email(Content={"Raw": {"Data": msg.as_bytes()}})
          print(f"report-mailer sent key={key} to={len(recipients)} recipients")
    PY
  }
}

resource "aws_lambda_function" "mailer" {
  function_name    = "${var.project_name}-report-mailer"
  runtime          = "python3.12"
  handler          = "index.handler"
  role             = aws_iam_role.mailer.arn
  timeout          = 30
  filename         = data.archive_file.mailer_zip.output_path
  source_code_hash = data.archive_file.mailer_zip.output_base64sha256

  environment {
    variables = {
      SENDER     = var.sender_email
      RECIPIENTS = var.recipient_emails
    }
  }
}

resource "aws_lambda_permission" "mailer" {
  statement_id   = "AllowS3Invoke"
  function_name  = aws_lambda_function.mailer.function_name
  action         = "lambda:InvokeFunction"
  principal      = "s3.amazonaws.com"
  source_arn     = aws_s3_bucket.reports.arn
  source_account = data.aws_caller_identity.current.account_id
}

# ---------- SES Email Identity ----------
resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}
