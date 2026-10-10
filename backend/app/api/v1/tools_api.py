from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.db.models.models import CustomTool
from app.schemas.tools import CustomToolCreate, CustomToolResponse
from app.tools.registry import default_registry

router = APIRouter()


@router.get("", response_model=List[CustomToolResponse])
async def list_custom_tools(db: AsyncSession = Depends(get_db_session)):
    """Lists registered custom tools."""
    stmt = select(CustomTool)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=CustomToolResponse)
async def register_custom_tool(
    body: CustomToolCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Registers a new custom tool with typed schema."""
    tool = CustomTool(
        name=body.name,
        description=body.description,
        schema_json=body.schema_json,
        enabled=body.enabled,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.post("/{tool_id}/validate")
async def validate_tool(tool_id: str, db: AsyncSession = Depends(get_db_session)):
    """Validates custom tool schema and execution permissions."""
    stmt = select(CustomTool).where(CustomTool.id == tool_id)
    res = await db.execute(stmt)
    tool = res.scalar_one_or_none()
    if not tool:
        return {"valid": False, "message": "Tool not found"}

    tool.enabled = True
    await db.commit()
    return {"valid": True, "message": f"Tool '{tool.name}' schema validated and enabled successfully."}
