from pydantic import BaseModel, Field


class PaymentVerificationRequest(BaseModel):
    order_id: str = Field(min_length=1)
    payment_id: str = Field(min_length=1)
    signature: str = Field(min_length=1)