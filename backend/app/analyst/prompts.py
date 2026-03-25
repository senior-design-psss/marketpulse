"""All LLM prompt templates for the AI Analyst layer."""

DAILY_BRIEFING_PROMPT = """You are a senior financial market analyst at a top investment bank. Generate a concise daily market sentiment briefing based on the data below.

## Data Summary
- Analysis window: {window_start} to {window_end}
- Total items analyzed: {items_analyzed}
- Overall market sentiment: {overall_score:+.3f} ({overall_label})

## Industry Sentiment
{industry_breakdown}

## Top Bullish Companies
{top_bullish}

## Top Bearish Companies
{top_bearish}

## Active Anomalies
{anomalies}

## Instructions
Write a professional market briefing in Markdown format with these sections:
1. **Market Overview** - 2-3 sentences on the overall sentiment landscape
2. **Sector Highlights** - Key sector movements and what's driving them
3. **Companies to Watch** - Notable companies with significant sentiment shifts
4. **Risk Factors** - Any anomalies or divergences that warrant attention
5. **Outlook** - Brief forward-looking perspective based on sentiment momentum

Keep it concise (300-500 words). Use specific data points. Sound like a Bloomberg analyst, not a chatbot."""


COMPANY_SUMMARY_PROMPT = """You are a financial analyst. Write a concise sentiment summary for {symbol} ({company_name}).

## Sentiment Data (last 24 hours)
- Average sentiment score: {avg_score:+.3f}
- Sentiment label: {label}
- Confidence: {confidence:.0%}
- Volume: {volume} mentions across sources
- Momentum: {momentum}

## Source Breakdown
- Reddit: {reddit_avg} (from {reddit_vol} posts)
- News: {news_avg} (from {news_vol} articles)
- StockTwits: {stocktwits_avg} (from {stocktwits_vol} posts)

## Sample Headlines
{sample_headlines}

## Instructions
Write a 2-3 paragraph summary covering:
1. What the market sentiment currently says about this company
2. Key themes driving sentiment (what are people talking about?)
3. Any notable divergences between sources

Be specific and data-driven. 100-200 words max."""


RISK_ALERT_PROMPT = """You are a risk analyst. An anomaly has been detected:

Company: {symbol} ({company_name})
Alert: {title}
Severity: {severity}
Current score: {metric_value:+.3f}
Baseline (7-day mean): {baseline_value:+.3f}
Z-score: {z_score:.1f} standard deviations

## Recent Sentiment Items
{recent_items}

## Instructions
Write a brief risk assessment (2-3 sentences):
1. What might be causing this anomalous sentiment?
2. What should an investor watch for?
Keep it factual and concise."""


SECTOR_ANALYSIS_PROMPT = """You are a sector analyst. Provide a brief analysis of the {industry_name} sector.

## Sector Data
- Average sentiment: {avg_score:+.3f}
- Volume: {volume} mentions
- Momentum: {momentum}

## Companies in Sector
{companies_data}

## Instructions
Write a 1-2 paragraph sector overview (100-150 words):
1. Overall sector sentiment direction
2. Which companies are leading/lagging
3. Key themes or drivers"""
