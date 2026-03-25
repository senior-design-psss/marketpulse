"""Processing pipeline — orchestrates: unprocessed content → clean → NER → score → store."""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.models.entity_mention import EntityMention
from app.models.raw_content import RawContent
from app.models.sentiment_score import SentimentScore
from app.processing.company_mapper import company_mapper
from app.processing.entity_extractor import extract_entities
from app.processing.text_cleaner import clean_text, truncate_for_model
from app.sentiment.ensemble import compute_ensemble
from app.sentiment.finbert import FinBERTResult
from app.sentiment.finbert import score_batch as finbert_batch
from app.sentiment.llm_scorer import LLMSentimentResult
from app.sentiment.llm_scorer import score_text as llm_score_text

logger = logging.getLogger(__name__)

BATCH_SIZE = 20


async def _ensure_mapper_loaded(session: AsyncSession) -> None:
    """Make sure the company mapper is loaded."""
    if not company_mapper.is_loaded:
        await company_mapper.load(session)


async def process_batch(batch_size: int = BATCH_SIZE) -> int:
    """
    Process a batch of unprocessed raw_content items.

    Steps for each item:
    1. Clean text
    2. Extract entities (companies mentioned)
    3. Score with FinBERT (batch)
    4. Score with LLM (if API key available)
    5. Compute ensemble score
    6. Store entity_mentions and sentiment_scores
    7. Mark raw_content as processed

    Returns the number of items processed.
    """
    async with get_session_factory()() as session:
        await _ensure_mapper_loaded(session)

        # Fetch unprocessed items
        result = await session.execute(
            select(RawContent)
            .where(RawContent.is_processed == False)  # noqa: E712
            .order_by(RawContent.ingested_at.asc())
            .limit(batch_size)
        )
        items = result.scalars().all()

        if not items:
            return 0

        logger.info(f"Processing {len(items)} items")

        # Step 1: Clean texts
        cleaned_texts = [clean_text(item.body) for item in items]

        # Step 2: FinBERT batch scoring
        model_texts = [truncate_for_model(t, max_chars=1500) for t in cleaned_texts]
        finbert_results: list[FinBERTResult | None] = finbert_batch(model_texts)

        # Step 3: Process each item
        processed_count = 0
        for i, item in enumerate(items):
            try:
                text = cleaned_texts[i]

                # Extract entities
                entities = extract_entities(text, company_mapper.alias_lookup)

                # LLM scoring (async, per-item)
                llm_result: LLMSentimentResult | None = None
                try:
                    llm_result = await llm_score_text(
                        truncate_for_model(text, max_chars=3000)
                    )
                except Exception as e:
                    logger.debug(f"LLM scoring skipped for item {item.id}: {e}")

                # Ensemble scoring
                ensemble = compute_ensemble(finbert_results[i], llm_result)

                # Store entity mentions
                for entity in entities:
                    company_id = company_mapper.get_company_id(entity.symbol)
                    if company_id:
                        mention = EntityMention(
                            raw_content_id=item.id,
                            company_id=company_id,
                            mention_text=entity.text,
                            confidence=entity.confidence,
                        )
                        session.add(mention)

                # Store sentiment scores — one per mentioned company
                if entities:
                    for entity in entities:
                        company_id = company_mapper.get_company_id(entity.symbol)
                        if company_id:
                            score = SentimentScore(
                                raw_content_id=item.id,
                                company_id=company_id,
                                finbert_positive=ensemble.finbert_positive,
                                finbert_negative=ensemble.finbert_negative,
                                finbert_neutral=ensemble.finbert_neutral,
                                finbert_label=ensemble.finbert_label,
                                llm_score=ensemble.llm_score,
                                llm_label=ensemble.llm_label,
                                llm_reasoning=ensemble.llm_reasoning,
                                ensemble_score=ensemble.ensemble_score,
                                ensemble_label=ensemble.ensemble_label,
                                ensemble_confidence=ensemble.ensemble_confidence,
                                source=item.source,
                            )
                            session.add(score)
                else:
                    # No entities found — store a general score without company
                    score = SentimentScore(
                        raw_content_id=item.id,
                        company_id=None,
                        finbert_positive=ensemble.finbert_positive,
                        finbert_negative=ensemble.finbert_negative,
                        finbert_neutral=ensemble.finbert_neutral,
                        finbert_label=ensemble.finbert_label,
                        llm_score=ensemble.llm_score,
                        llm_label=ensemble.llm_label,
                        llm_reasoning=ensemble.llm_reasoning,
                        ensemble_score=ensemble.ensemble_score,
                        ensemble_label=ensemble.ensemble_label,
                        ensemble_confidence=ensemble.ensemble_confidence,
                        source=item.source,
                    )
                    session.add(score)

                # Mark as processed
                await session.execute(
                    update(RawContent)
                    .where(RawContent.id == item.id)
                    .values(is_processed=True)
                )
                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process item {item.id}: {e}")
                continue

        await session.commit()
        logger.info(f"Processed {processed_count}/{len(items)} items")
        return processed_count
