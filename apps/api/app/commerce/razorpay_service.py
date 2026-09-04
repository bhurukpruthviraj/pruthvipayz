import hmac
import hashlib

import razorpay

from apps.api.app.commerce.authorization_schemas import Authorization
from apps.api.app.core.config import settings


class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                settings.razorpay_key_id,
                settings.razorpay_key_secret,
            )
        )

    def create_order(self, authorization: Authorization):
        if not authorization.authorized:
            raise ValueError(
                "Cannot create Razorpay order without authorization."
            )

        if authorization.approved_amount <= 0:
            raise ValueError(
                "Approved amount must be greater than zero."
            )

        order = self.client.order.create(
            {
                "amount": authorization.approved_amount * 100,
                "currency": authorization.currency,
                "receipt": f"pruthvipayz_{authorization.product_id}",
                "notes": {
                    "transaction_id": authorization.transaction_id,
                    "product_id": authorization.product_id,
                    "merchant_id": authorization.merchant_id,
                    "source": "pruthvipayz",
                },
            }
        )

        return order

    def create_bundle_order(
        self,
        transaction_id: str,
        approved_amount: int,
        currency: str,
        base_product: dict,
        add_on: dict,
    ):
        if approved_amount <= 0:
            raise ValueError(
                "Approved bundle amount must be greater than zero."
            )

        combined_price = (
            base_product["price"] + add_on["price"]
        )

        if approved_amount > combined_price:
            raise ValueError(
                "Approved bundle amount cannot exceed bundle price."
            )

        order = self.client.order.create(
            {
                "amount": approved_amount * 100,
                "currency": currency,
                "receipt": f"pruthvipayz_bundle_{transaction_id}",
                "notes": {
                    "transaction_id": transaction_id,
                    "merchant_id": "merchant_demo",
                    "source": "pruthvipayz_bundle",
                    "bundle": "true",
                    "base_product_id": base_product["id"],
                    "base_product_name": base_product["name"],
                    "base_product_price": str(base_product["price"]),
                    "add_on_product_id": add_on["id"],
                    "add_on_product_name": add_on["name"],
                    "add_on_product_price": str(add_on["price"]),
                    "bundle_original_price": str(combined_price),
                    "bundle_discount": str(
                        combined_price - approved_amount
                    ),
                },
            }
        )

        return order

    def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        generated_signature = hmac.new(
            settings.razorpay_key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            generated_signature,
            signature,
        )