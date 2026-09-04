from apps.api.app.audit.db_models import AgentDemandRecord
from apps.api.app.core.database import SessionLocal


class DemandService:
    def create(
        self,
        query: str,
        max_budget: int,
        ai_provider: str,
        selected_product_id: str | None = None,
        selected_product_name: str | None = None,
        selected_product_price: int | None = None,
        category: str | None = None,
        confidence: float | None = None,
    ) -> AgentDemandRecord:
        db = SessionLocal()

        try:
            demand = AgentDemandRecord(
                query=query,
                max_budget=max_budget,
                ai_provider=ai_provider,
                selected_product_id=selected_product_id,
                selected_product_name=selected_product_name,
                selected_product_price=selected_product_price,
                category=category,
                confidence=confidence,
            )

            db.add(demand)
            db.commit()
            db.refresh(demand)

            return demand

        finally:
            db.close()
