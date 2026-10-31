project_name = "spry"
aws_region   = "eu-north-1"

# Auth
domain_prefix    = "spry-sofiia"
site_url         = "https://d1pk13cbcfrq49.cloudfront.net"
google_client_id = "1067825772736-a5pgbvig5ive11a0io4d1mpn1r7m41o0.apps.googleusercontent.com"

# Reports
vpc_id                   = "vpc-0a4ba1d2c35976d63"
private_subnet_ids       = ["subnet-0d7fd77e5bf73abbd", "subnet-0e2cdde417e0aa0ce", "subnet-0b67c45fba56f734d"]
private_route_table_ids  = ["rtb-0a2a44e48d6ac2f03"]
lambda_security_group_id = "sg-07172fe5ea15a237c"
sender_email             = "zavada.sofia@gmail.com"
recipient_emails         = "zavada.sofia@gmail.com"
builder_image_uri        = "545769669518.dkr.ecr.eu-north-1.amazonaws.com/spry-backend@sha256:1cd862350cb7fa490c91f73706f76fe80e7623b17d7b2abc436fd3e7bd314f19"

# AI
parser_image_uri = "545769669518.dkr.ecr.eu-north-1.amazonaws.com/spry-backend:latest"
parser_model     = "anthropic.claude-opus-5-5"
mock_ai          = "true"
