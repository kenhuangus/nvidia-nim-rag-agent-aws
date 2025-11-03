"""
Unit tests for document processor
"""

import pytest
from src.retrieval.document_processor import DocumentProcessor


def test_chunk_text_small():
    """Test chunking with text smaller than chunk size"""
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=10)
    text = "This is a small text."
    chunks = processor.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_large():
    """Test chunking with text larger than chunk size"""
    processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
    text = "This is a longer text. " * 20  # Create a long text

    chunks = processor.chunk_text(text)

    assert len(chunks) > 1
    # Check overlap
    for i in range(len(chunks) - 1):
        assert len(chunks[i]) <= 50 or '.' in chunks[i][-10:]


def test_chunk_text_empty():
    """Test chunking with empty text"""
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=10)
    text = ""
    chunks = processor.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0] == ""


def test_read_text(tmp_path):
    """Test reading text file"""
    processor = DocumentProcessor()

    # Create a temporary text file
    test_file = tmp_path / "test.txt"
    test_content = "This is a test file."
    test_file.write_text(test_content)

    # Read the file
    content = processor.read_text(str(test_file))

    assert content == test_content


def test_process_file(tmp_path):
    """Test processing a file"""
    processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

    # Create a temporary text file
    test_file = tmp_path / "test.txt"
    test_content = "This is a test file. " * 10
    test_file.write_text(test_content)

    # Process the file
    processed = processor.process_file(str(test_file))

    assert len(processed) > 0
    assert all('text' in chunk for chunk in processed)
    assert all('metadata' in chunk for chunk in processed)
    assert all(chunk['metadata']['filename'] == 'test.txt' for chunk in processed)
