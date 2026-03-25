"""Entity extraction using cashtag matching + word-boundary alias lookup + spaCy NER."""

import logging
import re
from dataclasses import dataclass

from app.processing.text_cleaner import extract_cashtags

logger = logging.getLogger(__name__)

# spaCy model loaded lazily
_nlp = None

# Aliases that are common English words — require extra context to match
# These only match if they appear as standalone capitalized words (e.g. "Meta" not "meta")
AMBIGUOUS_ALIASES = {
    "apple", "meta", "coin", "ford", "visa", "cat", "nike",
    "bath", "snap", "match", "block", "dish", "gap",
}

# Aliases too short or generic to ever use for substring matching
SKIP_ALIASES = {
    "bac", "ms", "ge", "gm", "f", "v", "t", "ko", "ba",
}


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded: en_core_web_sm")
        except (OSError, ImportError):
            logger.warning(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            _nlp = False
    return _nlp if _nlp is not False else None


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    text: str
    symbol: str | None
    confidence: float
    match_type: str  # "cashtag", "alias_exact", "alias_boundary", "spacy_ner"


def _word_boundary_match(alias: str, text: str) -> bool:
    """Check if alias appears as a whole word/phrase in text (not as substring of another word)."""
    pattern = r"\b" + re.escape(alias) + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


FINANCIAL_CONTEXT_WORDS = {
    "stock", "shares", "earnings", "revenue", "profit", "loss", "quarterly",
    "ceo", "ipo", "market", "investor", "trading", "nasdaq", "nyse", "s&p",
    "analyst", "upgrade", "downgrade", "buy", "sell", "price", "valuation",
    "dividend", "guidance", "forecast", "q1", "q2", "q3", "q4", "fiscal",
    "billion", "million", "growth", "decline", "surge", "plunge", "rally",
    "bearish", "bullish", "sentiment", "ticker", "equity", "portfolio",
}


def _has_financial_context(text: str, window: int = 200) -> bool:
    """Check if the text contains financial keywords suggesting a stock/company context."""
    text_lower = text.lower()
    return any(w in text_lower for w in FINANCIAL_CONTEXT_WORDS)


def _capitalized_match(alias: str, text: str) -> bool:
    """Check if the alias appears capitalized AND in financial context."""
    capitalized = alias.capitalize()
    pattern = r"\b" + re.escape(capitalized) + r"\b"
    match = re.search(pattern, text)
    if not match:
        return False
    # Check financial context in the surrounding text
    start = max(0, match.start() - 150)
    end = min(len(text), match.end() + 150)
    window_text = text[start:end]
    return _has_financial_context(window_text)


def extract_entities(
    text: str,
    company_lookup: dict[str, str] | None = None,
) -> list[ExtractedEntity]:
    """
    Extract company entities from text with improved accuracy.

    Matching tiers (highest confidence first):
    1. Cashtags ($AAPL) — confidence 1.0
    2. Exact multi-word names ("Goldman Sachs", "Bank of America") — confidence 0.95
    3. Word-boundary single-word matches ("Tesla", "NVIDIA") — confidence 0.85
    4. Ambiguous words only if capitalized ("Apple" not "apple") — confidence 0.70
    5. spaCy NER ORG entities matched to known companies — confidence 0.75
    """
    entities: list[ExtractedEntity] = []
    seen_symbols: set[str] = set()

    if company_lookup is None:
        company_lookup = {}

    # 1. Cashtags ($AAPL, $TSLA) — highest confidence
    cashtags = extract_cashtags(text)
    for tag in cashtags:
        symbol = tag.lstrip("$").upper()
        if symbol not in seen_symbols:
            if symbol.lower() in company_lookup or any(
                v == symbol for v in company_lookup.values()
            ):
                entities.append(
                    ExtractedEntity(text=tag, symbol=symbol, confidence=1.0, match_type="cashtag")
                )
                seen_symbols.add(symbol)

    # 2 & 3. Alias matching with word boundaries
    for alias, symbol in company_lookup.items():
        if symbol in seen_symbols:
            continue

        # Skip aliases that are too short/generic for text matching
        if alias in SKIP_ALIASES:
            continue

        # Multi-word aliases (e.g. "Goldman Sachs", "Bank of America") — high confidence
        if " " in alias and len(alias) >= 8:
            if _word_boundary_match(alias, text):
                entities.append(
                    ExtractedEntity(
                        text=alias, symbol=symbol, confidence=0.95, match_type="alias_exact"
                    )
                )
                seen_symbols.add(symbol)
                continue

        # Single-word aliases
        if len(alias) < 4:
            continue  # Skip 1-3 char aliases entirely for text matching

        # Ambiguous common words — only match if capitalized in original text
        if alias in AMBIGUOUS_ALIASES:
            if _capitalized_match(alias, text):
                entities.append(
                    ExtractedEntity(
                        text=alias, symbol=symbol, confidence=0.70, match_type="alias_boundary"
                    )
                )
                seen_symbols.add(symbol)
            continue

        # Normal single-word aliases — word boundary match
        if _word_boundary_match(alias, text):
            entities.append(
                ExtractedEntity(
                    text=alias, symbol=symbol, confidence=0.85, match_type="alias_boundary"
                )
            )
            seen_symbols.add(symbol)

    # 4. spaCy NER — extract ORG entities
    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text[:5000])
        for ent in doc.ents:
            if ent.label_ == "ORG":
                ent_lower = ent.text.lower().strip()
                if ent_lower in company_lookup:
                    symbol = company_lookup[ent_lower]
                    if symbol not in seen_symbols:
                        entities.append(
                            ExtractedEntity(
                                text=ent.text, symbol=symbol, confidence=0.75, match_type="spacy_ner"
                            )
                        )
                        seen_symbols.add(symbol)

    return entities
