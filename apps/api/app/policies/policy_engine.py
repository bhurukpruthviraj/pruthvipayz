from apps.api.app.policies.policy_schemas import (
    PolicyCheckRequest,
    PolicyCheckResult,
)
from apps.api.app.catalog.catalog_service import get_catalog


class PolicyEngine:
    ALLOWED_MERCHANT_ID = "merchant_demo"
    ALLOWED_CURRENCY = "INR"

    def check(self, request: PolicyCheckRequest) -> PolicyCheckResult:
        catalog = get_catalog()

        product = next(
            (
                item
                for item in catalog["products"]
                if item["id"] == request.product_id
            ),
            None,
        )

        checks = {
            "merchant_allowed": request.merchant_id == self.ALLOWED_MERCHANT_ID,
            "currency_allowed": request.currency.upper() == self.ALLOWED_CURRENCY,
            "within_buyer_budget": request.amount <= request.buyer_max_budget,
            "product_exists": product is not None,
            "product_available": False,
            "agent_purchase_allowed": False,
            "amount_matches_catalog": False,
        }

        if product is not None:
            checks["product_available"] = (
                product["available"] and product["stock"] > 0
            )
            checks["agent_purchase_allowed"] = product["agent_purchase_allowed"]
            checks["amount_matches_catalog"] = request.amount == product["price"]

        allowed = all(checks.values())

        if allowed:
            reason = "Transaction passed all policy checks."
        else:
            failed_checks = [
                name for name, passed in checks.items() if not passed
            ]
            reason = (
                "Transaction blocked by policy checks: "
                + ", ".join(failed_checks)
                + "."
            )

        return PolicyCheckResult(
            allowed=allowed,
            product_id=request.product_id,
            amount=request.amount,
            checks=checks,
            reason=reason,
        )
