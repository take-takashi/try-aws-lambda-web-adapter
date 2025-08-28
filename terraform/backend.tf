terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configuration for bucket, region, and dynamodb_table
    # will be provided via the 'mise run tf-init' task.
    key     = "flask-app/terraform.tfstate"
    encrypt = true
  }
}
