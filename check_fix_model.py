#!/usr/bin/env python3
"""
Check and fix model name in .env file
"""

import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 60)
print("Current Configuration")
print("=" * 60)

nim_model = os.getenv("NIM_MODEL")
print(f"NIM_MODEL: {nim_model}")

if nim_model and not nim_model.startswith("nvidia/"):
    print("\n⚠️  Issue found: Model name missing 'nvidia/' prefix")
    print(f"   Current: {nim_model}")
    print(f"   Should be: nvidia/{nim_model}")
    print("\nFixing .env file...")

    # Read .env file
    with open(".env", "r") as f:
        lines = f.readlines()

    # Fix model name
    with open(".env", "w") as f:
        for line in lines:
            if line.startswith("NIM_MODEL=") and not "nvidia/" in line:
                # Extract just the model name part
                parts = line.strip().split("=", 1)
                if len(parts) == 2:
                    model_name = parts[1]
                    # Add nvidia/ prefix if not present
                    if not model_name.startswith("nvidia/"):
                        line = f"NIM_MODEL=nvidia/{model_name}\n"
            f.write(line)

    print("✅ Fixed! Updated .env file")

    # Reload and verify
    from importlib import reload
    import dotenv
    reload(dotenv)
    load_dotenv(override=True)

    new_model = os.getenv("NIM_MODEL")
    print(f"\n✅ New NIM_MODEL: {new_model}")
else:
    print("\n✅ Model name is correct!")

print("\n" + "=" * 60)
