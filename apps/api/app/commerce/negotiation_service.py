from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService
from apps.api.app.merchant_policy import MerchantPolicyService


class NegotiationService:
    MAX_AI_DISCOUNT = 299

    def __init__(self):
        self.transactions = TransactionService()
        self.audit = AuditService()
        self.policy = MerchantPolicyService()

    def propose(self, transaction_id: str, buyer_offer: int):
        transaction = self.transactions.get(transaction_id)

        if transaction.status not in {
            "AUTHORIZED",
            "NEGOTIATION_REQUIRED",
            "ORDER_CREATED",
        }:
            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "reason": (
                    f"Negotiation is not allowed from transaction "
                    f"status {transaction.status}."
                ),
            }

        previous_events = self.audit.get_events(transaction_id)

        if any(
            event.event_type in {
                "NEGOTIATION_APPROVED",
                "NEGOTIATION_REJECTED",
            }
            for event in previous_events
        ):
            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "reason": "Negotiation has already been closed for this purchase.",
            }
            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "reason": "This transaction has already completed negotiation.",
            }

        original_price = transaction.amount

        if buyer_offer <= 0:
            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "reason": "Offer must be greater than zero.",
            }

        if buyer_offer > transaction.buyer_max_amount:
            self.audit.record(
                transaction_id,
                "NEGOTIATION_REJECTED",
                {
                    "buyer_offer": buyer_offer,
                    "buyer_max_amount": transaction.buyer_max_amount,
                    "reason": "Offer exceeds buyer spending authority.",
                },
            )

            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "original_price": original_price,
                "buyer_offer": buyer_offer,
                "buyer_max_amount": transaction.buyer_max_amount,
                "reason": "Offer exceeds buyer spending authority.",
            }

        policy = self.policy.get()

        if not policy["ai_negotiation_enabled"]:
            self.audit.record(
                transaction_id,
                "NEGOTIATION_REJECTED",
                {
                    "buyer_offer": buyer_offer,
                    "reason": "AI negotiation is disabled by merchant policy.",
                },
            )

            return {
                "status": "rejected",
                "transaction_id": transaction_id,
                "original_price": original_price,
                "buyer_offer": buyer_offer,
                "reason": "AI negotiation is currently disabled by the merchant.",
            }

        discount = max(original_price - buyer_offer, 0)
        max_discount = policy["max_ai_discount"]

        if discount <= max_discount:
            updated = self.transactions.update_amount(
                transaction_id,
                buyer_offer,
            )

            self.audit.record(
                transaction_id,
                "NEGOTIATION_APPROVED",
                {
                    "product_id": transaction.product_id,
                    "original_price": original_price,
                    "buyer_offer": buyer_offer,
                    "discount": discount,
                    
                    "final_price": updated.amount,
                },
            )

            return {
                "status": "approved",
                "transaction_id": transaction_id,
                "product_id": transaction.product_id,
                "product_name": transaction.product_name,
                "original_price": original_price,
                "buyer_offer": buyer_offer,
                "discount": discount,
                
                "final_price": updated.amount,
                "buyer_max_amount": transaction.buyer_max_amount,
                "reason": (
                    "Offer is within the merchant's AI negotiation limit "
                    "and the buyer's spending authority."
                ),
            }

        self.audit.record(
            transaction_id,
            "NEGOTIATION_REJECTED",
            {
                "product_id": transaction.product_id,
                "original_price": original_price,
                "buyer_offer": buyer_offer,
                "discount": discount,
                "merchant_max_discount": max_discount,
            },
        )

        return {
            "status": "rejected",
            "transaction_id": transaction_id,
            "product_id": transaction.product_id,
            "product_name": transaction.product_name,
            "original_price": original_price,
            "buyer_offer": buyer_offer,
            "discount": discount,
            
            "reason": (
                "That price isn't available for this purchase."
            ),
        }
