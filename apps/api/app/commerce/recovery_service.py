from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService
from apps.api.app.commerce.authorization_schemas import Authorization
from apps.api.app.commerce.razorpay_service import RazorpayService


class RecoveryService:
    MAX_RETRIES = 1

    def __init__(self):
        self.transactions = TransactionService()
        self.audit = AuditService()
        self.razorpay = RazorpayService()

    def retry_payment(self, transaction_id: str):
        transaction = self.transactions.get(transaction_id)

        if transaction.status != "PAYMENT_FAILED":
            raise ValueError(
                f"Transaction is not recoverable from status "
                f"{transaction.status}."
            )

        if transaction.retry_count >= self.MAX_RETRIES:
            raise ValueError(
                "Retry limit exceeded. No further payment attempt is allowed."
            )

        self.audit.record(
            transaction_id,
            "RECOVERY_TRIGGERED",
            {
                "reason": "Payment failure",
                "retry_limit": self.MAX_RETRIES,
                "current_retry_count": transaction.retry_count,
            },
        )

        transaction = self.transactions.increment_retry(
            transaction_id
        )

        self.audit.record(
            transaction_id,
            "PAYMENT_RETRY",
            {
                "retry_number": transaction.retry_count,
            },
        )

        authorization = Authorization(
            transaction_id=transaction.transaction_id,
            authorized=True,
            buyer_max_amount=transaction.buyer_max_amount,
            approved_amount=transaction.amount,
            currency=transaction.currency,
            product_id=transaction.product_id,
            merchant_id="merchant_demo",
            reason="Bounded recovery retry authorized.",
        )

        razorpay_order = self.razorpay.create_order(
            authorization
        )

        self.transactions.attach_order(
            transaction_id=transaction.transaction_id,
            razorpay_order_id=razorpay_order["id"],
        )

        self.audit.record(
            transaction_id,
            "RECOVERY_ORDER_CREATED",
            {
                "razorpay_order_id": razorpay_order["id"],
                "retry_number": transaction.retry_count,
                "amount": razorpay_order["amount"],
            },
        )

        return {
            "status": "retry_order_created",
            "transaction_id": transaction.transaction_id,
            "retry_number": transaction.retry_count,
            "razorpay_order": razorpay_order,
        }