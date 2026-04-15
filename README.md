# 🌤️ Weather App - Cloud DevOps Stack

A production-ready **FastAPI** weather microservice utilizing an end-to-end DevOps deployment structure. This project automatically provisions AWS infrastructure via **Terraform**, runs continuous integration & deployment (CI/CD) through **GitHub Actions**, and features out-of-the-box observability using **Prometheus & Grafana**.

---

## 🏗️ Architecture

1.  **FastAPI Backend**: Fetches real-time weather data from OpenWeatherMap and natively exposes custom Python Prometheus metrics (`/metrics`).
2.  **AWS Infrastructure (Terraform)**: Provisions a free-tier `t3.micro` EC2 Instance, VPC, Security Groups, IAM Instance Profiles, and an AWS Elastic Container Registry (ECR).
3.  **Docker & Compose**: Containerizes the application. Uses `docker-compose.yml` for local development and `docker-compose.prod.yml` for CI/CD deployments.
4.  **CI/CD Pipeline (GitHub Actions)**: Automatically builds Docker images, pushes them to AWS ECR, connects to the EC2 via SSH, and dynamically injects the production containers via Docker Compose.
5.  **Monitoring Stack**: Included `prometheus` container for scraping data and an auto-provisioned `grafana` dashboard for visualizing HTTP request latency and weather fetch counts.

---

## 🚀 Local Development

To run this application locally on your machine without deploying to AWS:

*Note: The local `docker-compose.yml` handles building the image from the local `Dockerfile` rather than pulling from AWS ECR.*

1. Add your OpenWeather API key to a local `.env` file:
   ```env
   OPENWEATHER_API_KEY=your_openweather_api_key
   ENVIRONMENT=development
   ```
2. Run the application:
   ```bash
   docker compose up --build
   ```
3. Access the services globally:
   *   **FastAPI App:** `http://localhost:8000`
   *   **Prometheus:** `http://localhost:9090`
   *   **Grafana:** `http://localhost:3000` *(Login: admin / admin123)*

---

## ☁️ Cloud Deployment (AWS)

Follow these steps to deploy your own version of this project to the AWS Cloud.

### 1. Terraform Infrastructure Provisioning
You must create the AWS baseline infrastructure (EC2, ECR, IAM) first. 

```bash
# 1. Create a remote S3 Bucket for Terraform State (MUST BE GLOBALLY UNIQUE)
aws s3api create-bucket --bucket your-unique-tfstate-bucket --region us-east-1

# 2. Update terraform/main.tf
# Change line 10 to match your bucket above: bucket = "your-unique-tfstate-bucket"

# 3. Apply Terraform
cd terraform
terraform init
terraform apply -auto-approve
```

### 2. GitHub Secrets Setup
Once Terraform finishes, it will output 5 values. You must copy these and add them to your **GitHub Repository Settings -> Secrets and variables -> Actions**.

| GitHub Secret | Terraform Output Reference |
| :--- | :--- |
| `AWS_ACCESS_KEY_ID` | `terraform output github_actions_access_key_id` |
| `AWS_SECRET_ACCESS_KEY` | `terraform output -raw github_actions_secret_access_key` |
| `EC2_HOST` | `terraform output ec2_public_ip` |
| `EC2_SSH_KEY` | `terraform output -raw ssh_private_key` (Copy the full PEM text) |
| `OPENWEATHER_API_KEY` | *Your actual OpenWeatherMap API Key* |

### 3. Deploy App
Navigate to the GitHub Actions tab, or simply push code to the `main` branch. 
The pipeline will automatically build the image, push to your ECR, SSH into your EC2 server, and start the application!

---

## 🛑 Shutting Down (Cost Savings)
This project uses the AWS Option B Free-Tier architecture (`t3.micro`). It is eligible for 750 free hours per month, meaning it costs **$0.00** to leave it running 24/7 if it is your only EC2 server.

If you wish to fully destroy the infrastructure to ensure 100% clean billing:
```bash
cd terraform
terraform destroy
```
*(Warning: Re-deploying later via `terraform apply` will give your EC2 a Brand New Public IP, requiring you to update the `EC2_HOST` GitHub secret).*
