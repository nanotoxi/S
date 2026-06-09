import fitz  # PyMuPDF
import docx2txt
import logging
import os

logger = logging.getLogger(__name__)

class ResumeParser:
    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                return ResumeParser._extract_from_pdf(file_path)
            elif ext == '.docx':
                return ResumeParser._extract_from_docx(file_path)
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        return docx2txt.process(file_path)

resume_parser = ResumeParser()
