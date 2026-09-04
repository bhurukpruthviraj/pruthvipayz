from pydantic import BaseModel


class Authorization(BaseModel):
    transaction_id: str
    authorized: bool
    buyer_max_amount: int
    approved_amount: int
    currency: str
    product_id: str
    merchant_id: str
    reason: str