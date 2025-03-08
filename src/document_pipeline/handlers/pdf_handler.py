import logging
import os
from typing import Dict, Any, Tuple, Optional, Union, List
from pathlib import Path
import tempfile
import io

try:
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError("PyPDF2 is required for PDF processing. Install it with: pip install PyPDF2")

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logging.warning("OCR dependencies not found. PDF OCR will not be available. "
                   "Install with: pip install pytesseract pdf2image pillow")

from .base_handler import DocumentHandler

logger = logging.getLogger(__name__)

class PDFHandler(DocumentHandler):
    """
    Handler for PDF documents. Extracts text directly from PDF if possible,
    falls back to OCR if text extraction fails and OCR dependencies are available.
    """
    
    def __init__(self, enable_ocr: bool = True, ocr_language: str = 'eng'):
        """
        Initialize the PDF handler.
        
        Args:
            enable_ocr: Whether to enable OCR for image-based PDFs
            ocr_language: Language for OCR (default: English)
        """
        self.enable_ocr = enable_ocr and HAS_OCR
        self.ocr_language = ocr_language
        
        if self.enable_ocr and not HAS_OCR:
            logger.warning("OCR dependencies not available. OCR will be disabled.")
            self.enable_ocr = False
            
    def get_supported_mime_types(self) -> List[str]:
        """Get the supported MIME types for this handler."""
        return ['application/pdf']
        
    def process(self, file_path: Union[str, Path]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Process a PDF file and extract text and metadata.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple containing:
            - The extracted text content
            - Dictionary of metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        logger.info(f"Processing PDF: {file_path}")
        
        # Extract metadata
        metadata = self.extract_metadata(file_path)
        
        # Extract text
        text = self._extract_text(file_path)
        
        # If text extraction failed and OCR is enabled, try OCR
        if not text and self.enable_ocr:
            logger.info(f"No text extracted from PDF {file_path}. Trying OCR...")
            text = self._perform_ocr(file_path)
            
        # If we still don't have text, provide a message
        if not text:
            logger.warning(f"Failed to extract text from PDF: {file_path}")
            text = f"[No text could be extracted from PDF: {file_path.name}]"
            
        return text, metadata
        
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract metadata from a PDF document.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary of metadata
        """
        # Start with base metadata
        metadata = super().extract_metadata(file_path)
        
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                info = reader.metadata
                
                if info:
                    # Extract standard PDF metadata
                    for key in info:
                        # Clean up the key name by removing leading slash
                        clean_key = key
                        if isinstance(key, str) and key.startswith('/'):
                            clean_key = key[1:]
                            
                        # Add to metadata dict if value exists
                        if info[key]:
                            metadata[clean_key] = str(info[key])
                
                # Add page count
                metadata['page_count'] = len(reader.pages)
                
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF {file_path}: {str(e)}")
            
        return metadata
        
    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text directly from the PDF using PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text or empty string if extraction fails
        """
        text = ""
        
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            
        return text.strip()
        
    def _perform_ocr(self, file_path: Path) -> str:
        """
        Perform OCR on a PDF file using Tesseract.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text from OCR
        """
        if not self.enable_ocr or not HAS_OCR:
            return ""
            
        text = ""
        
        try:
            # Create a temporary directory for the images
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert PDF to images
                images = convert_from_path(
                    file_path,
                    output_folder=temp_dir,
                    fmt="png",
                    dpi=300
                )
                
                # Perform OCR on each image
                for i, image in enumerate(images):
                    try:
                        page_text = pytesseract.image_to_string(
                            image, 
                            lang=self.ocr_language,
                            config='--psm 1'  # Automatic page segmentation
                        )
                        if page_text:
                            text += f"\n--- Page {i + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"OCR failed on page {i + 1}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"OCR processing failed for PDF {file_path}: {str(e)}")
            
        return text.strip() 