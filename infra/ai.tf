# ---------- Agenda Parser IAM Role ----------
resource "aws_iam_role" "parser" {
  name = "${var.project_name}-agenda-parser-role"

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
    name = "BedrockMantleInference"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "bedrock-mantle:CreateInference",
            "bedrock:InvokeModel"
          ]
          Resource = "*"
        }
      ]
    })
  }

  tags = {
    PROJECT_NAME = var.project_name
  }
}

# ---------- Agenda Parser Lambda (No VPC) ----------
resource "aws_lambda_function" "parser" {
  function_name = "${var.project_name}-agenda-parser"
  package_type  = "Image"
  image_uri     = var.parser_image_uri
  role          = aws_iam_role.parser.arn
  timeout       = 30
  memory_size   = 512

  image_config {
    command = ["app.ai.agenda_lambda.handler"]
  }

  environment {
    variables = {
      PARSER_MODEL         = var.parser_model
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.users.id
      COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.web.id
      COGNITO_REGION       = var.aws_region
      MOCK_AI              = var.mock_ai
    }
  }

  tags = {
    PROJECT_NAME = var.project_name
  }
}

# ---------- Agenda Parser Function URL ----------
resource "aws_lambda_function_url" "parser" {
  function_name      = aws_lambda_function.parser.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins = [
      var.site_url,
      "http://localhost:3000",
      "http://localhost:5173"
    ]
    allow_methods = ["POST"]
    allow_headers = [
      "authorization",
      "content-type"
    ]
    max_age = 300
  }
}

resource "aws_lambda_permission" "function_url" {
  statement_id           = "FunctionURLAllowPublicAccess"
  function_name          = aws_lambda_function.parser.function_name
  action                 = "lambda:InvokeFunctionUrl"
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "invoke" {
  statement_id  = "AllowPublicInvoke"
  function_name = aws_lambda_function.parser.function_name
  action        = "lambda:InvokeFunction"
  principal     = "*"
}
