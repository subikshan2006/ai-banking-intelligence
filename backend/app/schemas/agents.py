from typing import Any, Literal
from pydantic import BaseModel, Field

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    duration_ms: float = 0.0
    status: Literal["success", "error"] = "success"
    error: str | None = None

class AgentResult(BaseModel):
    agent_name: str
    status: Literal["success", "error", "partial", "skipped"] = "success"
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0

class TaskStep(BaseModel):
    task_id: str
    agent_name: str
    action: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)  # list of task_ids that must finish before this step
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    result: AgentResult | None = None

class WorkflowPlan(BaseModel):
    plan_id: str
    correlation_id: str
    intent: str
    tasks: list[TaskStep] = Field(default_factory=list)
    created_at: str = ""
