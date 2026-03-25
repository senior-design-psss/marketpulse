"""Entity relationship graph API — industry hubs + company nodes + co-mention edges."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.company import Company
from app.models.company_industry import company_industries
from app.models.entity_relation import EntityRelation
from app.models.industry import Industry
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/entities", response_model=GraphResponse)
async def get_entity_graph(db: AsyncSession = Depends(get_db)):
    """
    Industry-company relationship graph.
    - Industry nodes (large hubs, colored by aggregate sentiment)
    - Company nodes (connected to their industries)
    - Co-mention edges between companies discussed together
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # 1. Industry hub nodes
    industries = (await db.execute(select(Industry).order_by(Industry.name))).scalars().all()

    for ind in industries:
        agg_result = await db.execute(
            select(SentimentAggregate)
            .where(SentimentAggregate.industry_id == ind.id, SentimentAggregate.period_type == "daily")
            .order_by(SentimentAggregate.period_start.desc())
            .limit(1)
        )
        agg = agg_result.scalar_one_or_none()
        sentiment = agg.avg_score if agg else None

        nodes.append(GraphNode(
            id=f"ind_{ind.slug}",
            name=ind.name,
            node_type="industry",
            sentiment=sentiment,
            volume=agg.volume if agg else 0,
            color=ind.display_color,
        ))

    # 2. Company nodes — batch load everything to avoid N+1
    companies = (await db.execute(select(Company).order_by(Company.symbol))).scalars().all()
    company_id_map: dict[str, str] = {}

    # Company -> industries mapping
    ci_result = await db.execute(
        select(company_industries.c.company_id, Industry.slug).join(
            Industry, Industry.id == company_industries.c.industry_id
        )
    )
    comp_industries: dict[str, list[str]] = {}
    for cid, slug in ci_result.all():
        comp_industries.setdefault(str(cid), []).append(slug)

    # Company sentiment
    sent_result = await db.execute(
        select(
            SentimentScore.company_id,
            func.avg(SentimentScore.ensemble_score).label("avg"),
            func.count(SentimentScore.id).label("vol"),
        )
        .where(SentimentScore.company_id.isnot(None))
        .group_by(SentimentScore.company_id)
    )
    comp_sentiments: dict[str, dict] = {}
    for row in sent_result.all():
        comp_sentiments[str(row.company_id)] = {
            "avg": float(row.avg) if row.avg else None,
            "vol": int(row.vol),
        }

    for comp in companies:
        cid = str(comp.id)
        company_id_map[cid] = comp.symbol
        ind_slugs = comp_industries.get(cid, [])
        sent_data = comp_sentiments.get(cid, {"avg": None, "vol": 0})
        primary_industry = ind_slugs[0] if ind_slugs else None

        nodes.append(GraphNode(
            id=comp.symbol,
            name=comp.name,
            node_type="company",
            symbol=comp.symbol,
            sentiment=sent_data["avg"],
            volume=sent_data["vol"],
            industry=primary_industry,
        ))

        # Edges from industry hubs to this company
        for slug in ind_slugs:
            edges.append(GraphEdge(
                source=f"ind_{slug}",
                target=comp.symbol,
                edge_type="industry_company",
                weight=max(sent_data["vol"], 1),
            ))

    # 3. Co-mention edges between companies
    relations = (await db.execute(
        select(EntityRelation)
        .where(EntityRelation.co_occurrence_count >= 2)
        .order_by(EntityRelation.co_occurrence_count.desc())
        .limit(100)
    )).scalars().all()

    for rel in relations:
        source = company_id_map.get(str(rel.company_a_id))
        target = company_id_map.get(str(rel.company_b_id))
        if source and target:
            edges.append(GraphEdge(
                source=source,
                target=target,
                edge_type="co_mention",
                weight=rel.co_occurrence_count,
                correlation=rel.sentiment_correlation,
            ))

    return GraphResponse(nodes=nodes, edges=edges)
