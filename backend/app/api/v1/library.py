from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.db.models.models import Source
from app.schemas.evidence import SourceResponse

router = APIRouter()


@router.get("/sources", response_model=List[SourceResponse])
async def list_saved_sources(db: AsyncSession = Depends(get_db_session)):
    """Lists saved sources in the user Source Library."""
    stmt = select(Source).order_by(Source.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()
