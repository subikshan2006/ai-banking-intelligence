from typing import Literal
from pydantic import BaseModel, Field

class EvaluationCaseResult(BaseModel):
    case_id: str
    prompt: str
    expected_intent: str
    actual_intent: str
    expected_agents: list[str] = Field(default_factory=list)
    actual_agents: list[str] = Field(default_factory=list)
    status: Literal["PASSED", "FAILED"]
    grounded: bool = True
    execution_time_ms: float = 0.0
    details: str = ""

class EvaluationResponse(BaseModel):
    evaluation_id: str
    timestamp: str
    total_cases: int
    passed_cases: int
    accuracy_rate: float
    mode: str
    results: list[EvaluationCaseResult] = Field(default_factory=list)
