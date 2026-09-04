from fastapi import APIRouter, HTTPException

from apps.api.app.agents.buyer_agent import BuyerAgent
from apps.api.app.agents.buyer_schemas import BuyerRequest
from apps.api.app.catalog.catalog_service import get_catalog


router = APIRouter(
    prefix="/api/buyer",
    tags=["Buyer Agent"],
)

buyer_agent = BuyerAgent()


@router.post("/select")
def select_product(request: BuyerRequest):
    try:
        catalog = get_catalog()
        return buyer_agent.select_product(request, catalog)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
