"""Custom exceptions for the VitAI application."""

from typing import Any


class VitAIException(Exception):
    """Base exception for VitAI application."""

    def __init__(self, message: str, error_code: str | None = None, details: dict[str, Any] | None = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ImageProcessingError(VitAIException):
    """Exception raised when image processing fails."""

    def __init__(
        self,
        message: str = "Failed to process image",
        error_code: str = "IMAGE_PROCESSING_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class OpenAIServiceError(VitAIException):
    """Exception raised when OpenAI service fails."""

    def __init__(
        self,
        message: str = "OpenAI service error",
        error_code: str = "OPENAI_SERVICE_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class InvalidFileTypeError(VitAIException):
    """Exception raised when uploaded file type is not allowed."""

    def __init__(
        self,
        message: str = "Invalid file type",
        error_code: str = "INVALID_FILE_TYPE",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class FileSizeExceededError(VitAIException):
    """Exception raised when uploaded file size exceeds limit."""

    def __init__(
        self,
        message: str = "File size exceeds limit",
        error_code: str = "FILE_SIZE_EXCEEDED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class NoImagesProvidedError(VitAIException):
    """Exception raised when no images are provided for analysis."""

    def __init__(
        self,
        message: str = "No images provided for analysis",
        error_code: str = "NO_IMAGES_PROVIDED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class AnalysisValidationError(VitAIException):
    """Exception raised when analysis validation fails."""

    def __init__(
        self,
        message: str = "Analysis validation failed",
        error_code: str = "ANALYSIS_VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
