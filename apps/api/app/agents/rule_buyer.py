from apps.api.app.agents.ai_buyer import AIBuyer
from apps.api.app.agents.buyer_schemas import (
    BuyerRequest,
    BuyerSelection,
)


class RuleBasedBuyer(AIBuyer):
    def select_product(
        self,
        buyer_request: BuyerRequest,
        catalog: dict,
    ) -> BuyerSelection:
        products = catalog["products"]

        eligible_products = [
            product
            for product in products
            if product["available"]
            and product["agent_purchase_allowed"]
            and product["price"] <= buyer_request.max_budget
        ]

        if not eligible_products:
            raise ValueError(
                "No eligible product found within the buyer's budget."
            )

        request_text = buyer_request.request.lower()

        keyword_scores = []

        for product in eligible_products:
            score = 0

            product_text = (
                f"{product['name']} "
                f"{product['description']} "
                f"{product['category']}"
            ).lower()

            for word in request_text.split():
                if len(word) >= 3 and word in product_text:
                    score += 1

            keyword_scores.append((score, product))

        keyword_scores.sort(
            key=lambda item: (item[0], -item[1]["price"]),
            reverse=True,
        )

        _, selected = keyword_scores[0]

        return BuyerSelection(
            buyer_request=buyer_request.request,
            selected_product_id=selected["id"],
            selected_product_name=selected["name"],
            price=selected["price"],
            currency=selected["currency"],
            buyer_max_budget=buyer_request.max_budget,
            reason=(
                f"Selected {selected['name']} because it matches "
                f"the buyer's request and is within the "
                f"₹{buyer_request.max_budget} budget."
            ),
            confidence=0.85,
        )