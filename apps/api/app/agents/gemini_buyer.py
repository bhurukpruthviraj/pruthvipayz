from google import genai

from apps.api.app.agents.ai_buyer import AIBuyer
from apps.api.app.agents.buyer_schemas import (
    BuyerRequest,
    BuyerSelection,
)
from apps.api.app.agents.llm_schemas import AIProductDecision
from apps.api.app.core.config import settings


class GeminiBuyer(AIBuyer):
    MODEL = "gemini-3.7-flash"

    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
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

        catalog_text = "\n\n".join(
            [
                (
                    f"Product ID: {product['id']}\n"
                    f"Name: {product['name']}\n"
                    f"Description: {product['description']}\n"
                    f"Category: {product['category']}\n"
                    f"Price: ₹{product['price']}\n"
                    f"Stock: {product['stock']}"
                )
                for product in eligible_products
            ]
        )

        prompt = f"""
You are the product-selection component of an AI buyer.

Buyer request:
{buyer_request.request}

Maximum buyer budget:
₹{buyer_request.max_budget}

Merchant catalog:
{catalog_text}

Choose the single best product for the buyer.

Rules:
- product_id MUST be an exact ID from the catalog.
- Only choose from the provided products.
- Never invent a product.
- Never invent a price.
- Never change the buyer budget.
- Never authorize payment.
- Explain briefly why the selected product best matches the request.
- confidence must be between 0 and 1.
"""

        interaction = self.client.interactions.create(
            model=self.MODEL,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": AIProductDecision.model_json_schema(),
            },
        )

        if not interaction.output_text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        decision = AIProductDecision.model_validate_json(
            interaction.output_text
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
                "Gemini selected a product that does not exist "
                "in the eligible merchant catalog."
            )

        if selected["price"] > buyer_request.max_budget:
            raise ValueError(
                "Gemini selected a product above the buyer's budget."
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