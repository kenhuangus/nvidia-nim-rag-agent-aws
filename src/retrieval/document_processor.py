"""
Document processing and ingestion pipeline
"""

from typing import List, Dict, Optional
from pathlib import Path
import asyncio
from loguru import logger

# Document parsers
import pypdf
from docx import Document as DocxDocument
import markdown
from bs4 import BeautifulSoup


class DocumentProcessor:
    """Process and chunk documents for ingestion"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Initialized DocumentProcessor (chunk_size={chunk_size}, overlap={chunk_overlap})")

    def read_pdf(self, file_path: str) -> str:
        """
        Read text from PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise

    def read_docx(self, file_path: str) -> str:
        """
        Read text from DOCX file

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text
        """
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            raise

    def read_markdown(self, file_path: str) -> str:
        """
        Read text from Markdown file

        Args:
            file_path: Path to Markdown file

        Returns:
            Extracted text (converted to plain text)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_text = file.read()
                html = markdown.markdown(md_text)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
            return text
        except Exception as e:
            logger.error(f"Error reading Markdown {file_path}: {e}")
            raise

    def read_text(self, file_path: str) -> str:
        """
        Read plain text file

        Args:
            file_path: Path to text file

        Returns:
            File contents
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise

    def read_file(self, file_path: str) -> str:
        """
        Read file based on extension

        Args:
            file_path: Path to file

        Returns:
            Extracted text
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.pdf':
            return self.read_pdf(file_path)
        elif extension == '.docx':
            return self.read_docx(file_path)
        elif extension in ['.md', '.markdown']:
            return self.read_markdown(file_path)
        elif extension in ['.txt', '.text']:
            return self.read_text(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}. Treating as text.")
            return self.read_text(file_path)

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                last_period = chunk.rfind('. ')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def process_file(self, file_path: str) -> List[Dict]:
        """
        Process a file into chunks with metadata

        Args:
            file_path: Path to file

        Returns:
            List of dicts with 'text' and 'metadata' keys
        """
        try:
            # Read file
            text = self.read_file(file_path)

            # Chunk text
            chunks = self.chunk_text(text)

            # Add metadata
            path = Path(file_path)
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                processed_chunks.append({
                    'text': chunk,
                    'metadata': {
                        'source': str(path),
                        'filename': path.name,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                    }
                })

            logger.info(f"Processed {path.name} into {len(chunks)} chunks")
            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    def process_directory(self, directory_path: str, file_pattern: str = "*.*") -> List[Dict]:
        """
        Process all matching files in a directory

        Args:
            directory_path: Path to directory
            file_pattern: Glob pattern for files (default: all files)

        Returns:
            List of processed chunks from all files
        """
        try:
            path = Path(directory_path)
            all_chunks = []

            for file_path in path.glob(file_pattern):
                if file_path.is_file():
                    try:
                        chunks = self.process_file(str(file_path))
                        all_chunks.extend(chunks)
                    except Exception as e:
                        logger.warning(f"Skipping file {file_path}: {e}")
                        continue

            logger.info(f"Processed {len(all_chunks)} total chunks from directory")
            return all_chunks

        except Exception as e:
            logger.error(f"Error processing directory {directory_path}: {e}")
            raise
