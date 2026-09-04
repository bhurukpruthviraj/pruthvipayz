from fastapi import APIRouter, HTTPException

from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService


router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"],
)

audit_service = AuditService()
transaction_service = TransactionService()


@router.get("/{transaction_id}")
def get_transaction_audit(transaction_id: str):
    try:
        transaction = transaction_service.get(transaction_id)

        events = audit_service.get_events(transaction_id)

        return {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "retry_count": transaction.retry_count,
            "razorpay_order_id": transaction.razorpay_order_id,
            "razorpay_payment_id": transaction.razorpay_payment_id,
            "events": [
                event.model_dump()
                for event in events
            ],
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
