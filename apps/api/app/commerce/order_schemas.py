from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    transaction_id: str = Field(min_length=1)