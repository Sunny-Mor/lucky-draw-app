# Jenkins Setup (Optional — Secondary CI/CD)

GitHub Actions is the primary CI/CD. Jenkins is an optional alternative.

## EC2 Setup

Launch an EC2 instance (t3.medium, Ubuntu 22.04) and run:

```bash
# Java
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk

# Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update && sudo apt-get install -y jenkins

# Docker
sudo apt-get install -y docker.io
sudo usermod -aG docker jenkins

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip && sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

sudo systemctl enable jenkins && sudo systemctl start jenkins
```

## Jenkins Credentials to Configure

In Jenkins → Manage Jenkins → Credentials:

| ID | Type | Value |
|---|---|---|
| `aws-credentials` | AWS Credentials | Access key + secret |
| `postgres-password` | Secret text | DB password |
| `admin-username` | Secret text | Admin username |
| `admin-password` | Secret text | Admin password |
| `app-secret-key` | Secret text | Flask secret key |

## Jenkins Environment Variables

In Jenkins → Manage Jenkins → Configure System → Global properties:

| Variable | Value |
|---|---|
| `ECR_PARTICIPATE_URL` | ECR URL from terraform output |
| `ECR_SUBMISSIONS_URL` | ECR URL from terraform output |
| `ECR_PICK_WINNER_URL` | ECR URL from terraform output |
| `ECR_SYNC_WORKER_URL` | ECR URL from terraform output |

## Create Pipeline Job

1. New Item → Pipeline
2. Pipeline → Definition: Pipeline script from SCM
3. SCM: Git → your repo URL
4. Script Path: `jenkins/Jenkinsfile`
5. Save and Build

## Required Jenkins Plugins

- Pipeline
- Git
- Amazon Web Services SDK
- Docker Pipeline
- Credentials Binding
