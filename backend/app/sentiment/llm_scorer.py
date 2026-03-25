"""LLM-based sentiment scoring using Claude Haiku via Anthropic API."""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_client = None


@dataclass
class LLMSentimentResult:
    """Result from LLM sentiment scoring."""

    score: float  # -1.0 to 1.0
    label: str  # very_negative, negative, neutral, positive, very_positive
    reasoning: str  # Brief explanation


SENTIMENT_PROMPT = """Analyze the financial sentiment of the following text. Rate it on a scale from -1.0 (very bearish/negative) to 1.0 (very bullish/positive).

Respond in this exact JSON format only, no other text:
{"score": <float>, "label": "<label>", "reasoning": "<one sentence>"}

Labels: very_negative (< -0.6), negative (-0.6 to -0.2), neutral (-0.2 to 0.2), positive (0.2 to 0.6), very_positive (> 0.6)

Text: {text}"""


def _get_client():
    global _client
    if _client is None:
        try:
            import anthropic

            from app.config import settings

            if not settings.anthropic_api_key:
                logger.warning("No Anthropic API key configured")
                return None
            _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            logger.warning("anthropic package not installed")
            return None
    return _client


def _parse_response(text: str) -> LLMSentimentResult | None:
    """Parse the LLM response JSON."""
    try:
        # Try to extract JSON from the response
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text)
        score = float(data["score"])
        score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]

        return LLMSentimentResult(
            score=score,
            label=data.get("label", _score_to_label(score)),
            reasoning=data.get("reasoning", ""),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return None


def _score_to_label(score: float) -> str:
    """Convert a numeric score to a label."""
    if score < -0.6:
        return "very_negative"
    elif score < -0.2:
        return "negative"
    elif score < 0.2:
        return "neutral"
    elif score < 0.6:
        return "positive"
    else:
        return "very_positive"


async def score_text(text: str) -> LLMSentimentResult | None:
    """Score a single text with Claude Haiku."""
    client = _get_client()
    if client is None:
        return None

    try:
        truncated = text[:3000]
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": SENTIMENT_PROMPT.format(text=truncated),
                }
            ],
        )

        response_text = message.content[0].text
        return _parse_response(response_text)
    except Exception as e:
        err_str = str(e)
        if "usage limits" in err_str or "rate" in err_str.lower():
            logger.warning(f"LLM API limit reached: {err_str[:100]}")
        else:
            logger.error(f"LLM scoring failed: {err_str[:100]}")
        return None


async def score_batch(texts: list[str]) -> list[LLMSentimentResult | None]:
    """Score a batch of texts with Claude Haiku (sequential calls)."""
    results = []
    for text in texts:
        result = await score_text(text)
        results.append(result)
    return results
