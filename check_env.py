#!/usr/bin/env python3
"""Check if .env is configured correctly"""
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('NIM_API_KEY', '')

print("=" * 50)
print("Environment Check")
print("=" * 50)

if not api_key:
    print("❌ NIM_API_KEY is NOT set")
    print("   Action: Add NIM_API_KEY to .env file")
elif api_key == 'your_nvidia_api_key_here':
    print("❌ NIM_API_KEY is still the placeholder value")
    print("   Action: Replace with your actual NVIDIA API key")
else:
    print("✅ NIM_API_KEY is set")
    print(f"   First 10 characters: {api_key[:10]}...")
    print(f"   Length: {len(api_key)} characters")

print("\nOther settings:")
print(f"  NIM_MODEL: {os.getenv('NIM_MODEL', 'not set')}")
print(f"  NIM_EMBEDDING_MODEL: {os.getenv('NIM_EMBEDDING_MODEL', 'not set')}")
print("=" * 50)
