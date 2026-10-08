AWS_REGION ?= eu-north-1
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REGISTRY = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPOSITORY = spry-backend
S3_BUCKET ?= sspry-frontend-bucket
CLOUDFRONT_DIST_ID ?= E3UJTICBAEK0V5
ECS_CLUSTER = spry-cluster
ECS_SERVICE = spry-backend-service
COMMIT_SHA ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")

.PHONY: deploy-frontend deploy-backend auth-env

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
	docker build -t $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(COMMIT_SHA) ./backend
	@echo "==> Pushing image to ECR..."
	docker push $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(COMMIT_SHA)
	@echo "==> Updating ECS Service..."
	aws ecs update-service --cluster $(ECS_CLUSTER) --service $(ECS_SERVICE) --force-new-deployment

auth-env:
	@POOL=$$(aws cloudformation describe-stacks --region eu-north-1 --stack-name spry-auth --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text); \
	CLIENT=$$(aws cloudformation describe-stacks --region eu-north-1 --stack-name spry-auth --query "Stacks[0].Outputs[?OutputKey=='ClientId'].OutputValue" --output text); \
	DOMAIN=$$(aws cloudformation describe-stacks --region eu-north-1 --stack-name spry-auth --query "Stacks[0].Outputs[?OutputKey=='CognitoDomain'].OutputValue" --output text); \
	printf "VITE_COGNITO_AUTHORITY=https://cognito-idp.eu-north-1.amazonaws.com/$$POOL\nVITE_COGNITO_CLIENT_ID=$$CLIENT\nVITE_COGNITO_DOMAIN=$$DOMAIN\n" > frontend/.env.production
