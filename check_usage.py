"""Check the ResponseUsage structure."""
import asyncio
import os

from openai import AsyncOpenAI


async def check_usage_structure():
    client = AsyncOpenAI(api_key=os.getenv("OPEN_AI_KEY"))

    response = await client.responses.create(
        model="gpt-5.1-chat-latest",
        input=[{"role": "user", "content": [{"type": "input_text", "text": "Say hello"}]}],
        max_output_tokens=50,
        text={"format": {"type": "text"}},
    )

    print("Response attributes:", dir(response))
    print("\nUsage object:", response.usage)
    print("\nUsage attributes:", dir(response.usage))
    print(
        "\nUsage dict:", response.usage.model_dump() if hasattr(response.usage, "model_dump") else vars(response.usage)
    )


asyncio.run(check_usage_structure())
