"""
Extraction manager that handles meeting data extraction.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from config.config import get_settings
from src.services.extraction.config import DEFAULT_MEETING_DATA, REQUIRED_MEETING_FIELDS
from src.utils import (
    get_logger,
    log_async_function_call,
    format_structured_log
)
from src.utils.exceptions import (
    ExtractionError,
    InsufficientDataError,
    ValidationError
)
from src.enums import ExtractionStatus


logger = get_logger(__name__)

class ExtractionManager:
    """
    Manager class for extracting structured meeting data from text.
    Primary implementation uses LLM-based extraction.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the extraction manager.
        
        Args:
            openai_api_key: API key for OpenAI (if None, read from settings)
            model: OpenAI model to use (defaults to configuration value)
            
        Raises:
            ValidationError: If API key is required but not provided
        """
        # Generate unique ID for this extraction manager instance
        self.instance_id = str(uuid.uuid4())[:8]
        logger.info(f"Initializing ExtractionManager instance {self.instance_id}")
        
        try:
            # If api_key is not provided, get from settings
            if not openai_api_key:
                settings = get_settings()
                self.openai_api_key = settings.OPENAI_API_KEY
            else:
                self.openai_api_key = openai_api_key
                
            self.model = model
            
            # Lazy load the LLM extractor when needed
            self._llm_extractor = None
            
            logger.debug(
                format_structured_log(
                    f"ExtractionManager initialized",
                    {
                        "instance_id": self.instance_id,
                        "model": self.model
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Error initializing ExtractionManager: {str(e)}", exc_info=True)
            raise ValidationError(
                "Failed to initialize extraction manager",
                original_exception=e
            )
    
    @log_async_function_call(logger)
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract meeting data from text.
        
        Args:
            text: Transcribed meeting text
            
        Returns:
            Dictionary containing extracted meeting data
            
        Raises:
            ExtractionError: If extraction fails
            InsufficientDataError: If extracted data is incomplete
        """
        # Create an extraction ID to trace this specific extraction request
        extraction_id = f"extract_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Initialize with default values
        result = DEFAULT_MEETING_DATA.copy()
        result["notes"] = text
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["extraction_status"] = ExtractionStatus.PENDING.value
        
        logger.info(
            format_structured_log(
                f"Starting extraction process [{extraction_id}]",
                {"text_length": len(text), "instance_id": self.instance_id}
            )
        )
        
        try:
            if not self.openai_api_key:
                raise ValidationError("OpenAI API key not provided and not found in environment")
            
            result["extraction_status"] = ExtractionStatus.PROCESSING.value
            
            # Lazy initialize the LLM extractor
            if not self._llm_extractor:
                from src.services.extraction.llm_extractor import LLMExtractor
                self._llm_extractor = LLMExtractor(
                    api_key=self.openai_api_key, 
                    model=self.model
                )
            
            logger.info(
                format_structured_log(
                    f"Using LLM extraction [{extraction_id}]",
                    {"model": self._llm_extractor.model}
                )
            )
            
            llm_result = await self._llm_extractor.extract(text)
            
            # Update our result with the extracted data
            for key in DEFAULT_MEETING_DATA.keys():
                if key in llm_result and llm_result[key] is not None:
                    result[key] = llm_result[key]
            
            if self._is_complete_extraction(result):
                result["extraction_status"] = ExtractionStatus.COMPLETE.value
                logger.info(
                    format_structured_log(
                        f"Extraction successful [{extraction_id}]",
                        {
                            "customer": result.get("customer_name"),
                            "date": result.get("meeting_date"),
                            "total_hours": result.get("total_hours"),
                            "status": result["extraction_status"]
                        }
                    )
                )
            else:
                result["extraction_status"] = ExtractionStatus.INCOMPLETE.value
                
                missing_fields = [
                    field for field in REQUIRED_MEETING_FIELDS 
                    if result.get(field) is None
                ]
                logger.warning(
                    format_structured_log(
                        f"Incomplete extraction [{extraction_id}]",
                        {
                            "missing_fields": missing_fields,
                            "status": result["extraction_status"]
                        }
                    )
                )
                
                # Only raise exception if explicitly requested by caller
                # (By default we return incomplete data with warnings logged)
                # Uncomment this to fail on incomplete extractions
                # raise InsufficientDataError(
                #     "Extracted data is incomplete",
                #     details={
                #         "missing_fields": missing_fields,
                #         "extraction_id": extraction_id
                #     }
                # )
                
        except Exception as e:
            result["extraction_status"] = ExtractionStatus.FAILED.value
            
            error_msg = f"Extraction error: {str(e)}"
            logger.error(
                format_structured_log(
                    f"{error_msg} [{extraction_id}]",
                    {
                        "instance_id": self.instance_id,
                        "status": result["extraction_status"]
                    }
                ),
                exc_info=True
            )
            
            result["extraction_error"] = str(e)
            
            # TODO
            # Decide whether to propagate the exception or return partial results
            # By default, we're returning partial results with an error flag
            # If you want to always raise exceptions, uncomment this
            # if not isinstance(e, InsufficientDataError):
            #     raise ExtractionError(
            #         error_msg,
            #         details={
            #             "extraction_id": extraction_id,
            #             "status": result["extraction_status"]
            #         },
            #         original_exception=e
            #     )
        
        return result
    
    def _is_complete_extraction(self, result: Dict[str, Any]) -> bool:
        """
        Check if the extraction result has all required fields.
        
        Args:
            result: Extraction result to check
            
        Returns:
            True if all required fields are present, False otherwise
        """
        return all(result.get(field) is not None for field in REQUIRED_MEETING_FIELDS)