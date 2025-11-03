#!/usr/bin/env python3
"""
Check and show correct model name configuration
"""

print("=" * 60)
print("MODEL NAME CONFIGURATION FIX")
print("=" * 60)

print("\n⚠️  ISSUE DETECTED:")
print("Your .env file has the wrong model name format\n")

print("❌ INCORRECT (what you have):")
print("   NIM_MODEL=llama-3_1-nemotron-nano-8b-v1")
print("   (uses underscores: 3_1 and wrong suffix: -v1)\n")

print("✅ CORRECT (what it should be):")
print("   NIM_MODEL=llama-3.1-nemotron-nano-8b-instruct")
print("   (uses dots: 3.1 and correct suffix: -instruct)\n")

print("=" * 60)
print("HOW TO FIX:")
print("=" * 60)
print("1. Edit your .env file:")
print("   nano .env")
print()
print("2. Find the line:")
print("   NIM_MODEL=llama-3_1-nemotron-nano-8b-v1")
print()
print("3. Change it to:")
print("   NIM_MODEL=llama-3.1-nemotron-nano-8b-instruct")
print()
print("4. Save (Ctrl+X, Y, Enter)")
print()
print("5. I will then restart the Streamlit app for you")
print("=" * 60)
