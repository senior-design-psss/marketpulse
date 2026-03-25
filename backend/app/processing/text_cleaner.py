"""Text cleaning and normalization for financial content."""

import re
from html import unescape

# Compiled regex patterns
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
EMAIL_PATTERN = re.compile(r"\S+@\S+\.\S+")
MULTI_WHITESPACE = re.compile(r"\s+")
TICKER_PATTERN = re.compile(r"\$[A-Z]{1,5}\b")


def clean_text(text: str) -> str:
    """Clean raw text for processing. Preserves cashtags and meaningful content."""
    if not text:
        return ""

    # Decode HTML entities
    text = unescape(text)

    # Remove HTML tags
    text = HTML_TAG_PATTERN.sub(" ", text)

    # Remove URLs
    text = URL_PATTERN.sub("", text)

    # Remove email addresses
    text = EMAIL_PATTERN.sub("", text)

    # Collapse whitespace
    text = MULTI_WHITESPACE.sub(" ", text)

    return text.strip()


def extract_cashtags(text: str) -> list[str]:
    """Extract $TICKER cashtags from text."""
    return TICKER_PATTERN.findall(text)


def truncate_for_model(text: str, max_chars: int = 2000) -> str:
    """Truncate text to a max character length, breaking at word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        return truncated[:last_space]
    return truncated
