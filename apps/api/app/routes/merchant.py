from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.api.app.audit.insights_service import InsightsService
from apps.api.app.merchant_policy import MerchantPolicyService


router = APIRouter(
    prefix="/api/merchant",
    tags=["Merchant"],
)

insights_service = InsightsService()
policy_service = MerchantPolicyService()


class MerchantPolicyUpdate(BaseModel):
    ai_negotiation_enabled: bool
    max_ai_discount: int


@router.get("/insights")
def merchant_insights():
    return insights_service.summary()


@router.get("/policy")
def merchant_policy():
    return policy_service.get()


@router.put("/policy")
def update_merchant_policy(request: MerchantPolicyUpdate):
    try:
        return {
            "status": "updated",
            "policy": policy_service.update(
                ai_negotiation_enabled=request.ai_negotiation_enabled,
                max_ai_discount=request.max_ai_discount,
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
