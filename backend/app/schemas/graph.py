"""Pydantic schemas for entity graph endpoints."""

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    name: str
    node_type: str  # "industry" or "company"
    symbol: str | None = None  # Only for companies
    sentiment: float | None = None
    volume: int = 0
    industry: str | None = None  # Slug, for companies
    color: str | None = None  # Display color


class GraphEdge(BaseModel):
    source: str  # node id
    target: str  # node id
    edge_type: str  # "industry_company", "co_mention"
    weight: int = 1
    correlation: float | None = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
