from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService


router = APIRouter(
    prefix="/api/payment",
    tags=["Payment"],
)

transactions = TransactionService()
audit = AuditService()


class PaymentFailureRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    razorpay_order_id: str = Field(min_length=1)
    razorpay_payment_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


@router.post("/failed")
def payment_failed(request: PaymentFailureRequest):
    try:
        transaction = transactions.mark_payment_failed(
            transaction_id=request.transaction_id,
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
        )

        audit.record(
            request.transaction_id,
            "PAYMENT_FAILED",
            {
                "razorpay_order_id": request.razorpay_order_id,
                "razorpay_payment_id": request.razorpay_payment_id,
                "reason": request.reason,
            },
        )

        return {
            "status": "payment_failed_recorded",
            "transaction_id": transaction.transaction_id,
            "transaction_status": transaction.status,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )