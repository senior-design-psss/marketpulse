"""Maps entity mentions to known companies using an in-memory lookup."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company

logger = logging.getLogger(__name__)


class CompanyMapper:
    """Builds and maintains an in-memory lookup from company aliases to symbols/IDs."""

    def __init__(self):
        self._alias_to_symbol: dict[str, str] = {}
        self._symbol_to_id: dict[str, uuid.UUID] = {}
        self._loaded = False

    async def load(self, session: AsyncSession) -> None:
        """Load all companies and build the lookup maps."""
        result = await session.execute(select(Company))
        companies = result.scalars().all()

        self._alias_to_symbol.clear()
        self._symbol_to_id.clear()

        for company in companies:
            symbol = company.symbol.upper()
            self._symbol_to_id[symbol] = company.id

            # Map symbol itself
            self._alias_to_symbol[symbol.lower()] = symbol

            # Map company name
            self._alias_to_symbol[company.name.lower()] = symbol

            # Map all aliases
            if company.aliases:
                for alias in company.aliases:
                    self._alias_to_symbol[alias.lower()] = symbol

        self._loaded = True
        logger.info(
            f"CompanyMapper loaded: {len(companies)} companies, "
            f"{len(self._alias_to_symbol)} aliases"
        )

    @property
    def alias_lookup(self) -> dict[str, str]:
        """Returns the alias -> symbol mapping for entity extraction."""
        return self._alias_to_symbol

    def get_company_id(self, symbol: str) -> uuid.UUID | None:
        """Get the company UUID for a ticker symbol."""
        return self._symbol_to_id.get(symbol.upper())

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Singleton instance
company_mapper = CompanyMapper()
