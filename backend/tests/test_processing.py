"""Tests for text processing and entity extraction."""

from app.processing.text_cleaner import clean_text, extract_cashtags, truncate_for_model
from app.sentiment.ensemble import compute_ensemble
from app.sentiment.finbert import FinBERTResult
from app.sentiment.llm_scorer import LLMSentimentResult


def test_clean_text_removes_html():
    assert "Hello world" == clean_text("<p>Hello world</p>")


def test_clean_text_removes_urls():
    result = clean_text("Check https://example.com for info")
    assert "https://" not in result


def test_clean_text_decodes_entities():
    assert "A & B" in clean_text("A &amp; B")


def test_extract_cashtags():
    tags = extract_cashtags("Buying $AAPL and $TSLA today")
    assert "$AAPL" in tags
    assert "$TSLA" in tags


def test_extract_cashtags_empty():
    assert extract_cashtags("no tickers here") == []


def test_truncate_for_model():
    long = "x" * 5000
    result = truncate_for_model(long, max_chars=100)
    assert len(result) <= 100


def test_truncate_short_text():
    assert truncate_for_model("short", max_chars=100) == "short"


def test_ensemble_both_models():
    fb = FinBERTResult(positive=0.8, negative=0.1, neutral=0.1, label="positive")
    llm = LLMSentimentResult(score=0.6, label="positive", reasoning="Good earnings")
    result = compute_ensemble(fb, llm)

    assert result.ensemble_score > 0
    assert result.ensemble_label in ("positive", "very_positive")
    assert result.ensemble_confidence > 0.5


def test_ensemble_finbert_only():
    fb = FinBERTResult(positive=0.9, negative=0.05, neutral=0.05, label="positive")
    result = compute_ensemble(fb, None)

    assert result.ensemble_score > 0
    assert result.ensemble_confidence == 0.3  # Reduced for single model


def test_ensemble_neither_model():
    result = compute_ensemble(None, None)
    assert result.ensemble_score == 0.0
    assert result.ensemble_confidence == 0.0
    assert result.ensemble_label == "neutral"


def test_ensemble_disagreement():
    fb = FinBERTResult(positive=0.8, negative=0.1, neutral=0.1, label="positive")
    llm = LLMSentimentResult(score=-0.5, label="negative", reasoning="Legal trouble")
    result = compute_ensemble(fb, llm)

    # Confidence should be lower when models disagree
    assert result.ensemble_confidence < 0.7
