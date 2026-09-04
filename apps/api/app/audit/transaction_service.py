from apps.api.app.audit.db_models import Transaction
from apps.api.app.core.database import SessionLocal


class TransactionService:
    def create(
        self,
        transaction_id: str,
        buyer_request: str,
        product_id: str,
        product_name: str,
        amount: int,
        buyer_max_amount: int,
        currency: str,
        status: str = "AUTHORIZED",
    ) -> Transaction:
        db = SessionLocal()

        try:
            transaction = Transaction(
                transaction_id=transaction_id,
                buyer_request=buyer_request,
                product_id=product_id,
                product_name=product_name,
                amount=amount,
                buyer_max_amount=buyer_max_amount,
                currency=currency,
                status=status,
            )

            db.add(transaction)
            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def get(self, transaction_id: str):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            return transaction

        finally:
            db.close()

    def update_status(
        self,
        transaction_id: str,
        status: str,
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            transaction.status = status

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def attach_order(
        self,
        transaction_id: str,
        razorpay_order_id: str,
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            transaction.razorpay_order_id = razorpay_order_id
            transaction.status = "ORDER_CREATED"

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def attach_payment(
        self,
        transaction_id: str,
        razorpay_payment_id: str,
        status: str = "PAYMENT_VERIFIED",
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.status = status

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def mark_payment_failed(
        self,
        transaction_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            if transaction.razorpay_order_id != razorpay_order_id:
                raise ValueError(
                    "Razorpay order does not match the transaction."
                )

            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.status = "PAYMENT_FAILED"

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def update_amount(
        self,
        transaction_id: str,
        amount: int,
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            if amount <= 0:
                raise ValueError(
                    "Transaction amount must be greater than zero."
                )

            if amount > transaction.buyer_max_amount:
                raise ValueError(
                    "Negotiated amount exceeds buyer spending authority."
                )

            transaction.amount = amount
            transaction.status = "NEGOTIATION_APPROVED"

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()

    def can_retry(
        self,
        transaction_id: str,
    ) -> bool:
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            return transaction.retry_count < 1

        finally:
            db.close()

    def increment_retry(
        self,
        transaction_id: str,
    ):
        db = SessionLocal()

        try:
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.transaction_id == transaction_id
                )
                .first()
            )

            if transaction is None:
                raise ValueError(
                    f"Unknown transaction: {transaction_id}"
                )

            if transaction.retry_count >= 1:
                raise ValueError(
                    "Retry limit exceeded."
                )

            transaction.retry_count += 1
            transaction.status = "RETRYING"

            db.commit()
            db.refresh(transaction)

            return transaction

        finally:
            db.close()