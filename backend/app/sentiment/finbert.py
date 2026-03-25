"""FinBERT sentiment analysis using Hugging Face transformers."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_pipeline = None


@dataclass
class FinBERTResult:
    """Result from FinBERT inference."""

    positive: float
    negative: float
    neutral: float
    label: str  # "positive", "negative", "neutral"


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline

            _pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                top_k=None,
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load FinBERT: {e}")
            _pipeline = False
    return _pipeline if _pipeline is not False else None


def score_text(text: str) -> FinBERTResult | None:
    """Score a single text with FinBERT. Returns probability distribution."""
    pipe = _get_pipeline()
    if pipe is None:
        return None

    try:
        # Truncate long text
        text = text[:1500]
        results = pipe(text)

        # results is [[{label, score}, ...]]
        scores = {r["label"]: r["score"] for r in results[0]}

        return FinBERTResult(
            positive=scores.get("positive", 0.0),
            negative=scores.get("negative", 0.0),
            neutral=scores.get("neutral", 0.0),
            label=max(scores, key=scores.get),
        )
    except Exception as e:
        logger.error(f"FinBERT scoring failed: {e}")
        return None


def score_batch(texts: list[str]) -> list[FinBERTResult | None]:
    """Score a batch of texts with FinBERT."""
    pipe = _get_pipeline()
    if pipe is None:
        return [None] * len(texts)

    try:
        truncated = [t[:1500] for t in texts]
        batch_results = pipe(truncated)

        results = []
        for item_scores in batch_results:
            # Handle nested list format: [[{...}]] vs [{...}]
            if item_scores and isinstance(item_scores[0], list):
                item_scores = item_scores[0]
            scores = {r["label"]: r["score"] for r in item_scores}
            results.append(
                FinBERTResult(
                    positive=scores.get("positive", 0.0),
                    negative=scores.get("negative", 0.0),
                    neutral=scores.get("neutral", 0.0),
                    label=max(scores, key=scores.get),
                )
            )
        return results
    except Exception as e:
        logger.error(f"FinBERT batch scoring failed: {e}")
        return [None] * len(texts)
