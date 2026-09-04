from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.commerce.recommendation_service import RecommendationService


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

service = RecommendationService()


class AddOnRequest(BaseModel):
    product_id: str
    buyer_max_budget: int = Field(gt=0)


@router.post("/add-ons")
def get_add_ons(request: AddOnRequest):
    result = service.get_add_ons(
        product_id=request.product_id,
        buyer_max_budget=request.buyer_max_budget,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    return result