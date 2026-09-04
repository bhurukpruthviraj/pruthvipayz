from abc import ABC, abstractmethod

from apps.api.app.agents.buyer_schemas import (
    BuyerRequest,
    BuyerSelection,
)


class AIBuyer(ABC):
    @abstractmethod
    def select_product(
        self,
        buyer_request: BuyerRequest,
        catalog: dict,
    ) -> BuyerSelection:
        raise NotImplementedError