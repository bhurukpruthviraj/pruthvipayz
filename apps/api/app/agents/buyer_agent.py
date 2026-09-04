from apps.api.app.agents.buyer_schemas import (
    BuyerRequest,
    BuyerSelection,
)
from apps.api.app.agents.gemini_buyer import GeminiBuyer
from apps.api.app.agents.rule_buyer import RuleBasedBuyer
from apps.api.app.catalog.catalog_service import get_catalog


class BuyerAgent:
    def __init__(self):
        self.fallback = RuleBasedBuyer()
        self.gemini = None
        self.last_provider = "unknown"
        self.last_error = None

        try:
            self.gemini = GeminiBuyer()
        except Exception:
            self.gemini = None

    def select_product(
        self,
        buyer_request: BuyerRequest,
        catalog: dict | None = None,
    ) -> BuyerSelection:

        if catalog is None:
            catalog = get_catalog()

        if self.gemini is not None:
            try:
                result = self.gemini.select_product(
                    buyer_request,
                    catalog,
                )

                self.last_provider = "gemini"
                self.last_error = None

                return result

            except Exception as error:
                self.last_provider = "rule_fallback"
                self.last_error = str(error)

        else:
            self.last_provider = "rule_fallback"
            self.last_error = "Gemini provider is unavailable."

        return self.fallback.select_product(
            buyer_request,
            catalog,
        )