from apps.api.app.agents.buyer_schemas import BuyerRequest
from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService
from apps.api.app.commerce.agent_search import AgentSearchService
from apps.api.app.commerce.authorization_schemas import Authorization
from apps.api.app.commerce.commerce_service import CommerceService
from apps.api.app.commerce.razorpay_service import RazorpayService
from apps.api.app.audit.demand_service import DemandService
from apps.api.app.catalog.catalog_service import get_catalog


class AgentPurchaseService:
    def __init__(self):
        self.commerce = CommerceService()
        self.search = AgentSearchService()
        self.transactions = TransactionService()
        self.audit = AuditService()
        self.razorpay = RazorpayService()
        self.demand = DemandService()

    def purchase(
        self,
        request_text: str,
        max_budget: int,
    ):
        # Preserve exact buyer intent before asking the general
        # product-selection agent to choose among affordable products.
        search_result = self.search.search(
            query=request_text,
            max_budget=max_budget,
        )

        if (
            not search_result["matched"]
            and search_result.get("opportunity")
        ):
            opportunity = search_result["opportunity"]
            transaction_id = self.audit.start_transaction()

            product = next(
                product
                for product in get_catalog()["products"]
                if product["id"] == opportunity["product_id"]
            )

            self.audit.record(
                transaction_id,
                "BUYER_REQUEST",
                {
                    "request": request_text,
                    "max_budget": max_budget,
                },
            )

            self.audit.record(
                transaction_id,
                "CATALOG_SEARCH",
                {
                    "merchant_id": "merchant_demo",
                    "product_count": len(get_catalog()["products"]),
                },
            )

            self.audit.record(
                transaction_id,
                "PRODUCT_SELECTED",
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "price": product["price"],
                    "confidence": None,
                    "provider": "catalog_match",
                },
            )

            self.audit.record(
                transaction_id,
                "NEGOTIATION_REQUIRED",
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "catalog_price": product["price"],
                    "buyer_max_amount": max_budget,
                    "price_gap": product["price"] - max_budget,
                },
            )

            self.transactions.create(
                transaction_id=transaction_id,
                buyer_request=request_text,
                product_id=product["id"],
                product_name=product["name"],
                amount=product["price"],
                buyer_max_amount=max_budget,
                currency=product["currency"],
                status="NEGOTIATION_REQUIRED",
            )

            return {
                "status": "negotiation_required",
                "transaction_id": transaction_id,
                "product": {
                    "buyer_request": request_text,
                    "selected_product_id": product["id"],
                    "selected_product_name": product["name"],
                    "price": product["price"],
                    "currency": product["currency"],
                    "buyer_max_budget": max_budget,
                    "reason": (
                        "The exact requested product is above the buyer's "
                        "budget. Negotiation is available instead of "
                        "substituting another product."
                    ),
                    "confidence": None,
                },
                "opportunity": opportunity,
                "authorization": {
                    "authorized": False,
                    "buyer_max_amount": max_budget,
                    "approved_amount": 0,
                    "currency": product["currency"],
                    "product_id": product["id"],
                    "merchant_id": "merchant_demo",
                    "reason": "Purchase requires negotiation before authorization.",
                },
                "audit": [
                    event.model_dump()
                    for event in self.audit.get_events(transaction_id)
                ],
            }

        result = self.commerce.evaluate_purchase(
            BuyerRequest(
                request=request_text,
                max_budget=max_budget,
            )
        )

        authorization = Authorization(
            **result["authorization"]
        )

        self.demand.create(
            query=request_text,
            max_budget=max_budget,
            ai_provider=result["audit"][
                next(
                    i
                    for i, event in enumerate(result["audit"])
                    if event["event_type"] == "AI_PROVIDER_USED"
                )
            ]["details"]["provider"],
            selected_product_id=result["selection"][
                "selected_product_id"
            ],
            selected_product_name=result["selection"][
                "selected_product_name"
            ],
            selected_product_price=result["selection"]["price"],
            category=next(
                product["category"]
                for product in get_catalog()["products"]
                if product["id"] == result["selection"]["selected_product_id"]
            ),
            confidence=result["selection"]["confidence"],
        )

        if not authorization.authorized:
            return {
                "status": "blocked",
                "transaction_id": authorization.transaction_id,
                "authorization": authorization.model_dump(),
                "audit": result["audit"],
            }

        razorpay_order = self.razorpay.create_order(
            authorization
        )

        self.transactions.attach_order(
            transaction_id=authorization.transaction_id,
            razorpay_order_id=razorpay_order["id"],
        )

        self.audit.record(
            authorization.transaction_id,
            "ORDER_CREATED",
            {
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
            },
        )

        return {
            "status": "payment_ready",
            "transaction_id": authorization.transaction_id,
            "product": result["selection"],
            "authorization": authorization.model_dump(),
            "payment": {
                "provider": "razorpay",
                "order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
            },
            "audit": [
                event.model_dump()
                for event in self.audit.get_events(
                    authorization.transaction_id
                )
            ],
        }
