from apps.api.app.catalog.catalog_service import get_catalog
from apps.api.app.merchant_policy import MerchantPolicyService


class RecommendationService:
    def __init__(self):
        self.policy_service = MerchantPolicyService()

    def get_add_ons(self, product_id: str, buyer_max_budget: int):
        catalog = get_catalog()
        products = catalog["products"]

        base_product = next(
            (product for product in products if product["id"] == product_id),
            None,
        )

        if not base_product:
            return {
                "status": "error",
                "message": "Base product not found.",
            }

        remaining_budget = buyer_max_budget - base_product["price"]

        affordable_add_ons = []
        bundle_opportunities = []

        for product in products:
            if product["id"] == product_id:
                continue

            if not product["available"]:
                continue

            if not product["agent_purchase_allowed"]:
                continue

            same_category = product["category"] == base_product["category"]
            combined_price = base_product["price"] + product["price"]
            bundle_gap = max(0, combined_price - buyer_max_budget)

            if product["price"] <= remaining_budget:
                affordable_add_ons.append(
                    {
                        **self._product_summary(product),
                        "category_match": same_category,
                        "remaining_authority_after_add_on": (
                            remaining_budget - product["price"]
                        ),
                        "reason": (
                            "Same-category add-on within buyer authority."
                            if same_category
                            else "Compatible catalog add-on within buyer authority."
                        ),
                    }
                )

            elif bundle_gap > 0:
                bundle_opportunities.append(
                    {
                        "base_product": self._product_summary(base_product),
                        "add_on": self._product_summary(product),
                        "combined_price": combined_price,
                        "buyer_max_budget": buyer_max_budget,
                        "price_gap": bundle_gap,
                        "category_match": same_category,
                        "negotiation_available": self._negotiation_can_cover(
                            bundle_gap
                        ),
                        "reason": (
                            "Same-category bundle exceeds buyer authority "
                            "but may be recoverable through bounded negotiation."
                            if same_category
                            else "Bundle exceeds buyer authority but may be "
                            "recoverable through bounded negotiation."
                        ),
                    }
                )

        affordable_add_ons.sort(
            key=lambda item: (
                not item["category_match"],
                item["price"],
            )
        )

        bundle_opportunities.sort(
            key=lambda item: (
                not item["negotiation_available"],
                item["price_gap"],
                not item["category_match"],
            )
        )

        return {
            "status": "ok",
            "base_product": self._product_summary(base_product),
            "buyer_max_budget": buyer_max_budget,
            "remaining_budget": remaining_budget,
            "recommendations": affordable_add_ons[:3],
            "bundle_opportunities": bundle_opportunities[:3],
            "message": self._message(
                affordable_add_ons,
                bundle_opportunities,
            ),
        }

    def _negotiation_can_cover(self, price_gap: int) -> bool:
        policy = self.policy_service.get()

        return (
            policy["ai_negotiation_enabled"]
            and price_gap <= policy["max_ai_discount"]
        )

    @staticmethod
    def _message(add_ons, bundles):
        if add_ons:
            return "Affordable add-ons found."

        if any(bundle["negotiation_available"] for bundle in bundles):
            return "Bundle opportunities found within merchant negotiation authority."

        if bundles:
            return "Bundle opportunities found, but merchant policy cannot cover the current price gap."

        return "No add-on or bundle opportunity fits the current buyer authority."

    @staticmethod
    def _product_summary(product):
        return {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "currency": product.get("currency", "INR"),
            "category": product["category"],
            "stock": product["stock"],
        }