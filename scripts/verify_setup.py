#!/usr/bin/env python3
"""
Verification script to check if the project is set up correctly
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_syntax():
    """Check Python syntax of all source files"""
    print("✓ Checking Python syntax...")
    try:
        import py_compile
        src_files = Path("src").rglob("*.py")
        for file in src_files:
            py_compile.compile(str(file), doraise=True)
        print("  ✓ All Python files have valid syntax")
        return True
    except Exception as e:
        print(f"  ✗ Syntax error: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n✓ Checking dependencies...")
    required = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'openai',
        'chromadb',
        'loguru',
        'tenacity',
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n  Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        return False
    return True


def check_configuration():
    """Check if configuration is set up correctly"""
    print("\n✓ Checking configuration...")

    # Check if .env exists
    if Path(".env").exists():
        print("  ✓ .env file exists")

        # Try to load settings
        try:
            from src.utils.config import settings

            if settings.nim_api_key:
                print("  ✓ NIM_API_KEY is set")
            else:
                print("  ⚠ NIM_API_KEY is empty (required for operation)")

            print(f"  ✓ Model: {settings.nim_model}")
            print(f"  ✓ ChromaDB: {settings.chroma_persist_dir}")
            return True
        except Exception as e:
            print(f"  ✗ Error loading configuration: {e}")
            return False
    else:
        print("  ⚠ .env file not found")
        print("  Create one from .env.example: cp .env.example .env")
        return True  # Not fatal, just a warning


def check_directories():
    """Check if required directories exist"""
    print("\n✓ Checking directory structure...")

    required_dirs = [
        "src",
        "src/agent",
        "src/nim_clients",
        "src/retrieval",
        "src/api",
        "frontend",
        "frontend/static",
        "tests",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} (missing)")
            all_exist = False

    return all_exist


def check_imports():
    """Check if modules can be imported"""
    print("\n✓ Checking module imports...")

    modules_to_test = [
        'src.utils.config',
        'src.nim_clients.llm_client',
        'src.nim_clients.embedding_client',
        'src.agent.tools',
        'src.retrieval.document_processor',
    ]

    all_imported = True
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            all_imported = False

    return all_imported


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("NIM RAG Agent - Setup Verification")
    print("=" * 60)

    results = []

    results.append(("Syntax", check_syntax()))
    results.append(("Directories", check_directories()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Configuration", check_configuration()))
    results.append(("Imports", check_imports()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Ensure NIM_API_KEY is set in .env")
        print("  2. Run: python -m uvicorn src.api.main:app --reload")
        print("  3. Visit: http://localhost:8000")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
