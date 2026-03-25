"""Seed the database with initial industries and companies."""

import asyncio

from sqlalchemy import select

from app.core.database import get_engine, get_session_factory
from app.models import Base, Company, Industry, company_industries

INDUSTRIES = [
    {"name": "Technology", "slug": "technology", "display_color": "#3B82F6"},
    {"name": "Finance", "slug": "finance", "display_color": "#10B981"},
    {"name": "Energy", "slug": "energy", "display_color": "#F59E0B"},
    {"name": "Healthcare", "slug": "healthcare", "display_color": "#EF4444"},
    {"name": "Consumer", "slug": "consumer", "display_color": "#8B5CF6"},
    {"name": "Industrials", "slug": "industrials", "display_color": "#6B7280"},
    {"name": "Real Estate", "slug": "real-estate", "display_color": "#EC4899"},
    {"name": "Crypto", "slug": "crypto", "display_color": "#F97316"},
    {"name": "Automotive", "slug": "automotive", "display_color": "#14B8A6"},
    {"name": "Communications", "slug": "communications", "display_color": "#6366F1"},
]

COMPANIES = [
    # Technology
    {"symbol": "AAPL", "name": "Apple Inc.", "aliases": ["Apple", "AAPL", "iPhone maker", "Apple Inc"], "industries": ["technology", "consumer"]},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "aliases": ["Google", "GOOGL", "Alphabet", "Google Cloud"], "industries": ["technology", "communications"]},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "aliases": ["Microsoft", "MSFT", "Azure", "Windows"], "industries": ["technology"]},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "aliases": ["Amazon", "AMZN", "AWS", "Amazon Web Services"], "industries": ["technology", "consumer"]},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "aliases": ["NVIDIA", "NVDA", "Nvidia", "Jensen Huang"], "industries": ["technology"]},
    {"symbol": "META", "name": "Meta Platforms Inc.", "aliases": ["Meta", "META", "Facebook", "Instagram", "WhatsApp"], "industries": ["technology", "communications"]},
    {"symbol": "TSM", "name": "Taiwan Semiconductor", "aliases": ["TSMC", "TSM", "Taiwan Semi"], "industries": ["technology"]},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "aliases": ["Broadcom", "AVGO"], "industries": ["technology"]},
    {"symbol": "CRM", "name": "Salesforce Inc.", "aliases": ["Salesforce", "CRM"], "industries": ["technology"]},
    {"symbol": "ORCL", "name": "Oracle Corp.", "aliases": ["Oracle", "ORCL"], "industries": ["technology"]},

    # Finance
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "aliases": ["JPMorgan", "JPM", "Chase", "JP Morgan"], "industries": ["finance"]},
    {"symbol": "GS", "name": "Goldman Sachs Group", "aliases": ["Goldman Sachs", "GS", "Goldman"], "industries": ["finance"]},
    {"symbol": "BAC", "name": "Bank of America Corp.", "aliases": ["Bank of America", "BAC", "BofA"], "industries": ["finance"]},
    {"symbol": "MS", "name": "Morgan Stanley", "aliases": ["Morgan Stanley", "MS"], "industries": ["finance"]},
    {"symbol": "V", "name": "Visa Inc.", "aliases": ["Visa", "V"], "industries": ["finance"]},

    # Energy
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "aliases": ["ExxonMobil", "XOM", "Exxon"], "industries": ["energy"]},
    {"symbol": "CVX", "name": "Chevron Corp.", "aliases": ["Chevron", "CVX"], "industries": ["energy"]},
    {"symbol": "COP", "name": "ConocoPhillips", "aliases": ["ConocoPhillips", "COP", "Conoco"], "industries": ["energy"]},

    # Healthcare
    {"symbol": "JNJ", "name": "Johnson & Johnson", "aliases": ["Johnson & Johnson", "JNJ", "J&J"], "industries": ["healthcare"]},
    {"symbol": "PFE", "name": "Pfizer Inc.", "aliases": ["Pfizer", "PFE"], "industries": ["healthcare"]},
    {"symbol": "UNH", "name": "UnitedHealth Group", "aliases": ["UnitedHealth", "UNH", "United Health"], "industries": ["healthcare"]},
    {"symbol": "LLY", "name": "Eli Lilly & Co.", "aliases": ["Eli Lilly", "LLY", "Lilly"], "industries": ["healthcare"]},

    # Consumer
    {"symbol": "WMT", "name": "Walmart Inc.", "aliases": ["Walmart", "WMT"], "industries": ["consumer"]},
    {"symbol": "KO", "name": "Coca-Cola Co.", "aliases": ["Coca-Cola", "KO", "Coke"], "industries": ["consumer"]},
    {"symbol": "PG", "name": "Procter & Gamble", "aliases": ["Procter & Gamble", "PG", "P&G"], "industries": ["consumer"]},
    {"symbol": "NKE", "name": "Nike Inc.", "aliases": ["Nike", "NKE"], "industries": ["consumer"]},

    # Industrials
    {"symbol": "BA", "name": "Boeing Co.", "aliases": ["Boeing", "BA"], "industries": ["industrials"]},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "aliases": ["Caterpillar", "CAT"], "industries": ["industrials"]},
    {"symbol": "GE", "name": "GE Aerospace", "aliases": ["GE", "General Electric", "GE Aerospace"], "industries": ["industrials"]},

    # Automotive
    {"symbol": "TSLA", "name": "Tesla Inc.", "aliases": ["Tesla", "TSLA", "Elon Musk", "Cybertruck"], "industries": ["automotive", "technology"]},
    {"symbol": "F", "name": "Ford Motor Co.", "aliases": ["Ford", "F"], "industries": ["automotive"]},
    {"symbol": "GM", "name": "General Motors Co.", "aliases": ["General Motors", "GM"], "industries": ["automotive"]},

    # Crypto
    {"symbol": "BTC", "name": "Bitcoin", "aliases": ["Bitcoin", "BTC", "bitcoin"], "industries": ["crypto"]},
    {"symbol": "ETH", "name": "Ethereum", "aliases": ["Ethereum", "ETH", "ethereum", "Ether"], "industries": ["crypto"]},
    {"symbol": "COIN", "name": "Coinbase Global", "aliases": ["Coinbase", "COIN"], "industries": ["crypto", "finance"]},

    # Communications
    {"symbol": "DIS", "name": "Walt Disney Co.", "aliases": ["Disney", "DIS", "Walt Disney"], "industries": ["communications", "consumer"]},
    {"symbol": "NFLX", "name": "Netflix Inc.", "aliases": ["Netflix", "NFLX"], "industries": ["communications"]},
    {"symbol": "T", "name": "AT&T Inc.", "aliases": ["AT&T", "T"], "industries": ["communications"]},

    # Real Estate
    {"symbol": "AMT", "name": "American Tower Corp.", "aliases": ["American Tower", "AMT"], "industries": ["real-estate"]},
    {"symbol": "PLD", "name": "Prologis Inc.", "aliases": ["Prologis", "PLD"], "industries": ["real-estate"]},
]


async def seed_data():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        # Check if already seeded
        result = await session.execute(select(Industry).limit(1))
        if result.scalar_one_or_none() is not None:
            print("Database already seeded, skipping.")
            return

        # Insert industries
        industry_map: dict[str, Industry] = {}
        for ind_data in INDUSTRIES:
            industry = Industry(**ind_data)
            session.add(industry)
            industry_map[ind_data["slug"]] = industry

        await session.flush()

        # Insert companies with industry mappings
        for comp_data in COMPANIES:
            industry_slugs = comp_data.pop("industries")
            company = Company(**comp_data)
            session.add(company)
            await session.flush()

            for slug in industry_slugs:
                if slug in industry_map:
                    await session.execute(
                        company_industries.insert().values(
                            company_id=company.id,
                            industry_id=industry_map[slug].id,
                        )
                    )

        await session.commit()
        print(f"Seeded {len(INDUSTRIES)} industries and {len(COMPANIES)} companies.")


if __name__ == "__main__":
    asyncio.run(seed_data())
