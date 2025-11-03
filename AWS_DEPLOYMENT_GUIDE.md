# AWS EKS Deployment Guide

**Status**: 🚧 In Progress
**Created**: 2025-11-02

---

## ⚠️ Prerequisites Checklist

Before deploying, you need:

- [ ] AWS CLI installed and configured
- [ ] AWS credentials (Access Key ID + Secret Access Key)
- [ ] kubectl installed
- [ ] Docker installed
- [ ] Terraform initialized (✅ DONE)

---

## 🔧 Step 1: Install AWS CLI

### Option A: Using pip (Recommended)
```bash
pip install awscli
```

### Option B: Using official installer
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Verify installation:
```bash
aws --version
```

**Expected output**: `aws-cli/2.x.x Python/3.x.x Linux/x.x.x`

---

## 🔑 Step 2: Configure AWS Credentials

### Get Your AWS Credentials

1. **Login to AWS Console**: https://console.aws.amazon.com
2. **Navigate to**: IAM → Users → Your Username → Security Credentials
3. **Create Access Key**: Click "Create access key" → Select "CLI" → Create
4. **Save**: Copy Access Key ID and Secret Access Key

### Configure AWS CLI

```bash
aws configure
```

**Enter when prompted**:
- AWS Access Key ID: [Your Access Key]
- AWS Secret Access Key: [Your Secret Key]
- Default region name: us-east-2  # Match your .env file
- Default output format: json

### Verify credentials work:
```bash
aws sts get-caller-identity
```

**Expected output**:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### Alternative: Use Environment Variables

If you don't want to use `aws configure`, you can export credentials:

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGION="us-east-2"
```

---

## 📝 Step 3: Create Terraform Variables File

```bash
cd infrastructure/terraform

# Create terraform.tfvars from example
cat > terraform.tfvars <<EOF
aws_region   = "us-east-2"
cluster_name = "nim-rag-agent-cluster"
environment  = "production"
EOF
```

---

## 🎯 Step 4: Review Infrastructure Plan

**IMPORTANT**: This will create real AWS resources that cost money!

### Cost Estimate (Monthly):
- **EKS Control Plane**: ~$72/month
- **EC2 CPU Nodes** (2x t3.large): ~$140/month
- **EC2 GPU Node** (1x g4dn.xlarge): ~$150/month
- **NAT Gateways** (2x): ~$64/month
- **Load Balancer**: ~$20/month
- **EBS Storage**: ~$10/month

**TOTAL**: ~$450-500/month

### Preview what will be created:
```bash
cd infrastructure/terraform
terraform plan
```

**This will show**:
- VPC with public/private subnets across 3 AZs
- NAT Gateways for private subnet internet access
- EKS cluster with control plane
- 2x t3.large CPU nodes
- 1x g4dn.xlarge GPU node (NVIDIA T4)
- Security groups and IAM roles

---

## 🚀 Step 5: Deploy EKS Cluster

**⚠️ WARNING**: This will create real AWS resources and start billing!

### Deploy infrastructure:
```bash
cd infrastructure/terraform
terraform apply
```

**Timeline**:
- VPC creation: ~2 minutes
- EKS cluster: ~10-15 minutes
- Node groups: ~3-5 minutes
- **Total**: ~15-20 minutes

### What to expect:
```
Terraform will perform the following actions:
  # 50+ resources will be created

Plan: 50+ to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Enter a value: yes
```

Type `yes` and press Enter.

### Monitor progress:
Terraform will show real-time progress. Wait for:
```
Apply complete! Resources: 50+ added, 0 changed, 0 destroyed.

Outputs:

cluster_endpoint = "https://XXXXXXXXXX.gr7.us-east-2.eks.amazonaws.com"
cluster_name = "nim-rag-agent-cluster"
vpc_id = "vpc-xxxxxxxxxxxxx"
```

---

## ⚙️ Step 6: Configure kubectl

After EKS cluster is created:

```bash
aws eks update-kubeconfig --region us-east-2 --name nim-rag-agent-cluster
```

### Verify cluster access:
```bash
kubectl get nodes
```

**Expected output**:
```
NAME                                          STATUS   ROLES    AGE   VERSION
ip-10-0-1-xxx.us-east-2.compute.internal     Ready    <none>   2m    v1.28.x
ip-10-0-2-xxx.us-east-2.compute.internal     Ready    <none>   2m    v1.28.x
ip-10-0-3-xxx.us-east-2.compute.internal     Ready    <none>   2m    v1.28.x
```

### Check GPU node:
```bash
kubectl get nodes -l workload=gpu
```

---

## 🐳 Step 7: Build and Push Docker Image

### Create ECR repository:
```bash
aws ecr create-repository --repository-name nim-rag-agent --region us-east-2
```

### Get your AWS account ID:
```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Your AWS Account ID: $AWS_ACCOUNT_ID"
```

### Build Docker image:
```bash
cd /home/kengpu/aws-contest
docker build -t nim-rag-agent:latest .
```

### Login to ECR:
```bash
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com
```

### Tag and push image:
```bash
docker tag nim-rag-agent:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nim-rag-agent:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nim-rag-agent:latest
```

---

## ☸️ Step 8: Deploy Application to Kubernetes

### Create namespace:
```bash
cd /home/kengpu/aws-contest/infrastructure/kubernetes
kubectl apply -f namespace.yaml
```

### Create secrets with your NVIDIA API key:
```bash
# Get your NIM API key from .env
NIM_API_KEY=$(grep "^NIM_API_KEY=" ../../.env | cut -d'=' -f2)

# Create Kubernetes secret
kubectl create secret generic nim-api-key \
  --from-literal=NIM_API_KEY=$NIM_API_KEY \
  -n nim-rag-agent
```

### Apply configurations:
```bash
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
```

### Update deployment with your ECR image:
```bash
# Update deployment.yaml with your image URL
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed -i "s|image:.*|image: $AWS_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nim-rag-agent:latest|g" deployment.yaml

# Deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
```

### Wait for pods to be ready:
```bash
kubectl get pods -n nim-rag-agent -w
```

**Press Ctrl+C when all pods show STATUS: Running**

---

## 🌐 Step 9: Access Your Application

### Get the LoadBalancer URL:
```bash
kubectl get svc nim-rag-agent -n nim-rag-agent
```

**Output**:
```
NAME             TYPE           CLUSTER-IP      EXTERNAL-IP
nim-rag-agent    LoadBalancer   10.100.xxx.xxx  a1b2c3d4-1234567890.us-east-2.elb.amazonaws.com
```

### Access your application:
```
http://a1b2c3d4-1234567890.us-east-2.elb.amazonaws.com
```

⏱️ **Note**: LoadBalancer may take 2-3 minutes to become available after creation.

---

## 📊 Step 10: Verify Deployment

### Check all resources:
```bash
# Pods
kubectl get pods -n nim-rag-agent

# Service
kubectl get svc -n nim-rag-agent

# HPA (Horizontal Pod Autoscaler)
kubectl get hpa -n nim-rag-agent

# PVC (Persistent Volume Claim)
kubectl get pvc -n nim-rag-agent
```

### View logs:
```bash
kubectl logs -f deployment/nim-rag-agent -n nim-rag-agent
```

### Test the application:
```bash
# Get LoadBalancer URL
LB_URL=$(kubectl get svc nim-rag-agent -n nim-rag-agent -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$LB_URL/

# Should show Streamlit interface
```

---

## 🐛 Troubleshooting

### Issue: Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n nim-rag-agent

# Check events
kubectl get events -n nim-rag-agent --sort-by='.lastTimestamp'
```

### Issue: ImagePullBackOff

```bash
# Verify ECR image exists
aws ecr describe-images --repository-name nim-rag-agent --region us-east-2

# Check if nodes can pull from ECR
kubectl get pods -n nim-rag-agent -o jsonpath='{.items[*].status.containerStatuses[*].state.waiting.message}'
```

### Issue: LoadBalancer not getting EXTERNAL-IP

```bash
# Check service events
kubectl describe svc nim-rag-agent -n nim-rag-agent

# Usually just needs more time (wait 5 minutes)
```

### Issue: Terraform errors

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check terraform state
cd infrastructure/terraform
terraform state list
```

---

## 🧹 Cleanup (When Done)

### Delete Kubernetes resources:
```bash
kubectl delete namespace nim-rag-agent
```

### Destroy EKS infrastructure:
```bash
cd infrastructure/terraform
terraform destroy
```

**⚠️ IMPORTANT**: Make sure to destroy resources when done to avoid ongoing charges!

---

## 📝 Next Steps After Deployment

1. ✅ Update README.md with actual LoadBalancer URL
2. ✅ Take screenshots of running application
3. ✅ Record demo video showing:
   - Application running on AWS
   - kubectl commands showing pods
   - AWS console showing EKS cluster
4. ✅ Document actual costs incurred
5. ✅ Test all features work on AWS

---

## 🎯 Quick Reference Commands

```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A

# View application logs
kubectl logs -f deployment/nim-rag-agent -n nim-rag-agent

# Scale application
kubectl scale deployment nim-rag-agent -n nim-rag-agent --replicas=3

# Get LoadBalancer URL
kubectl get svc nim-rag-agent -n nim-rag-agent -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Check costs
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-03 --granularity DAILY --metrics UnblendedCost
```

---

## ⏱️ Timeline Estimate

- **AWS CLI setup**: 10 minutes
- **Terraform apply**: 20 minutes
- **Docker build & push**: 10 minutes
- **K8s deployment**: 10 minutes
- **Testing & verification**: 10 minutes

**Total**: ~60 minutes (1 hour)

---

## 💰 Cost Management

### Monitor costs:
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost
```

### Set up billing alerts:
1. AWS Console → Billing → Billing Preferences
2. Enable "Receive Billing Alerts"
3. Set budget alert at $100, $200, $400

---

**Ready to proceed?** Start with Step 1 (Install AWS CLI) above!
