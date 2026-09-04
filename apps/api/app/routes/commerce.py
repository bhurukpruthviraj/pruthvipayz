from fastapi import APIRouter

from apps.api.app.agents.buyer_schemas import BuyerRequest
from apps.api.app.commerce.commerce_service import CommerceService


router = APIRouter(
    prefix="/api/commerce",
    tags=["Commerce"],
)

commerce_service = CommerceService()


@router.post("/evaluate")
def evaluate_purchase(request: BuyerRequest):
    return commerce_service.evaluate_purchase(request)