from xai_sdk import Client
from xai_sdk.chat import system, user

from apps.api.app.agents.ai_buyer import AIBuyer
from apps.api.app.agents.buyer_schemas import (
    BuyerRequest,
    BuyerSelection,
)
from apps.api.app.agents.llm_schemas import AIProductDecision
from apps.api.app.core.config import settings


class GrokBuyer(AIBuyer):
    def __init__(self):
        if not settings.xai_api_key:
            raise RuntimeError(
                "XAI_API_KEY is not configured."
            )

        self.client = Client(
            api_key=settings.xai_api_key
        )

    def select_product(
        self,
        buyer_request: BuyerRequest,
        catalog: dict,
    ) -> BuyerSelection:

        eligible_products = [
            product
            for product in catalog["products"]
            if product["available"]
            and product["agent_purchase_allowed"]
            and product["price"] <= buyer_request.max_budget
        ]

        if not eligible_products:
            raise ValueError(
                "No eligible product found within the buyer's budget."
            )

        catalog_text = "\n".join(
            [
                (
                    f"ID: {product['id']}\n"
                    f"Name: {product['name']}\n"
                    f"Description: {product['description']}\n"
                    f"Price: ₹{product['price']}\n"
                    f"Category: {product['category']}\n"
                    f"Stock: {product['stock']}\n"
                )
                for product in eligible_products
            ]
        )

        prompt = f"""
Buyer request:
{buyer_request.request}

Maximum budget:
₹{buyer_request.max_budget}

Eligible merchant products:
{catalog_text}

Select the single best product for this buyer.

Return:
- product_id: the exact ID of the selected catalog product
- reason: concise explanation of why it matches the buyer's intent
- confidence: your confidence from 0 to 1

Important:
- Only select a product from the provided catalog.
- Do not invent products.
- Do not invent prices.
- Do not authorize payment.
- Do not change the buyer's budget.
"""

        chat = self.client.chat.create(
            model="grok-4.6",
        )

        chat.append(
            system(
                "You are a product-selection agent. "
                "Your only job is to choose the best product "
                "from the provided merchant catalog. "
                "You never authorize payments."
            )
        )

        chat.append(user(prompt))

        response, decision = chat.parse(
            AIProductDecision
        )

        selected = next(
            (
                product
                for product in eligible_products
                if product["id"] == decision.product_id
            ),
            None,
        )

        if selected is None:
            raise ValueError(
                "Grok selected a product that does not exist "
                "in the eligible merchant catalog."
            )

        if selected["price"] > buyer_request.max_budget:
            raise ValueError(
                "Grok selected a product above the buyer's budget."
            )

        return BuyerSelection(
            buyer_request=buyer_request.request,
            selected_product_id=selected["id"],
            selected_product_name=selected["name"],
            price=selected["price"],
            currency=selected["currency"],
            buyer_max_budget=buyer_request.max_budget,
            reason=decision.reason,
            confidence=decision.confidence,
        )