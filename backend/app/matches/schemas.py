from datetime import datetime

from pydantic import BaseModel


class TeamSummary(BaseModel):
    id: int
    name: str
    short_name: str | None = None

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    id: int
    sport: str
    status: str
    scheduled_start: datetime
    home_team: TeamSummary
    away_team: TeamSummary
    venue_name: str | None = None
    competition_name: str
    data_quality: str
    result_summary: dict

    model_config = {"from_attributes": True}
