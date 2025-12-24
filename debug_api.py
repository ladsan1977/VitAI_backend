import asyncio
import sys
from pathlib import Path

from app.config import settings
from app.services.openai_service import OpenAIService

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_full_flow():
    """Test the complete OpenAI service flow."""

    print("=" * 60)
    print("DEBUG: Testing OpenAI Service")
    print("=" * 60)

    print("\n1. Configuration Check:")
    print(f"   Model: {settings.openai_model}")
    print(f"   Max Output Tokens: {settings.openai_max_output_tokens}")
    print(f"   Temperature: {settings.openai_temperature}")
    print(f"   API Key set: {bool(settings.openai_api_key)}")
    print(f"   API Key length: {len(settings.openai_api_key) if settings.openai_api_key else 0}")

    # Initialize service
    print("\n2. Initializing OpenAI Service...")
    try:
        service = OpenAIService()
        print("   ✅ Service initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    # Test building prompt
    print("\n3. Testing prompt building...")
    try:
        prompt = service._build_analysis_prompt(
            analysis_type="complete", user_profile=None, dietary_preferences=None, health_conditions=None
        )
        print(f"   ✅ Prompt built (length: {len(prompt)} chars)")
        print(f"   First 200 chars: {prompt[:200]}...")
    except Exception as e:
        print(f"   ❌ Failed to build prompt: {e}")
        import traceback

        traceback.print_exc()
        return

    # Create a simple test image (1x1 white pixel PNG in base64)
    print("\n4. Creating test image...")
    test_image_base64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    test_images = [(test_image_base64, "image/png", "test.png")]

    # Test image preparation
    print("\n5. Testing image preparation...")
    try:
        image_messages = service._prepare_image_messages(test_images)
        print(f"   ✅ Images prepared: {len(image_messages)} images")
        print(f"   Image message structure: {image_messages[0].keys()}")
        print(f"   Image type: {image_messages[0].get('type')}")
    except Exception as e:
        print(f"   ❌ Failed to prepare images: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test API call (this is where the issue likely is)
    print("\n6. Testing OpenAI API call...")
    print(f"   Using model: {settings.openai_model}")
    print(f"   Max output tokens: {settings.openai_max_output_tokens}")

    try:
        # Use a simple prompt for testing
        test_prompt = "Analiza esta imagen de etiqueta nutricional."

        print("   Calling responses.create()...")
        response_data, token_usage = await service._real_openai_call(
            prompt=test_prompt, image_messages=image_messages, analysis_type="complete"
        )

        print("   ✅ API call successful!")
        print(f"   Response keys: {list(response_data.keys())[:5]}...")
        print(f"   Token usage: {token_usage}")

    except Exception as e:
        print("   ❌ API call failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print("\n   Full traceback:")
        import traceback

        traceback.print_exc()

        # Try to get more details
        if hasattr(e, "__dict__"):
            print(f"\n   Error attributes: {e.__dict__}")

        return

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
