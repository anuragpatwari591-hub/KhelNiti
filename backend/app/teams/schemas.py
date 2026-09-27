from pydantic import BaseModel


class TeamOut(BaseModel):
    id: int
    sport: str
    name: str
    short_name: str | None = None
    country: str | None = None

    model_config = {"from_attributes": True}
