output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.india_tech_pulse.bucket
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.india_tech_pulse.endpoint
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.india_tech_pulse.port
}

