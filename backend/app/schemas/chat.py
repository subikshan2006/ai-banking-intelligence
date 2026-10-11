from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.agents import ToolCallRecord

class ExecutionTraceItem(BaseModel):
    step_id: str
    phase: Literal["INTENT_CLASSIFICATION", "PLANNING", "AGENT_EXECUTION", "TOOL_CALL", "AGGREGATION", "VALIDATION"]
    agent_name: str | None = None
    tool_name: str | None = None
    input_data: Any = None
    output_data: Any = None
    status: Literal["SUCCESS", "ERROR", "WARNING", "SKIPPED"] = "SUCCESS"
    duration_ms: float = 0.0
    timestamp: str = ""

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    correlation_id: str | None = None
    demo_role: str = "manager"

class ChatResponse(BaseModel):
    correlation_id: str
    intent: str
    execution_mode: Literal["deterministic_fallback", "llm"]
    status: Literal["completed", "failed", "clarification_needed"]
    answer: str
    agents_involved: list[str] = Field(default_factory=list)
    tool_results: list[ToolCallRecord] = Field(default_factory=list)
    trace: list[ExecutionTraceItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    structured_data: dict[str, Any] = Field(default_factory=dict)
