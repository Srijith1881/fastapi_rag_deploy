from langchain_community.document_loaders import PyMuPDFLoader
import logging

logger = logging.getLogger(__name__)

def load_pdf(file_path):
    """Load PDF and return documents"""
    try:
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        if not docs:
            raise ValueError("PDF is empty or unreadable")
        logger.info(f"✅ PDF loaded successfully: {file_path}")
        return docs
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"❌ Error loading PDF {file_path}: {e}")
        raise
