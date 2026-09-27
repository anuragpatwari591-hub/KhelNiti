from datetime import datetime

from pydantic import BaseModel


class NewsArticleOut(BaseModel):
    id: int
    source: str
    published_at: datetime
    title: str
    summary: str | None
    category: str
    verification_status: str

    model_config = {"from_attributes": True}
