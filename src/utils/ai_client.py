import logging

from fastapi import HTTPException, status
from groq import APIConnectionError, Groq, GroqError, RateLimitError

from src.config import settings

# This will track errors in console
logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)


def get_basic_completion(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    # Testing the groq api key by sending some text

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI Tutor for students in Gilgit Baltistan Pakistan. You should guide related to all universities across Pakistan not limited to GB.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=0.7,  # this controls creativity (0 is strict and 1 is creative)
        )
        content = response.choices[0].message.content
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The AI Tutor returned an empty response",
            )
        return content
    except RateLimitError as e:
        logger.error(f"Groq Rate Limit Hit:{e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The AI Tutor is currently very busy, Please try again in a minute",
        ) from e
    except APIConnectionError as e:
        logger.error(f"Grop Connection Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the AI service. Check your internet connection",
        ) from e
    except GroqError as e:
        logger.error(f"General Groq Error:{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=" The AI Tutor encountered an unexpected error",
        ) from e
