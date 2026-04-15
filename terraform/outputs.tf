output "ec2_public_ip" {
  description = "Public IP of the EC2 instance — add to GitHub Secrets as EC2_HOST"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.app.public_dns
}

output "app_url" {
  description = "Weather app URL"
  value       = "http://${aws_instance.app.public_ip}:8000"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_instance.app.public_ip}:9090"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = "http://${aws_instance.app.public_ip}:3000"
}

output "ecr_repository_url" {
  description = "ECR repository URL — used by GitHub Actions to push images"
  value       = aws_ecr_repository.app.repository_url
}

output "ssh_private_key" {
  description = "PEM private key — add to GitHub Secrets as EC2_SSH_KEY, and save locally to SSH in"
  value       = tls_private_key.app.private_key_pem
  sensitive   = true
}

output "ssh_command" {
  description = "Command to SSH into your EC2 instance"
  value       = "ssh -i weather-app-key.pem ubuntu@${aws_instance.app.public_ip}"
}

output "github_actions_access_key_id" {
  description = "Add to GitHub Secrets as AWS_ACCESS_KEY_ID"
  value       = aws_iam_access_key.github_actions.id
}

output "github_actions_secret_access_key" {
  description = "Add to GitHub Secrets as AWS_SECRET_ACCESS_KEY"
  value       = aws_iam_access_key.github_actions.secret
  sensitive   = true
}
