# ---------- Auth Outputs ----------

output "UserPoolId" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.users.id
}

output "ClientId" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.web.id
}

output "CognitoDomain" {
  description = "Cognito Hosted UI Domain URL"
  value       = "https://${aws_cognito_user_pool_domain.domain.domain}.auth.${var.aws_region}.amazoncognito.com"
}

# ---------- AI Parser Outputs ----------

output "ParserFunctionArn" {
  description = "ARN of the agenda parser Lambda"
  value       = aws_lambda_function.parser.arn
}

output "ParserFunctionUrl" {
  description = "Function URL endpoint for the agenda parser"
  value       = aws_lambda_function_url.parser.function_url
}

# ---------- Reports Outputs ----------

output "ReportsBucketName" {
  description = "Name of the S3 reports bucket"
  value       = aws_s3_bucket.reports.id
}

output "ReportRequestsQueueUrl" {
  description = "SQS URL for incoming report generation requests"
  value       = aws_sqs_queue.requests.url
}

output "ReportRequestsDlqUrl" {
  description = "SQS Dead Letter Queue URL for failed report requests"
  value       = aws_sqs_queue.dlq.url
}

output "VerifiedEmailIdentity" {
  description = "Verified SES sender email identity"
  value       = aws_ses_email_identity.sender.email
}
