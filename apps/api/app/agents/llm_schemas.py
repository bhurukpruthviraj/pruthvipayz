from pydantic import BaseModel, Field


class AIProductDecision(BaseModel):
    product_id: str
    reason: str
    confidence: float = Field(ge=0, le=1)