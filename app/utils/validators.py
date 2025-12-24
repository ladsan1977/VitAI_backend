"""Validation utilities for file uploads and data validation."""

import io

from fastapi import UploadFile
from PIL import Image

from ..config import settings
from ..core.exceptions import FileSizeExceededError, InvalidFileTypeError


async def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file.

    Args:
        file: The uploaded file to validate

    Raises:
        InvalidFileTypeError: If file type is not allowed
        FileSizeExceededError: If file size exceeds limit
    """
    # Check file size
    content = await file.read()
    file_size = len(content)

    if file_size > settings.max_file_size:
        raise FileSizeExceededError(
            f"File size {file_size} bytes exceeds maximum allowed size {settings.max_file_size} bytes",
            details={"file_size": file_size, "max_size": settings.max_file_size},
        )

    # Reset file pointer
    await file.seek(0)

    # Check MIME type
    if file.content_type not in settings.allowed_image_types:
        raise InvalidFileTypeError(
            f"File type {file.content_type} is not allowed",
            details={"provided_type": file.content_type, "allowed_types": settings.allowed_image_types},
        )

    # Validate that it's actually an image by trying to open it
    try:
        image_data = io.BytesIO(content)
        with Image.open(image_data) as img:
            # Verify it's a valid image
            img.verify()
    except Exception as e:
        raise InvalidFileTypeError(f"File is not a valid image: {str(e)}", details={"validation_error": str(e)}) from e

    # Reset file pointer for later use
    await file.seek(0)


async def validate_multiple_images(files: list[UploadFile]) -> None:
    """Validate multiple uploaded image files.

    Args:
        files: List of uploaded files to validate

    Raises:
        InvalidFileTypeError: If any file type is not allowed
        FileSizeExceededError: If any file size exceeds limit
    """
    if not files:
        return

    for i, file in enumerate(files):
        try:
            await validate_image_file(file)
        except (InvalidFileTypeError, FileSizeExceededError) as e:
            # Add file index to error details
            if e.details:
                e.details["file_index"] = i
                e.details["filename"] = file.filename
            raise e


def validate_analysis_request_data(data: dict) -> dict:
    """Validate and sanitize analysis request data.

    Args:
        data: Raw request data

    Returns:
        Sanitized and validated data
    """
    # Remove empty or None values
    cleaned_data = {k: v for k, v in data.items() if v is not None and v != ""}

    # Validate analysis_type
    valid_analysis_types = ["nutrition", "ingredients", "complete"]
    if "analysis_type" in cleaned_data:
        if cleaned_data["analysis_type"] not in valid_analysis_types:
            cleaned_data["analysis_type"] = "complete"

    # Ensure lists are actual lists
    list_fields = ["dietary_preferences", "health_conditions"]
    for field in list_fields:
        if field in cleaned_data:
            if isinstance(cleaned_data[field], str):
                # Convert comma-separated string to list
                cleaned_data[field] = [item.strip() for item in cleaned_data[field].split(",")]
            elif not isinstance(cleaned_data[field], list):
                cleaned_data[field] = []

    return cleaned_data
