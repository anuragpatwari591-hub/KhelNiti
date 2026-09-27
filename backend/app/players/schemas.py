from datetime import date

from pydantic import BaseModel


class PlayerOut(BaseModel):
    id: int
    sport: str
    full_name: str
    country: str | None = None
    date_of_birth: date | None = None
    batting_style: str | None = None
    bowling_style: str | None = None
    primary_position: str | None = None

    model_config = {"from_attributes": True}


class PlayerMatchStatsOut(BaseModel):
    match_id: int
    runs_scored: int
    balls_faced: int
    strike_rate: float | None
    wickets_taken: int
    overs_bowled: float
    economy_rate: float | None
    data_quality: str

    model_config = {"from_attributes": True}
