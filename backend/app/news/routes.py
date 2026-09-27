from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.news.schemas import NewsArticleOut
from database.models.context import NewsArticle

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=list[NewsArticleOut])
def list_news(
    category: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
    if category:
        stmt = stmt.where(NewsArticle.category == category)
    if verification_status:
        stmt = stmt.where(NewsArticle.verification_status == verification_status)
    return db.scalars(stmt).all()
