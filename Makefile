AWS_REGION ?= eu-north-1
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REGISTRY = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPOSITORY = spry-backend
S3_BUCKET ?= sspry-frontend-bucket
CLOUDFRONT_DIST_ID ?= E3UJTICBAEK0V5
ECS_CLUSTER = spry-cluster
ECS_SERVICE = spry-backend-service
COMMIT_SHA ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")

PROJECT_NAME ?= spry

.PHONY: deploy-frontend deploy-backend auth-env report-now llm-hello parse infra-plan

deploy-frontend: auth-env
	@echo "==> Building frontend bundle..."
	cd frontend && npm ci && npm run build
	@echo "==> Syncing build files to S3..."
	aws s3 sync frontend/dist s3://$(S3_BUCKET) --delete
	@echo "==> Invalidating CloudFront cache..."
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_DIST_ID) --paths "/*"

deploy-backend:
	@echo "==> Logging in to Amazon ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)
	@echo "==> Building Docker image..."
	docker build --platform linux/amd64 -t $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(COMMIT_SHA) -t $(ECR_REGISTRY)/$(ECR_REPOSITORY):latest ./backend
	@echo "==> Pushing image to ECR..."
	docker push $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(COMMIT_SHA)
	docker push $(ECR_REGISTRY)/$(ECR_REPOSITORY):latest
	@echo "==> Updating ECS Service..."
	aws ecs update-service --region $(AWS_REGION) --cluster $(ECS_CLUSTER) --service $(ECS_SERVICE) --force-new-deployment

auth-env:
	@POOL=$$(terraform -chdir=infra output -raw UserPoolId); \
	CLIENT=$$(terraform -chdir=infra output -raw ClientId); \
	DOMAIN=$$(terraform -chdir=infra output -raw CognitoDomain); \
	PARSER=$$(terraform -chdir=infra output -raw ParserFunctionUrl 2>/dev/null || echo ""); \
	printf "VITE_COGNITO_AUTHORITY=https://cognito-idp.eu-north-1.amazonaws.com/$$POOL\nVITE_COGNITO_CLIENT_ID=$$CLIENT\nVITE_COGNITO_DOMAIN=$$DOMAIN\nVITE_PARSER_FUNCTION_URL=$$PARSER\n" > frontend/.env.production

report-now:
	@test -n "$(WEEK)" || (echo "usage: make report-now WEEK=2026-W39" && exit 1)
	aws sqs send-message \
	  --region $(AWS_REGION) \
	  --queue-url $$(terraform -chdir=infra output -raw ReportRequestsQueueUrl) \
	  --message-body '{"week":"$(WEEK)","source":"manual"}'

infra-plan:
	@echo "==> Running terraform plan in infra/..."
	terraform -chdir=infra plan

llm-hello:
	PYTHONPATH=backend python3 -c '\
from app.config import settings; \
from anthropic import AnthropicBedrockMantle; \
client = AnthropicBedrockMantle(aws_region="us-east-1"); \
msg = client.messages.create( \
    model=settings.PARSER_MODEL, \
    max_tokens=1024, \
    output_config={"effort": "low"}, \
    messages=[{"role": "user", "content": "In one sentence: what is an ISO week?"}], \
); \
print(next(b.text for b in msg.content if b.type == "text")); \
print(msg.stop_reason, msg.usage.input_tokens, msg.usage.output_tokens); \
'

parse:
	@test -n "$(TEXT)" || (echo "usage: make parse TEXT=\"...\"" && exit 1)
	PYTHONPATH=backend python3 -c '\
import json, sys; \
from datetime import date; \
from app.ai.agenda import parse_agenda, cost_usd; \
from app.config import settings; \
agenda, usage = parse_agenda(sys.argv[1], date.today(), "Europe/Kyiv"); \
print(agenda.model_dump_json(indent=2)); \
print(f"usage: {usage}, cost: $${cost_usd(settings.PARSER_MODEL, usage):.6f}"); \
' "$(TEXT)"






