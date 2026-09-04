from pydantic import BaseModel


class AuditEvent(BaseModel):
    transaction_id: str
    event_type: str
    timestamp: str
    details: dict