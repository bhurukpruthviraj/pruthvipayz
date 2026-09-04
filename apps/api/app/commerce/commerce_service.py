from apps.api.app.agents.buyer_agent import BuyerAgent
from apps.api.app.agents.buyer_schemas import BuyerRequest
from apps.api.app.audit.audit_service import AuditService
from apps.api.app.audit.transaction_service import TransactionService
from apps.api.app.catalog.catalog_service import get_catalog
from apps.api.app.commerce.authorization_schemas import Authorization
from apps.api.app.policies.policy_engine import PolicyEngine
from apps.api.app.policies.policy_schemas import PolicyCheckRequest


class CommerceService:
    def __init__(self):
        self.buyer_agent = BuyerAgent()
        self.policy_engine = PolicyEngine()
        self.audit = AuditService()
        self.transactions = TransactionService()

    def evaluate_purchase(self, buyer_request: BuyerRequest):
        transaction_id = self.audit.start_transaction()

        self.audit.record(
            transaction_id,
            "BUYER_REQUEST",
            {
                "request": buyer_request.request,
                "max_budget": buyer_request.max_budget,
            },
        )

        catalog = get_catalog()

        self.audit.record(
            transaction_id,
            "CATALOG_SEARCH",
            {
                "merchant_id": catalog["merchant"]["id"],
                "product_count": len(catalog["products"]),
            },
        )

        selection = self.buyer_agent.select_product(
            buyer_request,
            catalog,
        )

        self.audit.record(
            transaction_id,
            "AI_PROVIDER_USED",
            {
                "provider": self.buyer_agent.last_provider,
            },
        )

        self.audit.record(
            transaction_id,
            "PRODUCT_SELECTED",
            {
                "product_id": selection.selected_product_id,
                "product_name": selection.selected_product_name,
                "price": selection.price,
                "confidence": selection.confidence,
                "provider": self.buyer_agent.last_provider,
            },
        )
        

        policy_result = self.policy_engine.check(
            PolicyCheckRequest(
                product_id=selection.selected_product_id,
                amount=selection.price,
                currency=selection.currency,
                buyer_max_budget=selection.buyer_max_budget,
                merchant_id=catalog["merchant"]["id"],
            )
        )

        self.audit.record(
            transaction_id,
            "POLICY_CHECK",
            {
                "allowed": policy_result.allowed,
                "checks": policy_result.checks,
            },
        )

        authorization = Authorization(
            transaction_id=transaction_id,
            authorized=policy_result.allowed,
            buyer_max_amount=selection.buyer_max_budget,
            approved_amount=selection.price
            if policy_result.allowed
            else 0,
            currency=selection.currency,
            product_id=selection.selected_product_id,
            merchant_id=catalog["merchant"]["id"],
            reason=policy_result.reason,
        )

        self.audit.record(
            transaction_id,
            "AUTHORIZATION_GRANTED"
            if authorization.authorized
            else "AUTHORIZATION_BLOCKED",
            {
                "authorized": authorization.authorized,
                "approved_amount": authorization.approved_amount,
                "buyer_max_amount": authorization.buyer_max_amount,
                "reason": authorization.reason,
            },
        )

        self.transactions.create(
            transaction_id=transaction_id,
            buyer_request=buyer_request.request,
            product_id=selection.selected_product_id,
            product_name=selection.selected_product_name,
            amount=authorization.approved_amount,
            buyer_max_amount=buyer_request.max_budget,
            currency=authorization.currency,
            status=(
                "AUTHORIZED"
                if authorization.authorized
                else "BLOCKED"
            ),
        )

        return {
            "transaction_id": transaction_id,
            "buyer_request": buyer_request.request,
            "selection": selection.model_dump(),
            "policy": policy_result.model_dump(),
            "authorization": authorization.model_dump(),
            "audit": [
                event.model_dump()
                for event in self.audit.get_events(transaction_id)
            ],
        }