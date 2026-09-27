"""Mock news data provider — development/test only. See mock_cricket.py for
the general rationale on mock providers.
"""
import random
from datetime import datetime, timedelta, timezone

from data.ingestion.providers.base import NewsDataProvider
from data.ingestion.providers.types import NewsArticlePayload
from database.models.enums import DataQuality

_TEMPLATES = [
    ("injury", "unverified", "{player} a doubt for upcoming fixture with knee complaint"),
    ("selection", "reported", "{player} reportedly set to be rested for next match"),
    ("lineup", "confirmed", "{team} confirm starting lineup ahead of kickoff"),
    ("weather", "confirmed", "Rain forecast could affect conditions at the venue"),
    ("transfer", "reported", "{player} linked with move away from {team}"),
]


class MockNewsProvider(NewsDataProvider):
    def __init__(self, seed: int = 11):
        self._seed = seed

    @property
    def provider_name(self) -> str:
        return "mock-news"

    def get_latest_articles(self, since: datetime | None = None) -> list[NewsArticlePayload]:
        rng = random.Random(self._seed)
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(5):
            category, verification, template = rng.choice(_TEMPLATES)
            published_at = now - timedelta(hours=i * 3)
            if since is not None and published_at < since:
                continue
            title = template.format(player="Mock Player", team="Mock Team")
            articles.append(
                NewsArticlePayload(
                    source="mock-news-wire",
                    url=None,
                    published_at=published_at,
                    title=title,
                    summary=None,
                    category=category,
                    verification_status=verification,
                    sport=rng.choice(["cricket", "football"]),
                    entities=["Mock Player", "Mock Team"],
                    data_quality=DataQuality.MOCK,
                )
            )
        return articles
