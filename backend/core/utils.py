"""
Utility functions for error handling, logging, and common operations.
"""

import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException

class APIError(Exception):
    """Custom API error with structured error information."""
    
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

def handle_api_error(error: Exception, context: str = "Unknown") -> HTTPException:
    """
    Convert various error types to HTTPException with proper logging.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred (for logging)
    
    Returns:
        HTTPException with appropriate status code and message
    """
    print(f"\n=== ERROR in {context} ===")
    traceback.print_exc()
    
    if isinstance(error, APIError):
        print(f"API Error: {error.message} (Code: {error.error_code})")
        return HTTPException(
            status_code=error.status_code,
            detail={
                "error": error.error_code,
                "message": error.message,
                "context": context,
                **error.details
            }
        )
    
    elif isinstance(error, ValueError):
        print(f"Validation Error: {str(error)}")
        return HTTPException(
            status_code=400,
            detail={
                "error": "VALIDATION_ERROR",
                "message": str(error),
                "context": context
            }
        )
    
    elif isinstance(error, FileNotFoundError):
        print(f"File Not Found: {str(error)}")
        return HTTPException(
            status_code=404,
            detail={
                "error": "FILE_NOT_FOUND",
                "message": str(error),
                "context": context
            }
        )
    
    else:
        print(f"Unexpected Error: {str(error)}")
        return HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please check the logs.",
                "context": context
            }
        )

def validate_required_env_vars(*env_vars: str) -> None:
    """
    Validate that required environment variables are set.
    
    Args:
        *env_vars: Variable names to check
        
    Raises:
        APIError: If any required environment variable is missing
    """
    import os
    
    missing_vars = []
    for var in env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise APIError(
            f"Missing required environment variables: {', '.join(missing_vars)}",
            error_code="MISSING_ENV_VARS",
            status_code=500,
            details={"missing_vars": missing_vars}
        )

def log_operation(operation: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an operation with structured information.
    
    Args:
        operation: Name of the operation
        details: Additional details to log
    """
    print(f"\n--- {operation} ---")
    if details:
        for key, value in details.items():
            print(f"{key}: {value}")
    print("---")

def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Optional data to include
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": import_datetime().datetime.now().isoformat()
    }
    
    if data:
        response.update(data)
    
    return response

def import_datetime():
    """Import datetime to avoid circular imports."""
    import datetime
    return datetime

def validate_chunk_ids(chunk_ids: list) -> None:
    """
    Validate that chunk IDs are provided and valid.
    
    Args:
        chunk_ids: List of chunk IDs to validate
        
    Raises:
        APIError: If chunk IDs are invalid
    """
    if not chunk_ids:
        raise APIError(
            "No relevant document chunks found for the given query.",
            error_code="NO_RELEVANT_CHUNKS",
            status_code=404
        )
    
    if not isinstance(chunk_ids, list):
        raise APIError(
            "Chunk IDs must be provided as a list.",
            error_code="INVALID_CHUNK_IDS",
            status_code=400
        )

def validate_json_response(response_text: str, context: str = "AI response") -> Dict[str, Any]:
    """
    Validate and parse JSON response from AI models.
    
    Args:
        response_text: Raw response text
        context: Context for error reporting
        
    Returns:
        Parsed JSON data
        
    Raises:
        APIError: If JSON is invalid
    """
    import json
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise APIError(
            f"Failed to parse JSON from {context}. Raw response: {response_text[:200]}...",
            error_code="INVALID_JSON_RESPONSE",
            status_code=500,
            details={"json_error": str(e), "raw_response": response_text[:500]}
        )