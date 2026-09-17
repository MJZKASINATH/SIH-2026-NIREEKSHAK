from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import AuditLog
from schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Digital Audit Trail"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    project_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieves immutable chronological audit records with cryptographic SHA-256 event hashes."""
    query = db.query(AuditLog)
    if project_id:
        query = query.filter(AuditLog.project_id == project_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if role:
        query = query.filter(AuditLog.role == role)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [
        AuditLogResponse(
            event_id=log.event_id,
            user_name=log.user_name,
            role=log.role,
            action=log.action,
            project_id=log.project_id,
            timestamp=str(log.timestamp),
            previous_value=log.previous_value,
            new_value=log.new_value,
            metadata_json=log.metadata_json or {},
            event_hash=log.event_hash
        )
        for log in logs
    ]
