from fastapi import HTTPException
from typing import List
import os

def validate_file_size(file_size: int, max_size: int):
    """Validate file size"""
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        )

def validate_file_extension(filename: str, allowed_extensions: List[str]):
    """Validate file extension"""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} not allowed. Allowed extensions: {allowed_extensions}"
        )
