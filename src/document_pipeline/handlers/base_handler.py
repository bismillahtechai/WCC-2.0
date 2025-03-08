from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentHandler(ABC):
    """
    Base abstract class for document handlers.
    All document type handlers should inherit from this class.
    """
    
    @abstractmethod
    def process(self, file_path: Union[str, Path]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Process a document file and extract text and metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple containing:
            - The extracted text content
            - Dictionary of metadata (or None if no metadata is extracted)
        """
        pass
    
    @abstractmethod
    def get_supported_mime_types(self) -> list[str]:
        """
        Get the list of MIME types supported by this handler.
        
        Returns:
            List of supported MIME types
        """
        pass
    
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract metadata from a document. This default implementation
        returns minimal metadata. Subclasses should override this method
        to provide document-type specific metadata extraction.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary of metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # Default metadata is just file info
        metadata = {
            "file_size": file_path.stat().st_size,
            "file_name": file_path.name,
        }
        
        return metadata 