import json
from datetime import datetime, timezone
from uuid import uuid4

from apps.api.app.audit.audit_models import AuditEvent
from apps.api.app.audit.db_models import AuditEventRecord
from apps.api.app.core.database import SessionLocal


class AuditService:
    def start_transaction(self) -> str:
        return f"txn_{uuid4().hex[:12]}"

    def record(
        self,
        transaction_id: str,
        event_type: str,
        details: dict | None = None,
    ) -> AuditEvent:
        timestamp = datetime.now(timezone.utc)

        db = SessionLocal()

        try:
            record = AuditEventRecord(
                transaction_id=transaction_id,
                event_type=event_type,
                timestamp=timestamp,
                details=json.dumps(details or {}),
            )

            db.add(record)
            db.commit()

            return AuditEvent(
                transaction_id=transaction_id,
                event_type=event_type,
                timestamp=timestamp.isoformat(),
                details=details or {},
            )

        finally:
            db.close()

    def get_events(
        self,
        transaction_id: str,
    ) -> list[AuditEvent]:
        db = SessionLocal()

        try:
            records = (
                db.query(AuditEventRecord)
                .filter(
                    AuditEventRecord.transaction_id
                    == transaction_id
                )
                .order_by(AuditEventRecord.id.asc())
                .all()
            )

            return [
                AuditEvent(
                    transaction_id=record.transaction_id,
                    event_type=record.event_type,
                    timestamp=record.timestamp.replace(
                        tzinfo=timezone.utc
                    ).isoformat(),
                    details=json.loads(record.details),
                )
                for record in records
            ]

        finally:
            db.close()