# Quick Deployment Guide

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Docker installed
- [ ] AWS CLI configured
- [ ] kubectl installed
- [ ] Terraform installed
- [ ] NVIDIA API key obtained
- [ ] AWS account with EKS permissions

## Option 1: Local Development (5 minutes)

### Step 1: Environment Setup
```bash
# Clone repository
git clone <your-repo>
cd aws-contest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your NVIDIA API key
# NIM_API_KEY=nvapi-xxxxxxxxxxxxx
```

### Step 3: Run Application
```bash
# Start the server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Access at http://localhost:8000
```

## Option 2: Docker Deployment (10 minutes)

### Step 1: Build Image
```bash
# Build Docker image
docker build -t nim-rag-agent:latest .
```

### Step 2: Run with Docker Compose
```bash
# Set environment variable
export NIM_API_KEY=nvapi-xxxxxxxxxxxxx

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access at http://localhost:8000
```

### Step 3: Test
```bash
# Health check
curl http://localhost:8000/health

# Query agent
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

## Option 3: AWS EKS Production Deployment (60 minutes)

### Phase 1: Infrastructure Setup (30 minutes)

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates VPC, EKS cluster, node groups)
terraform apply -auto-approve

# Wait for cluster creation (15-20 minutes)
```

### Phase 2: Docker Image (10 minutes)

```bash
# Return to project root
cd ../..

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Create ECR repository
aws ecr create-repository \
  --repository-name nim-rag-agent \
  --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and tag image
docker build -t nim-rag-agent:latest .
docker tag nim-rag-agent:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nim-rag-agent:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nim-rag-agent:latest
```

### Phase 3: Kubernetes Deployment (20 minutes)

```bash
# Configure kubectl
aws eks update-kubeconfig \
  --region us-east-1 \
  --name nim-rag-agent-cluster

# Verify connection
kubectl get nodes

# Navigate to Kubernetes directory
cd infrastructure/kubernetes

# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your NVIDIA API key
kubectl apply -f secrets.yaml

# Deploy application
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml

# Update deployment.yaml with your ECR image URL
# Then deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

# Wait for pods to be ready (5-10 minutes)
kubectl get pods -n nim-rag-agent -w
```

### Phase 4: Access Application

```bash
# Get LoadBalancer URL
kubectl get svc nim-rag-agent -n nim-rag-agent

# The EXTERNAL-IP is your application URL
# Example: a1b2c3d4e5.us-east-1.elb.amazonaws.com
```

## Verification Steps

### 1. Health Check
```bash
# Local
curl http://localhost:8000/health

# AWS
LOAD_BALANCER_URL=$(kubectl get svc nim-rag-agent -n nim-rag-agent -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LOAD_BALANCER_URL/health
```

### 2. Test Query
```bash
curl -X POST http://$LOAD_BALANCER_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is artificial intelligence?"}'
```

### 3. Ingest Test Document
```bash
curl -X POST http://$LOAD_BALANCER_URL/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is the simulation of human intelligence by machines.",
    "metadata": {"source": "test"}
  }'
```

### 4. Web Interface
Open browser and navigate to:
- Local: http://localhost:8000
- AWS: http://$LOAD_BALANCER_URL

## Monitoring

### Check Pod Status
```bash
# View pods
kubectl get pods -n nim-rag-agent

# View logs
kubectl logs -f deployment/nim-rag-agent -n nim-rag-agent

# Describe pod for issues
kubectl describe pod <pod-name> -n nim-rag-agent
```

### Check Autoscaling
```bash
# View HPA status
kubectl get hpa -n nim-rag-agent

# Watch HPA events
kubectl get hpa -n nim-rag-agent -w
```

### Check Service
```bash
# View service details
kubectl describe svc nim-rag-agent -n nim-rag-agent

# Get endpoint
kubectl get endpoints -n nim-rag-agent
```

## Common Issues and Solutions

### Issue: Pods Not Starting

**Symptom**: Pods stuck in Pending or CrashLoopBackOff

**Solutions**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n nim-rag-agent

# Check logs
kubectl logs <pod-name> -n nim-rag-agent

# Common fixes:
# 1. Verify image exists in ECR
# 2. Check secrets are created
# 3. Verify sufficient resources
# 4. Check node affinity/tolerations
```

### Issue: Cannot Access LoadBalancer

**Symptom**: LoadBalancer EXTERNAL-IP is pending

**Solutions**:
```bash
# Check service
kubectl describe svc nim-rag-agent -n nim-rag-agent

# Common fixes:
# 1. Wait 5-10 minutes for provisioning
# 2. Check AWS ELB console
# 3. Verify security groups
# 4. Check VPC subnet tags
```

### Issue: 500 Errors from API

**Symptom**: API returns 500 Internal Server Error

**Solutions**:
```bash
# Check application logs
kubectl logs -f deployment/nim-rag-agent -n nim-rag-agent

# Common fixes:
# 1. Verify NIM_API_KEY is correct
# 2. Check NVIDIA API status
# 3. Verify PVC is mounted
# 4. Check resource limits
```

### Issue: Out of Memory

**Symptom**: Pods getting OOMKilled

**Solutions**:
```bash
# Increase memory limits in deployment.yaml
# Update limits:
#   memory: "8Gi"  # Instead of 4Gi

kubectl apply -f deployment.yaml
```

## Cleanup

### Remove Application from EKS
```bash
# Delete namespace (removes all resources)
kubectl delete namespace nim-rag-agent
```

### Destroy Infrastructure
```bash
cd infrastructure/terraform
terraform destroy -auto-approve
```

**Warning**: This will delete:
- EKS cluster
- VPC and subnets
- NAT gateways
- Load balancers
- All associated costs will stop

### Local Cleanup
```bash
# Stop Docker Compose
docker-compose down -v

# Remove virtual environment
deactivate
rm -rf venv

# Remove data
rm -rf data/
```

## Cost Optimization Tips

1. **Use Spot Instances**: Modify node groups to use spot instances for non-critical workloads
2. **Right-size Resources**: Adjust pod resource requests/limits based on actual usage
3. **Scale Down**: Reduce min replicas during off-hours
4. **Use Single NAT**: Modify Terraform to use single NAT gateway
5. **Stop When Not Needed**: Stop EKS cluster when not in use (destroys nodes only)

## Next Steps

After successful deployment:

1. **Ingest Documents**: Upload your knowledge base
   ```bash
   python scripts/ingest_documents.py --directory /path/to/docs
   ```

2. **Test Queries**: Try various questions through the UI

3. **Monitor Performance**: Watch logs and metrics

4. **Scale**: Adjust HPA settings based on load

5. **Customize**: Add new tools and capabilities

6. **Secure**: Add authentication and HTTPS

## Support

- Check logs: `kubectl logs`
- Review pod events: `kubectl describe pod`
- Test endpoints: Use `/docs` for API documentation
- Check README.md for detailed information
- Review ARCHITECTURE.md for system design

## Estimated Deployment Times

| Method | Time | Complexity |
|--------|------|------------|
| Local Dev | 5 min | Easy |
| Docker | 10 min | Easy |
| AWS EKS | 60 min | Medium |

## Resource Requirements

| Deployment | RAM | CPU | Storage |
|------------|-----|-----|---------|
| Local | 4GB | 2 cores | 10GB |
| Docker | 4GB | 2 cores | 10GB |
| AWS EKS | 8GB+ | 4+ cores | 20GB+ |
