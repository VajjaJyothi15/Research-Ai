import asyncio
import time
from typing import Any, Dict, Optional
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.models import ToolCallLog
from app.tools.registry import ToolRegistry, default_registry


class ToolDispatcher:
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or default_registry

    async def dispatch(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        run_id: str,
        stage: str = "execution",
        db: Optional[AsyncSession] = None,
        max_retries: int = 2,
        timeout_seconds: float = 30.0,
    ) -> Any:
        start_time = time.time()
        tool = self.registry.get_tool(tool_name)

        if not tool:
            err_msg = f"Tool '{tool_name}' is not registered or allowed."
            logger.error(err_msg)
            await self._log_tool_call(
                db, run_id, stage, tool_name, arguments, "FAILED", None, err_msg, 0, 0
            )
            raise ValueError(err_msg)

        # Validate arguments against Pydantic schema
        try:
            validated_args = tool.input_schema.model_validate(arguments)
        except ValidationError as ve:
            err_msg = f"Invalid arguments for tool '{tool_name}': {ve.errors()}"
            logger.error(err_msg)
            await self._log_tool_call(
                db, run_id, stage, tool_name, arguments, "FAILED", None, err_msg, 0, 0
            )
            raise ValueError(err_msg)

        # Execute handler with retry loop & timeout
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                res = await asyncio.wait_for(tool.handler(validated_args), timeout=timeout_seconds)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Format result summary
                summary = str(res)[:500]
                await self._log_tool_call(
                    db, run_id, stage, tool_name, arguments, "SUCCESS", summary, None, duration_ms, attempt
                )
                return res
            except Exception as e:
                last_exception = e
                logger.warning(f"Tool '{tool_name}' execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        duration_ms = int((time.time() - start_time) * 1000)
        err_msg = f"Tool execution failed after {max_retries + 1} attempts: {str(last_exception)}"
        await self._log_tool_call(
            db, run_id, stage, tool_name, arguments, "FAILED", None, err_msg, duration_ms, max_retries
        )
        raise RuntimeError(err_msg)

    async def _log_tool_call(
        self,
        db: Optional[AsyncSession],
        run_id: str,
        stage: str,
        tool_name: str,
        arguments: Dict[str, Any],
        status: str,
        summary: Optional[str],
        error_msg: Optional[str],
        duration_ms: int,
        retry_count: int,
    ):
        if not db:
            return
        try:
            log_entry = ToolCallLog(
                run_id=run_id,
                stage=stage,
                tool_name=tool_name,
                arguments_json=arguments,
                status=status,
                result_summary=summary,
                error_message=error_msg,
                duration_ms=duration_ms,
                retry_count=retry_count,
            )
            db.add(log_entry)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to log tool call to database: {e}")


dispatcher = ToolDispatcher()
