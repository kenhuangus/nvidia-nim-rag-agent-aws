#!/bin/bash
# AWS Configuration Helper Script

echo "========================================="
echo "AWS Credentials Configuration"
echo "========================================="
echo ""

# Source the .env file to check for credentials
if [ -f .env ]; then
    # Try to read AWS credentials from .env
    AWS_ACCESS_KEY=$(grep "^AWS_ACCESS_KEY_ID=" .env | cut -d'=' -f2 | tr -d ' ')
    AWS_SECRET_KEY=$(grep "^AWS_SECRET_ACCESS_KEY=" .env | cut -d'=' -f2 | tr -d ' ')
    AWS_REGION=$(grep "^AWS_REGION=" .env | cut -d'=' -f2 | tr -d ' ')

    # Check if credentials are set (not commented or empty)
    if [ -z "$AWS_ACCESS_KEY" ] || [ "$AWS_ACCESS_KEY" = "#" ]; then
        echo "⚠️  AWS credentials not found in .env file"
        echo ""
        echo "Please configure your AWS credentials in one of these ways:"
        echo ""
        echo "Option 1: Update .env file"
        echo "=========================="
        echo "Edit .env and add:"
        echo "AWS_ACCESS_KEY_ID=your-access-key-id"
        echo "AWS_SECRET_ACCESS_KEY=your-secret-access-key"
        echo "AWS_REGION=us-east-2"
        echo ""
        echo "Option 2: Use aws configure"
        echo "==========================="
        echo "Run: ./venv/bin/aws configure"
        echo ""
        echo "Option 3: Set environment variables"
        echo "===================================="
        echo "export AWS_ACCESS_KEY_ID=your-access-key-id"
        echo "export AWS_SECRET_ACCESS_KEY=your-secret-access-key"
        echo "export AWS_REGION=us-east-2"
        echo ""
        echo "========================================="
        echo ""
        echo "To get AWS credentials:"
        echo "1. Login to https://console.aws.amazon.com"
        echo "2. Go to: IAM → Users → Your Username → Security Credentials"
        echo "3. Click 'Create access key' → Select 'CLI'"
        echo "4. Save the Access Key ID and Secret Access Key"
        echo ""
        exit 1
    fi

    # Configure AWS CLI with credentials from .env
    echo "✅ Found AWS credentials in .env file"
    echo ""
    echo "Region: $AWS_REGION"
    echo "Access Key: ${AWS_ACCESS_KEY:0:8}..."
    echo ""

    # Export for current shell
    export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_KEY"
    export AWS_DEFAULT_REGION="$AWS_REGION"

    # Configure AWS CLI
    mkdir -p ~/.aws

    # Create credentials file
    cat > ~/.aws/credentials <<EOF
[default]
aws_access_key_id = $AWS_ACCESS_KEY
aws_secret_access_key = $AWS_SECRET_KEY
EOF

    # Create config file
    cat > ~/.aws/config <<EOF
[default]
region = $AWS_REGION
output = json
EOF

    echo "✅ AWS CLI configured successfully"
    echo ""

    # Test credentials
    echo "Testing AWS credentials..."
    if ./venv/bin/aws sts get-caller-identity > /tmp/aws_identity.json 2>&1; then
        echo "✅ AWS credentials are valid!"
        echo ""
        cat /tmp/aws_identity.json
        echo ""
        rm -f /tmp/aws_identity.json
    else
        echo "❌ AWS credentials test failed!"
        echo ""
        cat /tmp/aws_identity.json
        echo ""
        rm -f /tmp/aws_identity.json
        exit 1
    fi

else
    echo "❌ .env file not found!"
    echo ""
    echo "Please create .env file with AWS credentials:"
    echo "AWS_ACCESS_KEY_ID=your-access-key-id"
    echo "AWS_SECRET_ACCESS_KEY=your-secret-access-key"
    echo "AWS_REGION=us-east-2"
    exit 1
fi

echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Create terraform.tfvars file"
echo "   cd infrastructure/terraform"
echo "   cp terraform.tfvars.example terraform.tfvars"
echo ""
echo "2. Review infrastructure plan"
echo "   terraform plan"
echo ""
echo "3. Deploy to AWS (costs ~$450/month)"
echo "   terraform apply"
echo ""
echo "========================================="
