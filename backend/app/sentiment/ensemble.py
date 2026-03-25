"""Ensemble sentiment scoring — weighted merge of FinBERT + LLM."""

import logging
from dataclasses import dataclass

from app.sentiment.finbert import FinBERTResult
from app.sentiment.llm_scorer import LLMSentimentResult

logger = logging.getLogger(__name__)

# Ensemble weights
LLM_WEIGHT = 0.70
FINBERT_WEIGHT = 0.30


@dataclass
class EnsembleResult:
    """Combined result from ensemble scoring."""

    # FinBERT
    finbert_positive: float | None
    finbert_negative: float | None
    finbert_neutral: float | None
    finbert_label: str | None

    # LLM
    llm_score: float | None
    llm_label: str | None
    llm_reasoning: str | None

    # Ensemble
    ensemble_score: float
    ensemble_label: str
    ensemble_confidence: float


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


def _finbert_to_continuous(result: FinBERTResult) -> float:
    """Convert FinBERT probabilities to a -1 to 1 continuous score."""
    return result.positive - result.negative


def compute_ensemble(
    finbert_result: FinBERTResult | None,
    llm_result: LLMSentimentResult | None,
) -> EnsembleResult:
    """
    Compute the weighted ensemble of FinBERT and LLM scores.

    Handles cases where one or both models fail:
    - Both available: 70% LLM + 30% FinBERT
    - Only LLM: 100% LLM with reduced confidence
    - Only FinBERT: 100% FinBERT with reduced confidence
    - Neither: neutral score with zero confidence
    """
    finbert_score = _finbert_to_continuous(finbert_result) if finbert_result else None
    llm_score = llm_result.score if llm_result else None

    # Compute ensemble score
    if finbert_score is not None and llm_score is not None:
        ensemble_score = LLM_WEIGHT * llm_score + FINBERT_WEIGHT * finbert_score
        # Confidence based on model agreement
        agreement = 1.0 - abs(finbert_score - llm_score)
        confidence = 0.5 + 0.5 * agreement  # Range: 0.5 to 1.0
    elif llm_score is not None:
        ensemble_score = llm_score
        confidence = 0.4  # Reduced confidence with single model
    elif finbert_score is not None:
        ensemble_score = finbert_score
        confidence = 0.3  # Lower confidence for FinBERT alone
    else:
        ensemble_score = 0.0
        confidence = 0.0

    # Clamp
    ensemble_score = max(-1.0, min(1.0, ensemble_score))
    ensemble_label = _score_to_label(ensemble_score)

    return EnsembleResult(
        finbert_positive=finbert_result.positive if finbert_result else None,
        finbert_negative=finbert_result.negative if finbert_result else None,
        finbert_neutral=finbert_result.neutral if finbert_result else None,
        finbert_label=finbert_result.label if finbert_result else None,
        llm_score=llm_result.score if llm_result else None,
        llm_label=llm_result.label if llm_result else None,
        llm_reasoning=llm_result.reasoning if llm_result else None,
        ensemble_score=ensemble_score,
        ensemble_label=ensemble_label,
        ensemble_confidence=confidence,
    )
