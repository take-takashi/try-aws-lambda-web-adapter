
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  project_name = "try-aws-lambda-web-adapter"
  tags = {
    Project = local.project_name
  }

  # Check if the 'latest' image exists in the ECR repository.
  # The `try` function handles the error that occurs if the image is not found.
  latest_image = try(data.aws_ecr_image.app.image_digest, null)

  # Use the public dummy image if our image doesn't exist yet (on the first run).
  # Otherwise, use the image from our ECR repository.
  lambda_image_uri = local.latest_image == null ? "public.ecr.aws/lambda/python:3.12-slim" : "${aws_ecr_repository.app.repository_url}@${data.aws_ecr_image.app.image_digest}"
}

# ECR
resource "aws_ecr_repository" "app" {
  name                 = local.project_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Be careful with this in production

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

# Attempt to find the 'latest' tagged image in our repository.
# This depends on the repository being created first.
data "aws_ecr_image" "app" {
  repository_name = aws_ecr_repository.app.name
  image_tag       = "latest"
  depends_on = [
    aws_ecr_repository.app
  ]
}

# CloudWatch
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/lambda/${local.project_name}"
  retention_in_days = 30

  tags = local.tags
}

# IAM
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${local.project_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "aws_lambda_basic_execution_role" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda
resource "aws_lambda_function" "app" {
  function_name = local.project_name
  role          = aws_iam_role.app.arn
  package_type  = "Image"
  image_uri     = local.lambda_image_uri # Use the conditional image URI
  timeout       = 30

  tags = local.tags

  # Explicitly depend on the ECR repository resource
  depends_on = [
    aws_ecr_repository.app
  ]
}

# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "http_api" {
  name          = local.project_name
  protocol_type = "HTTP"

  tags = local.tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  tags = local.tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"

  integration_uri    = aws_lambda_function.app.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
