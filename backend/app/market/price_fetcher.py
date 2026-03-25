"""Fetch daily stock price data using yfinance."""

import logging

from sqlalchemy import select

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.price_data import PriceData

logger = logging.getLogger(__name__)

# Skip non-stock tickers
SKIP_SYMBOLS = {"BTC", "ETH"}


async def fetch_prices(days: int = 90) -> int:
    """
    Fetch daily OHLCV data for all tracked companies via yfinance.
    Returns number of price records upserted.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed, skipping price fetch")
        return 0

    count = 0

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
            if company.symbol in SKIP_SYMBOLS:
                continue

            try:
                ticker = yf.Ticker(company.symbol)
                hist = ticker.history(period=f"{days}d")

                if hist.empty:
                    continue

                for idx, row in hist.iterrows():
                    price_date = idx.date() if hasattr(idx, "date") else idx

                    # Check if already exists
                    existing = await session.execute(
                        select(PriceData).where(
                            PriceData.company_id == company.id,
                            PriceData.date == price_date,
                        )
                    )
                    pd_record = existing.scalar_one_or_none()

                    close_price = float(row["Close"])
                    open_price = float(row["Open"]) if "Open" in row else None
                    high_price = float(row["High"]) if "High" in row else None
                    low_price = float(row["Low"]) if "Low" in row else None
                    volume = int(row["Volume"]) if "Volume" in row else None

                    if pd_record:
                        pd_record.close = close_price
                        pd_record.open = open_price
                        pd_record.high = high_price
                        pd_record.low = low_price
                        pd_record.volume = volume
                    else:
                        pd_record = PriceData(
                            company_id=company.id,
                            date=price_date,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume,
                        )
                        session.add(pd_record)
                    count += 1

            except Exception as e:
                logger.error(f"Failed to fetch prices for {company.symbol}: {e}")
                continue

        # Compute daily returns
        for company in companies:
            if company.symbol in SKIP_SYMBOLS:
                continue

            prices_result = await session.execute(
                select(PriceData)
                .where(PriceData.company_id == company.id)
                .order_by(PriceData.date.asc())
            )
            prices = prices_result.scalars().all()
            for i in range(1, len(prices)):
                if prices[i - 1].close and prices[i - 1].close != 0:
                    prices[i].daily_return = (
                        (prices[i].close - prices[i - 1].close) / prices[i - 1].close
                    )

        await session.commit()

    logger.info(f"Fetched {count} price records")
    return count
