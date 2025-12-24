"""Image processing service for handling uploaded images."""

import base64
import io

from fastapi import UploadFile
from PIL import Image

from ..core.exceptions import ImageProcessingError


class ImageService:
    """Service for processing images before sending to AI."""

    @staticmethod
    async def process_upload_file(file: UploadFile) -> tuple[str, str]:
        """Process an uploaded file and convert to base64.

        Args:
            file: The uploaded file

        Returns:
            Tuple of (base64_data, content_type)

        Raises:
            ImageProcessingError: If image processing fails
        """
        try:
            # Read file content
            content = await file.read()

            # Convert to base64
            base64_data = base64.b64encode(content).decode("utf-8")

            # Reset file pointer
            await file.seek(0)

            return base64_data, file.content_type

        except Exception as e:
            raise ImageProcessingError(
                f"Failed to process image {file.filename}: {str(e)}",
                details={"filename": file.filename, "error": str(e)},
            ) from e

    @staticmethod
    async def process_multiple_files(files: list[UploadFile]) -> list[tuple[str, str, str]]:
        """Process multiple uploaded files.

        Args:
            files: List of uploaded files

        Returns:
            List of tuples (base64_data, content_type, filename)

        Raises:
            ImageProcessingError: If any image processing fails
        """
        processed_images = []

        for i, file in enumerate(files):
            try:
                base64_data, content_type = await ImageService.process_upload_file(file)
                processed_images.append((base64_data, content_type, file.filename or f"image_{i}"))
            except ImageProcessingError as e:
                # Add file index to error details
                if e.details:
                    e.details["file_index"] = i
                raise e

        return processed_images

    @staticmethod
    def optimize_image_for_ai(image_data: bytes, max_size: int = 1024) -> bytes:
        """Optimize image for AI processing by resizing if necessary.

        Args:
            image_data: Raw image data
            max_size: Maximum dimension in pixels

        Returns:
            Optimized image data

        Raises:
            ImageProcessingError: If optimization fails
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))

            # Calculate new size maintaining aspect ratio
            width, height = image.size
            if max(width, height) > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int((height * max_size) / width)
                else:
                    new_height = max_size
                    new_width = int((width * max_size) / height)

                # Resize image
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB if necessary (for JPEG)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Save optimized image
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)

            return output.getvalue()

        except Exception as e:
            raise ImageProcessingError(f"Failed to optimize image: {str(e)}", details={"error": str(e)}) from e

    @staticmethod
    def get_image_info(image_data: bytes) -> dict:
        """Get information about an image.

        Args:
            image_data: Raw image data

        Returns:
            Dictionary with image information
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": len(image_data),
            }
        except Exception:
            return {}
