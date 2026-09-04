from fastapi import APIRouter

from pydantic import BaseModel

from apps.api.app.commerce.negotiation_service import NegotiationService


router = APIRouter(
    prefix="/api/negotiation",
    tags=["Negotiation"],
)

negotiation_service = NegotiationService()


class NegotiationRequest(BaseModel):
    transaction_id: str
    buyer_offer: int


@router.post("/propose")
def propose_negotiation(request: NegotiationRequest):
    return negotiation_service.propose(
        transaction_id=request.transaction_id,
        buyer_offer=request.buyer_offer,
    )
