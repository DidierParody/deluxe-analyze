"""FastAPI app for the deluxe-analyze sales dashboard."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from . import queries
from .auth import require_api_key
from .config import Settings
from .neo4j_client import (
    close_driver,
    ensure_projection,
    get_driver,
    get_username,
    run_query,
    user_exists,
)
from .schemas import (
    BrokerEntry,
    BrokersResponse,
    CommunitiesResponse,
    CommunityEntry,
    EventRecommendation,
    EventRecommendationsResponse,
    HealthResponse,
    HopCount,
    InfluencerEntry,
    InfluencersResponse,
    PromoReachResponse,
    UsersResponse,
    UserSummary,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: warm up driver and projection
    try:
        get_driver()
        ensure_projection()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Startup warm-up failed (continuing): %s", exc)
    yield
    close_driver()


app = FastAPI(title="deluxe-analyze dashboard-api", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/users", response_model=UsersResponse, tags=["catalog"])
def list_users(
    limit: int = Query(500, ge=1, le=2000),
    _key: str = Depends(require_api_key),
) -> UsersResponse:
    rows = run_query(queries.LIST_USERS, {"limit": limit})
    return UsersResponse(users=[UserSummary(id=r["id"], username=r.get("username")) for r in rows])


@app.get("/promo-reach/{user_id}", response_model=PromoReachResponse, tags=["analytics"])
def promo_reach(user_id: str, _key: str = Depends(require_api_key)) -> PromoReachResponse:
    if not user_exists(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    rows = run_query(queries.PROMO_REACH, {"user_id": user_id})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data for {user_id}")
    r = rows[0]
    total = int(r["total_users"] or 0)
    by_hop = [
        HopCount(hop=1, count=int(r.get("hop1") or 0)),
        HopCount(hop=2, count=int(r.get("hop2") or 0)),
        HopCount(hop=3, count=int(r.get("hop3") or 0)),
    ]
    total_reach = sum(h.count for h in by_hop)
    pct = round((total_reach / total * 100) if total else 0.0, 2)
    return PromoReachResponse(
        user_id=user_id,
        username=r.get("username"),
        total_reach=total_reach,
        total_users=total,
        reach_percentage=pct,
        by_hop=by_hop,
    )


@app.get("/influencers", response_model=InfluencersResponse, tags=["analytics"])
def influencers(
    limit: int = Query(10, ge=1, le=50),
    _key: str = Depends(require_api_key),
) -> InfluencersResponse:
    ensure_projection()
    rows = run_query(queries.INFLUENCERS, {"limit": limit, "graph": settings.GDS_GRAPH_NAME})
    ranking = [
        InfluencerEntry(
            rank=i + 1,
            user_id=r["user_id"],
            username=r.get("username"),
            score=float(r["score"]),
        )
        for i, r in enumerate(rows)
    ]
    max_score = ranking[0].score if ranking else 0.0
    return InfluencersResponse(max_score=max_score, ranking=ranking)


@app.get(
    "/event-recommendations/{user_id}",
    response_model=EventRecommendationsResponse,
    tags=["analytics"],
)
def event_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    _key: str = Depends(require_api_key),
) -> EventRecommendationsResponse:
    if not user_exists(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    rows = run_query(queries.EVENT_RECOMMENDATIONS, {"user_id": user_id, "limit": limit})
    username = rows[0].get("username") if rows else get_username(user_id)
    recs = [
        EventRecommendation(
            rank=i + 1,
            event_id=r["event_id"],
            event_name=r.get("event_name"),
            score=float(r["score"]),
            friends_attended=int(r["friends_attended"]),
        )
        for i, r in enumerate(rows)
    ]
    return EventRecommendationsResponse(user_id=user_id, username=username, recommendations=recs)


@app.get("/communities", response_model=CommunitiesResponse, tags=["analytics"])
def communities(
    min_size: int = Query(2, ge=1, le=1000),
    _key: str = Depends(require_api_key),
) -> CommunitiesResponse:
    ensure_projection()
    rows = run_query(queries.COMMUNITIES, {"graph": settings.GDS_GRAPH_NAME})
    dominant: list[CommunityEntry] = []
    niches_count = 0
    niches_members = 0
    for r in rows:
        size_ = int(r["size"])
        if size_ >= min_size:
            users: list[str] = list(r.get("users") or [])
            dominant.append(
                CommunityEntry(
                    community_id=int(r["communityId"]),
                    size=size_,
                    sample_users=users[:10],
                )
            )
        else:
            niches_count += 1
            niches_members += size_
    return CommunitiesResponse(
        total_communities=len(rows),
        dominant_communities=dominant,
        niches_count=niches_count,
        niches_total_members=niches_members,
    )


@app.get("/brokers", response_model=BrokersResponse, tags=["analytics"])
def brokers(
    limit: int = Query(10, ge=1, le=50),
    _key: str = Depends(require_api_key),
) -> BrokersResponse:
    ensure_projection()
    rows = run_query(queries.BROKERS, {"limit": limit, "graph": settings.GDS_GRAPH_NAME})
    ranking = [
        BrokerEntry(
            rank=i + 1,
            user_id=r["user_id"],
            username=r.get("username"),
            betweenness_score=float(r["score"]),
        )
        for i, r in enumerate(rows)
    ]
    return BrokersResponse(ranking=ranking)
