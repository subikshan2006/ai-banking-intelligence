import time
import json
import logging
from typing import Any, Callable, Type
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from app.schemas.agents import ToolCallRecord

logger = logging.getLogger(__name__)

class ToolDefinition(BaseModel):
    name: str
    description: str
    permission: str = "READ_ONLY"  # READ_ONLY, ELEVATED_READ, STATE_CHANGING_APPROVAL_REQUIRED
    is_state_changing: bool = False
    args_schema: Any = None  # Pydantic Model class
    handler: Any = None      # Callable

    class Config:
        arbitrary_types_allowed = True

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        permission: str = "READ_ONLY",
        is_state_changing: bool = False,
        args_schema: Type[BaseModel] | None = None
    ):
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                permission=permission,
                is_state_changing=is_state_changing,
                args_schema=args_schema,
                handler=func
            )
            return func
        return decorator

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        result = []
        for name, t in self._tools.items():
            schema_json = {}
            if t.args_schema:
                schema_json = t.args_schema.model_json_schema()
            result.append({
                "name": t.name,
                "description": t.description,
                "permission": t.permission,
                "is_state_changing": t.is_state_changing,
                "parameters": schema_json
            })
        return result

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        correlation_id: str,
        db: Session,
        context: dict[str, Any] | None = None
    ) -> ToolCallRecord:
        tool_def = self._tools.get(name)
        if not tool_def:
            return ToolCallRecord(
                tool_name=name,
                arguments=arguments,
                status="error",
                error=f"Tool '{name}' is not registered in the system Tool Registry.",
                duration_ms=0.0
            )

        start_time = time.perf_counter()
        validated_args = arguments

        # Pydantic argument validation
        if tool_def.args_schema:
            try:
                validated_model = tool_def.args_schema(**arguments)
                validated_args = validated_model.model_dump()
            except ValidationError as ve:
                duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                return ToolCallRecord(
                    tool_name=name,
                    arguments=arguments,
                    status="error",
                    error=f"Invalid arguments for tool '{name}': {ve.errors()}",
                    duration_ms=duration_ms
                )

        try:
            # Execute tool handler
            output = tool_def.handler(db=db, **validated_args)
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            
            # Record audit event
            try:
                from app.services.audit_service import audit_service
                audit_service.log_event(
                    correlation_id=correlation_id,
                    actor="ToolRegistry",
                    event_type="TOOL_COMPLETED",
                    tool_name=name,
                    details={"arguments": validated_args, "duration_ms": duration_ms},
                    duration_ms=duration_ms,
                    status="SUCCESS",
                    db=db
                )
            except Exception as ae:
                logger.warning(f"Audit log error: {ae}")

            return ToolCallRecord(
                tool_name=name,
                arguments=validated_args,
                output=output,
                duration_ms=duration_ms,
                status="success"
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            
            try:
                from app.services.audit_service import audit_service
                audit_service.log_event(
                    correlation_id=correlation_id,
                    actor="ToolRegistry",
                    event_type="TOOL_FAILED",
                    tool_name=name,
                    details={"arguments": validated_args, "error": str(e)},
                    duration_ms=duration_ms,
                    status="ERROR",
                    db=db
                )
            except Exception:
                pass

            return ToolCallRecord(
                tool_name=name,
                arguments=arguments,
                status="error",
                error=str(e),
                duration_ms=duration_ms
            )

registry = ToolRegistry()
