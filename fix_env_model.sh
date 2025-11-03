#!/bin/bash
# Fix model name in .env file

echo "=================================================="
echo "Fixing Model Name in .env File"
echo "=================================================="

# Backup the original .env
cp .env .env.backup.$(date +%s)
echo "✅ Created backup of .env"

# Replace the model name
sed -i 's/llama-3_1-nemotron-nano-8b-v1/llama-3.1-nemotron-nano-8b-v1/g' .env

echo ""
echo "✅ Updated model name:"
echo "   FROM: llama-3_1-nemotron-nano-8b-v1 (underscores)"
echo "   TO:   llama-3.1-nemotron-nano-8b-v1 (dots)"
echo ""

# Verify the change
echo "Verifying change..."
if grep -q "llama-3.1-nemotron-nano-8b-v1" .env; then
    echo "✅ Model name successfully updated!"
else
    echo "❌ Update may have failed. Check .env manually."
fi

echo ""
echo "=================================================="
echo "Next: Restart Streamlit app to apply changes"
echo "=================================================="
