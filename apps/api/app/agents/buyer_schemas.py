from pydantic import BaseModel, Field


class BuyerRequest(BaseModel):
    request: str = Field(min_length=1)
    max_budget: int = Field(gt=0)


class BuyerSelection(BaseModel):
    buyer_request: str
    selected_product_id: str
    selected_product_name: str
    price: int
    currency: str
    buyer_max_budget: int
    reason: str
    confidence: float = Field(ge=0, le=1)
