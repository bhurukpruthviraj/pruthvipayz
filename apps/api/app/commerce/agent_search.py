from apps.api.app.agents.buyer_agent import BuyerAgent
from apps.api.app.agents.buyer_schemas import BuyerRequest
from apps.api.app.audit.demand_service import DemandService
from apps.api.app.catalog.catalog_service import get_catalog


class AgentSearchService:
    def __init__(self):
        self.buyer = BuyerAgent()
        self.demand = DemandService()

    @staticmethod
    def find_relevant_product(query: str, catalog: dict):
        query_words = {
            word.lower().strip(".,!?")
            for word in query.split()
            if len(word) >= 3
        }

        candidates = []

        for product in catalog["products"]:
            product_text = (
                f"{product['name']} "
                f"{product['description']} "
                f"{product['category']}"
            ).lower()

            score = sum(
                1
                for word in query_words
                if word in product_text
            )

            if score > 0:
                candidates.append((score, product))

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1]["price"],
            ),
            reverse=True,
        )

        return candidates[0][1] if candidates else None

    def search(
        self,
        query: str,
        max_budget: int,
    ):
        catalog = get_catalog()

        # First determine whether the request resembles a real
        # catalog product, regardless of its price.
        relevant_product = self.find_relevant_product(
            query,
            catalog,
        )

        if (
            relevant_product is not None
            and relevant_product["price"] > max_budget
        ):
            price_gap = relevant_product["price"] - max_budget

            self.demand.create(
                query=query,
                max_budget=max_budget,
                ai_provider="catalog_match",
                selected_product_id=relevant_product["id"],
                selected_product_name=relevant_product["name"],
                selected_product_price=relevant_product["price"],
                category=relevant_product["category"],
                confidence=None,
            )

            return {
                "matched": False,
                "query": query,
                "max_budget": max_budget,
                "ai_provider": "catalog_match",
                "reason": (
                    "A relevant product exists in the merchant "
                    "catalog, but it exceeds the buyer's budget."
                ),
                "opportunity": {
                    "product_id": relevant_product["id"],
                    "product_name": relevant_product["name"],
                    "category": relevant_product["category"],
                    "current_price": relevant_product["price"],
                    "buyer_budget": max_budget,
                    "price_gap": price_gap,
                    "currency": relevant_product["currency"],
                },
            }

        try:
            selection = self.buyer.select_product(
                BuyerRequest(
                    request=query,
                    max_budget=max_budget,
                ),
                catalog,
            )

            selected = next(
                product
                for product in catalog["products"]
                if product["id"] == selection.selected_product_id
            )

            self.demand.create(
                query=query,
                max_budget=max_budget,
                ai_provider=self.buyer.last_provider,
                selected_product_id=selected["id"],
                selected_product_name=selected["name"],
                selected_product_price=selected["price"],
                category=selected["category"],
                confidence=selection.confidence,
            )

            return {
                "matched": True,
                "query": query,
                "max_budget": max_budget,
                "ai_provider": self.buyer.last_provider,
                "recommended_product": {
                    "id": selected["id"],
                    "name": selected["name"],
                    "description": selected["description"],
                    "category": selected["category"],
                    "price": selected["price"],
                    "currency": selected["currency"],
                    "available": selected["available"],
                    "agent_purchase_allowed": selected[
                        "agent_purchase_allowed"
                    ],
                },
                "reason": selection.reason,
                "confidence": selection.confidence,
            }

        except ValueError:
            self.demand.create(
                query=query,
                max_budget=max_budget,
                ai_provider=self.buyer.last_provider,
                confidence=None,
            )

            return {
                "matched": False,
                "query": query,
                "max_budget": max_budget,
                "ai_provider": self.buyer.last_provider,
                "reason": (
                    "No suitable product was found in the "
                    "merchant catalog."
                ),
                "opportunity": None,
            }