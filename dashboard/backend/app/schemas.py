"""Pydantic response models for the dashboard API."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class UserSummary(BaseModel):
    id: str
    username: str | None = None


class UsersResponse(BaseModel):
    users: list[UserSummary]


class HopCount(BaseModel):
    hop: int
    count: int


class PromoReachResponse(BaseModel):
    user_id: str
    username: str | None = None
    total_reach: int
    total_users: int
    reach_percentage: float
    by_hop: list[HopCount]


class InfluencerEntry(BaseModel):
    rank: int
    user_id: str
    username: str | None = None
    score: float


class InfluencersResponse(BaseModel):
    max_score: float
    ranking: list[InfluencerEntry]


class EventRecommendation(BaseModel):
    rank: int
    event_id: str
    event_name: str | None = None
    score: float
    friends_attended: int


class EventRecommendationsResponse(BaseModel):
    user_id: str
    username: str | None = None
    recommendations: list[EventRecommendation]


class CommunityEntry(BaseModel):
    community_id: int
    size: int
    sample_users: list[str] = Field(default_factory=list)


class CommunitiesResponse(BaseModel):
    total_communities: int
    dominant_communities: list[CommunityEntry]
    niches_count: int
    niches_total_members: int


class BrokerEntry(BaseModel):
    rank: int
    user_id: str
    username: str | None = None
    betweenness_score: float


class BrokersResponse(BaseModel):
    ranking: list[BrokerEntry]
