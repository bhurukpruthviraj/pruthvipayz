from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.commerce.recovery_service import RecoveryService


router = APIRouter(
    prefix="/api/recovery",
    tags=["Recovery"],
)

recovery_service = RecoveryService()


class RecoveryRequest(BaseModel):
    transaction_id: str = Field(min_length=1)


@router.post("/retry")
def retry_payment(request: RecoveryRequest):
    try:
        return recovery_service.retry_payment(
            request.transaction_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )