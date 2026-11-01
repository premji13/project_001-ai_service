"""Document processing: file extraction, chunking, and text preprocessing."""
import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.chatbot.config import CHUNK_SIZE, CHUNK_OVERLAP, ALLOWED_EXTENSIONS


class DocumentProcessor:
    """Process documents (txt, pdf, docx, doc) into chunks."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text(self, file_path: str) -> str:
        """Extract text from various file formats."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.txt':
            return self._extract_txt(file_path)
        elif ext == '.pdf':
            return self._extract_pdf(file_path)
        elif ext in {'.doc', '.docx'}:
            return self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from .txt file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from .pdf file."""
        from pypdf import PdfReader
        text = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from .docx or .doc file."""
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        if not text or not text.strip():
            raise ValueError("Empty document text")
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            raise ValueError("Could not chunk document")
        return chunks

    def process_file(self, file_path: str) -> List[str]:
        """Full pipeline: extract text and chunk."""
        text = self.extract_text(file_path)
        return self.chunk_text(text)
