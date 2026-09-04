from sqlalchemy import func

from apps.api.app.audit.db_models import AgentDemandRecord
from apps.api.app.core.database import SessionLocal


class InsightsService:
    def summary(self):
        db = SessionLocal()

        try:
            total_requests = (
                db.query(func.count(AgentDemandRecord.id))
                .scalar()
                or 0
            )

            average_budget = (
                db.query(func.avg(AgentDemandRecord.max_budget))
                .scalar()
            )

            product_rows = (
                db.query(
                    AgentDemandRecord.selected_product_name,
                    AgentDemandRecord.selected_product_id,
                    AgentDemandRecord.selected_product_price,
                    func.count(AgentDemandRecord.id).label(
                        "request_count"
                    ),
                )
                .filter(
                    AgentDemandRecord.selected_product_id.isnot(None)
                )
                .group_by(
                    AgentDemandRecord.selected_product_id,
                    AgentDemandRecord.selected_product_name,
                    AgentDemandRecord.selected_product_price,
                )
                .order_by(
                    func.count(AgentDemandRecord.id).desc()
                )
                .all()
            )

            category_rows = (
                db.query(
                    AgentDemandRecord.category,
                    func.count(AgentDemandRecord.id).label(
                        "request_count"
                    ),
                )
                .filter(
                    AgentDemandRecord.category.isnot(None)
                )
                .group_by(
                    AgentDemandRecord.category
                )
                .order_by(
                    func.count(AgentDemandRecord.id).desc()
                )
                .all()
            )

            gap_rows = (
                db.query(
                    AgentDemandRecord.selected_product_id,
                    AgentDemandRecord.selected_product_name,
                    AgentDemandRecord.selected_product_price,
                    AgentDemandRecord.max_budget,
                    AgentDemandRecord.category,
                    func.count(AgentDemandRecord.id).label(
                        "request_count"
                    ),
                )
                .filter(
                    AgentDemandRecord.selected_product_id.isnot(None),
                    AgentDemandRecord.selected_product_price
                    > AgentDemandRecord.max_budget,
                )
                .group_by(
                    AgentDemandRecord.selected_product_id,
                    AgentDemandRecord.selected_product_name,
                    AgentDemandRecord.selected_product_price,
                    AgentDemandRecord.max_budget,
                    AgentDemandRecord.category,
                )
                .order_by(
                    func.count(AgentDemandRecord.id).desc()
                )
                .all()
            )

            return {
                "total_ai_buyer_requests": total_requests,
                "average_buyer_budget": (
                    round(float(average_budget), 2)
                    if average_budget is not None
                    else 0
                ),
                "top_products": [
                    {
                        "product_id": row.selected_product_id,
                        "product_name": row.selected_product_name,
                        "price": row.selected_product_price,
                        "request_count": row.request_count,
                    }
                    for row in product_rows
                ],
                "top_categories": [
                    {
                        "category": row.category,
                        "request_count": row.request_count,
                    }
                    for row in category_rows
                ],
                "budget_gap_opportunities": [
                    {
                        "product_id": row.selected_product_id,
                        "product_name": row.selected_product_name,
                        "category": row.category,
                        "current_price": row.selected_product_price,
                        "buyer_budget": row.max_budget,
                        "price_gap": (
                            row.selected_product_price
                            - row.max_budget
                        ),
                        "request_count": row.request_count,
                    }
                    for row in gap_rows
                ],
            }

        finally:
            db.close()
