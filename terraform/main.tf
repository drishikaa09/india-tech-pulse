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

# S3 Bucket
resource "aws_s3_bucket" "india_tech_pulse" {
  bucket = "india-tech-pulse-data"

  tags = {
    Project = "india-tech-pulse"
  }
}

# Security Group for RDS (existing default sg)
resource "aws_security_group" "rds_sg" {
  name        = "default"
  description = "default VPC security group"
  vpc_id      = "vpc-0507f29468aa7af80"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "india_tech_pulse" {
  identifier        = "india-tech-pulse-db"
  engine            = "postgres"
  engine_version    = "18.3"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp2"

  username              = var.db_username
  password              = var.db_password

  publicly_accessible   = true
  skip_final_snapshot   = true
  storage_encrypted     = true
  copy_tags_to_snapshot = true
  max_allocated_storage = 1000

  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  tags = {
    Project = "india-tech-pulse"
  }
}
