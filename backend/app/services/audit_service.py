from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


def log(db: Session, action: str, *, actor: str = "system",
        entity: str | None = None, entity_id: int | None = None, detail: str = "") -> AuditLog:
    entry = AuditLog(actor=actor, action=action, entity=entity, entity_id=entity_id, detail=detail)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry