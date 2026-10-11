import time
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.schemas.agents import AgentResult, ToolCallRecord
from app.tools.registry import registry

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        correlation_id: str,
        db: Session,
        tool_calls_accumulator: list[ToolCallRecord]
    ) -> Any:
        record = registry.execute_tool(
            name=tool_name,
            arguments=arguments,
            correlation_id=correlation_id,
            db=db,
            context={"agent": self.name}
        )
        tool_calls_accumulator.append(record)
        if record.status == "error":
            raise RuntimeError(f"Tool {tool_name} failed: {record.error}")
        return record.output

    def execute_task(
        self,
        action: str,
        arguments: dict[str, Any],
        correlation_id: str,
        db: Session
    ) -> AgentResult:
        start_time = time.perf_counter()
        tool_calls: list[ToolCallRecord] = []
        errors: list[str] = []

        try:
            handler_method = getattr(self, action, None)
            if not handler_method:
                raise NotImplementedError(f"Action '{action}' is not supported by agent '{self.name}'.")

            result_data, evidence = handler_method(
                arguments=arguments,
                correlation_id=correlation_id,
                db=db,
                tool_calls=tool_calls
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return AgentResult(
                agent_name=self.name,
                status="success",
                data=result_data,
                evidence=evidence if isinstance(evidence, list) else [evidence],
                tool_calls=tool_calls,
                errors=[],
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            err_msg = str(e)
            logger.error(f"[{self.name}] Error during action '{action}': {err_msg}")
            errors.append(err_msg)
            return AgentResult(
                agent_name=self.name,
                status="error",
                data={},
                evidence=[],
                tool_calls=tool_calls,
                errors=errors,
                duration_ms=duration_ms
            )
