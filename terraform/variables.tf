variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used to prefix all resources"
  type        = string
  default     = "weather-app"
}

variable "ec2_instance_type" {
  description = "EC2 instance type — t3.micro is free tier eligible"
  type        = string
  default     = "t3.micro"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    Project     = "weather-app"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
