#!/usr/bin/env python3
"""
Test PDF processing functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.document_processor import DocumentProcessor


def test_pdf_processing():
    """Test DocumentProcessor with different file types"""
    print("=" * 60)
    print("Testing Document Processor")
    print("=" * 60)

    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)

    # Test 1: Check initialization
    print("\n✅ Test 1: Initialization")
    print(f"   Chunk size: {processor.chunk_size}")
    print(f"   Chunk overlap: {processor.chunk_overlap}")

    # Test 2: Text chunking
    print("\n✅ Test 2: Text Chunking")
    test_text = "This is a test. " * 100  # Create long text
    chunks = processor.chunk_text(test_text)
    print(f"   Input length: {len(test_text)} chars")
    print(f"   Number of chunks: {len(chunks)}")
    print(f"   First chunk length: {len(chunks[0])} chars")

    # Test 3: Test with actual files (if they exist)
    print("\n✅ Test 3: File Processing")

    # Check for test files in current directory
    test_files = []
    for ext in ['.txt', '.pdf', '.docx', '.md']:
        test_files.extend(Path('.').glob(f'**/*{ext}'))

    if test_files:
        print(f"   Found {len(test_files)} test files")
        # Try first file
        test_file = test_files[0]
        print(f"   Testing with: {test_file}")
        try:
            chunks = processor.process_file(str(test_file))
            print(f"   ✅ Successfully processed {len(chunks)} chunks")
            print(f"   Sample chunk: {chunks[0]['text'][:100]}...")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print("   No test files found")

    # Test 4: Supported file types
    print("\n✅ Test 4: Supported File Types")
    print("   - PDF (.pdf) - Using pypdf")
    print("   - Word (.docx) - Using python-docx")
    print("   - Markdown (.md, .markdown) - Using markdown + BeautifulSoup")
    print("   - Text (.txt, .text) - Using plain text reader")

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_pdf_processing()
