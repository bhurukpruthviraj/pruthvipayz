from fastapi import APIRouter

from apps.api.app.policies.policy_engine import PolicyEngine
from apps.api.app.policies.policy_schemas import PolicyCheckRequest


router = APIRouter(
    prefix="/api/policy",
    tags=["Policy Engine"],
)

policy_engine = PolicyEngine()


@router.post("/check")
def check_policy(request: PolicyCheckRequest):
    return policy_engine.check(request)