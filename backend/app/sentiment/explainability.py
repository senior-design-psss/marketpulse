"""Generate human-readable explanations for sentiment scores."""

from app.sentiment.ensemble import EnsembleResult


def generate_explanation(result: EnsembleResult) -> str:
    """Generate a human-readable explanation of the sentiment score."""
    parts = []

    # FinBERT explanation
    if result.finbert_label is not None:
        fb_pct = max(
            result.finbert_positive or 0,
            result.finbert_negative or 0,
            result.finbert_neutral or 0,
        )
        parts.append(
            f"FinBERT: {result.finbert_label} ({fb_pct:.0%} confidence)"
        )

    # LLM explanation
    if result.llm_reasoning:
        parts.append(f"AI Analysis: {result.llm_reasoning}")
    elif result.llm_label:
        parts.append(f"AI Classification: {result.llm_label} ({result.llm_score:+.2f})")

    # Ensemble summary
    direction = "bullish" if result.ensemble_score > 0.1 else (
        "bearish" if result.ensemble_score < -0.1 else "neutral"
    )
    parts.append(
        f"Overall: {direction} (score: {result.ensemble_score:+.2f}, "
        f"confidence: {result.ensemble_confidence:.0%})"
    )

    return " | ".join(parts)
