from fastapi import APIRouter
from pydantic import BaseModel, Field
from apps.api.app.commerce.agent_purchase import AgentPurchaseService
from apps.api.app.catalog.catalog_service import get_catalog
from apps.api.app.commerce.agent_search import AgentSearchService


router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"],
)

search_service = AgentSearchService()
purchase_service = AgentPurchaseService()

class AgentSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    max_budget: int = Field(gt=0)

class AgentPurchaseRequest(BaseModel):
    request: str = Field(min_length=1)
    max_budget: int = Field(gt=0)

@router.get("/catalog")
def agent_catalog():
    catalog = get_catalog()

    return {
        "protocol": "pruthvipayz-agent-commerce-v1",
        "merchant": catalog["merchant"],
        "capabilities": {
            "product_discovery": True,
            "agent_purchase": True,
            "policy_authorization": True,
            "razorpay_test_mode": True,
        },
        "products": catalog["products"],
    }


@router.post("/search")
def agent_search(request: AgentSearchRequest):
    return search_service.search(
        query=request.query,
        max_budget=request.max_budget,
    )

@router.post("/purchase")
def agent_purchase(request: AgentPurchaseRequest):
    return purchase_service.purchase(
        request_text=request.request,
        max_budget=request.max_budget,
    )    