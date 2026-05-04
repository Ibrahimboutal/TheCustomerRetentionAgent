from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

# =========================
# API Models (Production Hardened)
# =========================

class EventStreamRequest(BaseModel):
    customer_id: int
    event: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class EventStreamResponse(BaseModel):
    customer_id: int
    event: str
    churn_probability: float
    decision_made: str
    action_taken: str
    model_version: str

class GenerateDiscountRequest(BaseModel):
    customer_id: int

class GenerateDiscountResponse(BaseModel):
    status: str
    msg: str

class FlagVipRequest(BaseModel):
    customer_id: int

class FlagVipResponse(BaseModel):
    status: str
    msg: str

class DebateRequest(BaseModel):
    customer_id: int

class DebateResponse(BaseModel):
    customer: str
    churn_risk_score: str
    proposed_rate: str
    approved_rate: str
    justification: str
    roi: float

class EmailRequest(BaseModel):
    customer_id: int
    tone: str = "empathetic"

class EmailResponse(BaseModel):
    email_body: str
    safety_checked: bool
    ai_powered: bool

class OptimizeRequest(BaseModel):
    budget: float = Field(5000.0, gt=0)

class OptimizeResponse(BaseModel):
    status: str
    budget_used: float
    customers_optimized: int
    avg_discount_pct: float
    allocations: Dict[str, Any]
