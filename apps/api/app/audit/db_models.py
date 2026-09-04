from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    buyer_request: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    product_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    buyer_max_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="AUTHORIZED",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

class AgentDemandRecord(Base):
    __tablename__ = "agent_demand"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    max_budget: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ai_provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    selected_product_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    selected_product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    selected_product_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
        