variable "aws_region" {
  description = "AWS region"
  default     = "eu-north-1"
}

variable "db_password" {
  description = "RDS master password"
  sensitive   = true
}

variable "db_username" {
  description = "RDS master username"
  default     = "postgres"
}
