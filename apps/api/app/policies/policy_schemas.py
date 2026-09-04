from pydantic import BaseModel


class PolicyCheckRequest(BaseModel):
    product_id: str
    amount: int
    currency: str
    buyer_max_budget: int
    merchant_id: str


class PolicyCheckResult(BaseModel):
    allowed: bool
    product_id: str
    amount: int
    checks: dict[str, bool]
    reason: str
