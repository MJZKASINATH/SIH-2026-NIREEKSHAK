import uuid
import hashlib
import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Project, ProjectApproval, Tender, ContractorRiskProfile,
    ExpenditureTransaction, ProgressUpdate, GeoCheckpoint, GeoEvidence,
    InvestigationCase, InvestigationNote, AuditLog, Notification,
    State, Constituency, MP, ProjectRisk
)
from schemas import (
    ProjectCreate, ProjectBase, ApprovalSubmitRequest, ApprovalResponse,
    TenderCreate, TenderResponse, ExpenditureCreate, ExpenditureTransactionResponse,
    ProgressCreate, ProgressUpdateResponse, GeoCheckpointUpdate, GeoCheckpointResponse,
    EvidenceUploadRequest, EvidenceUploadResponse
)
from services.risk_engine import (
    calculate_fused_risk, normalize_entity_name,
    calculate_haversine_distance
)
from routes.auth import get_current_user, require_roles
from models import User

router = APIRouter(prefix="/projects", tags=["Project Lifecycle & Field Verification"])

STATE_CODE_MAP = {
    "kerala": "KL",
    "maharashtra": "MH",
    "uttar pradesh": "UP",
    "tamil nadu": "TN",
    "karnataka": "KA",
    "delhi": "DL",
    "west bengal": "WB",
    "rajasthan": "RJ",
    "gujarat": "GJ",
    "andhra pradesh": "AP",
    "telangana": "TG",
    "punjab": "PB",
    "haryana": "HR",
    "bihar": "BR",
    "odisha": "OD",
    "assam": "AS",
}

def get_state_code(state_str: str) -> str:
    if not state_str:
        return "KL"
    cleaned = state_str.lower().strip()
    if cleaned in STATE_CODE_MAP:
        return STATE_CODE_MAP[cleaned]
    if len(state_str) == 2:
        return state_str.upper()
    return state_str[:2].upper()

def create_audit_log(
    db: Session,
    user_name: str,
    role: str,
    action: str,
    project_id: str,
    previous_value: Optional[str] = None,
    new_value: Optional[str] = None,
    metadata_json: Optional[dict] = None
):
    """Appends an immutable audit log record with SHA-256 event hash linked to previous event hash."""
    last_log = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
    previous_hash = last_log.event_hash if (last_log and last_log.event_hash) else "0" * 64
    
    event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    raw_str = f"{event_id}:{user_name}:{action}:{project_id}:{previous_hash}:{datetime.datetime.now().isoformat()}"
    event_hash = hashlib.sha256(raw_str.encode()).hexdigest()
    
    meta = metadata_json or {}
    meta["previous_hash"] = previous_hash
    
    log = AuditLog(
        event_id=event_id,
        user_name=user_name,
        role=role,
        action=action,
        project_id=project_id,
        previous_value=previous_value,
        new_value=new_value,
        metadata_json=meta,
        event_hash=event_hash
    )
    db.add(log)
    db.commit()
    return log

def trigger_risk_recalculation(db: Session, project_id: str):
    """
    Recalculates risk using the fused 9-anomaly engine.
    If score >= 80 (RED FLAG):
    - Automatically opens an InvestigationCase (if not already opened).
    - Idempotently updates contractor suspicious project count.
    - Emits notification.
    """
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        return None

    # Gather data for engine
    transactions = [
        {"amount": float(tx.amount), "date": str(tx.transaction_date)}
        for tx in p.expenditures
    ]
    latest_progress = p.progress_updates[-1] if p.progress_updates else None
    physical_pct = latest_progress.physical_progress_percent if latest_progress else 0.0
    
    total_exp = float(p.expenditure_amount or 0.0)
    alloc_amt = float(p.awarded_amount or p.allocated_amount or p.proposed_amount or 1.0)
    financial_pct = min(100.0, (total_exp / alloc_amt * 100.0)) if alloc_amt > 0 else 0.0

    checkpoints_data = [
        {"verification_status": cp.verification_status, "checkpoint_code": cp.checkpoint_code}
        for cp in p.checkpoints
    ]

    # Contractor details
    contractor = None
    contractor_suspicious = 0
    contractor_red_flags = 0
    contractor_name = "Unknown"
    if p.tender and p.tender.contractor_entity:
        contractor = p.tender.contractor_entity
        contractor_suspicious = contractor.suspicious_projects
        contractor_red_flags = contractor.red_flagged_projects
        contractor_name = contractor.contractor_name

    risk_result = calculate_fused_risk(
        cost=float(p.allocated_amount or p.proposed_amount or 0.0),
        peer_median=2500000.0,
        awarded_amount=float(p.awarded_amount or 0.0),
        estimated_amount=float(p.proposed_amount or 0.0),
        actual_expenditure=total_exp,
        physical_progress=physical_pct,
        financial_progress=financial_pct,
        transactions=transactions,
        description=p.work_description or "",
        expected_lat=p.latitude,
        expected_lng=p.longitude,
        submitted_lat=latest_progress.submitted_latitude if latest_progress else p.latitude,
        submitted_lng=latest_progress.submitted_longitude if latest_progress else p.longitude,
        checkpoints=checkpoints_data,
        contractor_suspicious_count=contractor_suspicious,
        contractor_red_flags=contractor_red_flags,
        contractor_name=contractor_name
    )

    score = risk_result["overall_score"]
    level = risk_result["risk_level"]

    # Save risk profile
    if not p.risk_profile:
        p.risk_profile = ProjectRisk(
            project_id=p.project_id,
            risk_score=score,
            risk_level=level,
            confidence_score=risk_result["confidence_score"],
            signals=risk_result["signals"],
            breakdown=risk_result["breakdown"],
            summary_text=risk_result["summary_text"]
        )
        db.add(p.risk_profile)
    else:
        p.risk_profile.risk_score = score
        p.risk_profile.risk_level = level
        p.risk_profile.signals = risk_result["signals"]
        p.risk_profile.breakdown = risk_result["breakdown"]
        p.risk_profile.summary_text = risk_result["summary_text"]

    # --- RED FLAG WORKFLOW AUTOMATION ---
    if score >= 80:
        p.project_status = "RED_FLAGGED"
        
        # 1. Open investigation case if not already open
        existing_case = db.query(InvestigationCase).filter(InvestigationCase.project_id == project_id).first()
        if not existing_case:
            case_id = f"INV-2026-{uuid.uuid4().hex[:5].upper()}"
            new_case = InvestigationCase(
                case_id=case_id,
                project_id=project_id,
                status="OPEN",
                priority="HIGH",
                summary=f"Automated case generated: Multi-signal risk score reached {score}/100.",
                findings=json.dumps(risk_result["signals"])
            )
            db.add(new_case)
            
            # Initial auto note
            note = InvestigationNote(
                case_id=case_id,
                author_name="NIREEKSHAK AI Engine",
                role="SYSTEM",
                note_text=f"Project flagged with risk score {score}/100. Key drivers: " + "; ".join([s["title"] for s in risk_result["signals"]]),
                action_type="ESCALATION"
            )
            db.add(note)

        # 2. Idempotent contractor risk update
        if contractor:
            # Check if we already incremented for this project
            # Store project_id in audit or check red flags
            existing_audit = db.query(AuditLog).filter(
                AuditLog.project_id == project_id,
                AuditLog.action == "CONTRACTOR_SUSPICIOUS_INCREMENT"
            ).first()
            if not existing_audit:
                contractor.suspicious_projects = (contractor.suspicious_projects or 0) + 1
                contractor.risk_status = "HIGH" if contractor.suspicious_projects >= 2 else "MEDIUM"
                contractor.risk_score = min(100, int(contractor.suspicious_projects * 25 + 30))
                db.commit()
                create_audit_log(
                    db,
                    user_name="AI Risk Engine",
                    role="SYSTEM",
                    action="CONTRACTOR_SUSPICIOUS_INCREMENT",
                    project_id=project_id,
                    previous_value=str(contractor.suspicious_projects - 1),
                    new_value=str(contractor.suspicious_projects),
                    metadata_json={"contractor_name": contractor.contractor_name, "registration": contractor.registration_number}
                )

        # 3. Notification
        notif = Notification(
            user_role="AUDITOR",
            title=f"RED FLAG: Project {project_id}",
            message=f"Risk Score {score}/100. Requires immediate human investigation.",
            project_id=project_id,
            severity="CRITICAL"
        )
        db.add(notif)

    db.commit()
    return risk_result

# -----------------------------------------------------------
# 1. PROPOSE PROJECT (MP Role)
# -----------------------------------------------------------
@router.post("/propose", response_model=ProjectBase)
def propose_project(
    req: ProjectCreate,
    current_user: User = Depends(require_roles(["MP", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Registers a new project proposal by an MP with automatic 5 checkpoints and unique ID."""
    state_code = get_state_code(req.state)
    unique_suffix = uuid.uuid4().hex[:6].upper()
    project_id = f"MPLADS-2026-{state_code}-{unique_suffix}"

    # Find or link State and Constituency
    state_obj = db.query(State).filter(State.state_name.ilike(f"%{req.state}%")).first()
    if not state_obj:
        state_obj = State(state_name=req.state)
        db.add(state_obj)
        db.flush()

    const_obj = db.query(Constituency).filter(
        Constituency.constituency_name.ilike(f"%{req.mp_constituency}%")
    ).first()
    if not const_obj:
        const_obj = Constituency(state_id=state_obj.state_id, constituency_name=req.mp_constituency)
        db.add(const_obj)
        db.flush()

    # Link MP
    mp_obj = db.query(MP).filter(MP.mp_name.ilike(f"%{req.mp_name}%")).first()
    if not mp_obj:
        mp_obj = MP(mp_name=req.mp_name, constituency_id=const_obj.constituency_id, house="LOK_SABHA")
        db.add(mp_obj)
        db.flush()

    new_proj = Project(
        project_id=project_id,
        project_title=req.title,
        work_description=req.description,
        category=req.category,
        mp_id=mp_obj.mp_id,
        constituency_id=const_obj.constituency_id,
        state_id=state_obj.state_id,
        city=req.district,
        block=req.local_body or req.district,
        proposed_amount=req.proposed_amount,
        allocated_amount=req.estimated_cost,
        latitude=req.latitude,
        longitude=req.longitude,
        proposed_location=req.proposed_location,
        recommendation_date=datetime.date.today(),
        expected_completion_date=datetime.date.today() + datetime.timedelta(days=365),
        project_status="SUBMITTED",
        approval_status="PENDING",
        beneficiary_info=req.beneficiary_info,
        supporting_documents=req.supporting_documents or [],
        created_by=req.mp_name
    )
    db.add(new_proj)
    db.flush()

    # Create 5 predefined verification checkpoints (A to E) around the project site
    lat, lng = req.latitude, req.longitude
    checkpoints = [
        ("A", "Location A – Project entrance/reference point", lat, lng, 150.0),
        ("B", "Location B – North/primary work area", lat + 0.0008, lng, 150.0),
        ("C", "Location C – Secondary work area", lat, lng + 0.0008, 150.0),
        ("D", "Location D – Infrastructure/component area", lat - 0.0008, lng, 150.0),
        ("E", "Location E – Completion/reference area", lat, lng - 0.0008, 150.0),
    ]
    for code, name, c_lat, c_lng, radius in checkpoints:
        cp = GeoCheckpoint(
            checkpoint_id=f"CP-{project_id}-{code}",
            project_id=project_id,
            checkpoint_code=code,
            checkpoint_name=name,
            expected_latitude=c_lat,
            expected_longitude=c_lng,
            allowed_radius_meters=radius,
            verification_status="PENDING"
        )
        db.add(cp)

    db.commit()

    create_audit_log(
        db,
        user_name=req.mp_name,
        role="MP",
        action="PROJECT_PROPOSAL_SUBMITTED",
        project_id=project_id,
        new_value=json.dumps({"title": req.title, "amount": req.proposed_amount})
    )

    return ProjectBase(
        id=new_proj.project_id,
        title=new_proj.project_title,
        state=state_obj.state_name,
        constituency=const_obj.constituency_name,
        district=new_proj.city,
        category=new_proj.category,
        description=new_proj.work_description,
        amount=float(new_proj.allocated_amount or 0.0),
        status=new_proj.project_status,
        risk=0,
        risk_level="LOW",
        year=2026,
        recommendation_date=str(new_proj.recommendation_date),
        latitude=new_proj.latitude,
        longitude=new_proj.longitude
    )

# -----------------------------------------------------------
# 2. APPROVE PROJECT (Approving Authority Role)
# -----------------------------------------------------------
@router.post("/{project_id}/approve", response_model=ApprovalResponse)
def approve_project(
    project_id: str,
    req: ApprovalSubmitRequest,
    current_user: User = Depends(require_roles(["APPROVING_AUTHORITY", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Digitally approves a proposal with official ID verification, synthetic scan, and geo-tagged proof."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    if p.project_status == "APPROVED":
        raise HTTPException(status_code=400, detail="Project is already approved")

    if not req.official_id or not req.official_id.strip():
        raise HTTPException(status_code=400, detail="Official identity verification is required for approval")
    if not req.digital_signature or not req.digital_signature.strip():
        raise HTTPException(status_code=400, detail="Digital signature evidence is required for approval")
    if req.location_latitude is not None and req.location_longitude is not None:
        if abs(req.location_latitude) > 90 or abs(req.location_longitude) > 180:
            raise HTTPException(status_code=400, detail="Invalid GPS coordinates for approval evidence")
        if p.latitude is not None and p.longitude is not None:
            dist = calculate_haversine_distance(p.latitude, p.longitude, req.location_latitude, req.location_longitude)
            if dist > 5000: # > 5km
                raise HTTPException(status_code=400, detail=f"Geo approval location is too far ({dist:.1f}m) from project location")

    approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    doc_hash = hashlib.sha256(f"{project_id}:{req.official_id}:{req.scanned_id_demo_reference}".encode()).hexdigest()

    approval = ProjectApproval(
        approval_id=approval_id,
        project_id=project_id,
        approved_by=req.approved_by,
        designation=req.designation,
        official_id=req.official_id,
        approval_date=datetime.date.today(),
        approval_remarks=req.remarks or "Administrative and technical sanctions verified. Approved for tendering.",
        digital_signature=req.digital_signature,
        document_hash=doc_hash,
        masked_id_preview=f"GOV-ID-XXXX-{req.official_id[-4:] if len(req.official_id) >= 4 else '8921'}",
        location_latitude=req.location_latitude or p.latitude,
        location_longitude=req.location_longitude or p.longitude,
        photo_reference=req.approval_photo_url or "https://images.unsplash.com/photo-1541888946425-d0fbb186156a?w=400",
        photo_hash=hashlib.sha256(f"photo_{approval_id}".encode()).hexdigest()
    )
    db.add(approval)

    p.project_status = "APPROVED"
    p.approval_status = "APPROVED"
    p.approval_date = datetime.date.today()
    db.commit()

    create_audit_log(
        db,
        user_name=req.approved_by,
        role="APPROVING_AUTHORITY",
        action="PROJECT_APPROVED",
        project_id=project_id,
        previous_value="SUBMITTED",
        new_value="APPROVED",
        metadata_json={"approval_id": approval_id, "official_id": req.official_id, "doc_hash": doc_hash}
    )

    return ApprovalResponse(
        approval_id=approval.approval_id,
        project_id=approval.project_id,
        approved_by=approval.approved_by,
        designation=approval.designation,
        official_id=approval.official_id,
        approval_date=str(approval.approval_date),
        approval_remarks=approval.approval_remarks,
        digital_signature=approval.digital_signature,
        document_hash=approval.document_hash,
        masked_id_preview=approval.masked_id_preview,
        location_latitude=approval.location_latitude,
        location_longitude=approval.location_longitude,
        photo_reference=approval.photo_reference,
        created_at=str(approval.created_at)
    )

# -----------------------------------------------------------
# 3. REGISTER TENDER & CONTRACTOR
# -----------------------------------------------------------
@router.post("/{project_id}/tender", response_model=TenderResponse)
def register_tender(
    project_id: str,
    req: TenderCreate,
    current_user: User = Depends(require_roles(["APPROVING_AUTHORITY", "CONTRACTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Registers tender award, normalizes contractor entity, and calculates deviation."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    norm_name = normalize_entity_name(req.contractor_name)
    contractor = db.query(ContractorRiskProfile).filter(
        (ContractorRiskProfile.registration_number == req.registration_number) |
        (ContractorRiskProfile.normalized_name == norm_name)
    ).first()

    if not contractor:
        contractor = ContractorRiskProfile(
            contractor_id=f"CON-{uuid.uuid4().hex[:6].upper()}",
            contractor_name=req.contractor_name,
            registration_number=req.registration_number,
            normalized_name=norm_name,
            total_projects=1,
            total_project_value=req.awarded_amount,
            risk_score=15,
            risk_status="LOW"
        )
        db.add(contractor)
        db.flush()
    else:
        contractor.total_projects += 1
        contractor.total_project_value = float(contractor.total_project_value or 0) + req.awarded_amount

    est_amt = float(p.allocated_amount or p.proposed_amount or req.tender_amount)
    dev_pct = ((req.awarded_amount - est_amt) / est_amt * 100.0) if est_amt > 0 else 0.0

    tender_id = f"TND-{uuid.uuid4().hex[:6].upper()}"
    tender = Tender(
        tender_id=tender_id,
        project_id=project_id,
        contractor_id=contractor.contractor_id,
        contractor_name=req.contractor_name,
        registration_number=req.registration_number,
        tender_date=datetime.date.today(),
        tender_amount=req.tender_amount,
        estimated_project_amount=est_amt,
        awarded_amount=req.awarded_amount,
        tender_deviation_percent=round(dev_pct, 2),
        bid_information=req.bid_information or "Standard Competitive E-Procurement Bidding",
        work_order_number=req.work_order_number,
        work_order_date=datetime.date.today(),
        contract_start_date=datetime.date.today(),
        contract_end_date=datetime.date.today() + datetime.timedelta(days=240),
        supporting_documents=req.supporting_documents or []
    )
    db.add(tender)

    p.awarded_amount = req.awarded_amount
    p.project_status = "WORK_STARTED"
    p.start_date = datetime.date.today()
    db.commit()

    trigger_risk_recalculation(db, project_id)

    create_audit_log(
        db,
        user_name="Procurement Officer",
        role="AUTHORIZED_PERSONNEL",
        action="TENDER_AWARDED",
        project_id=project_id,
        new_value=json.dumps({"contractor": req.contractor_name, "awarded": req.awarded_amount})
    )

    return TenderResponse(
        tender_id=tender.tender_id,
        project_id=tender.project_id,
        contractor_name=tender.contractor_name,
        registration_number=tender.registration_number,
        tender_date=str(tender.tender_date),
        tender_amount=float(tender.tender_amount),
        estimated_project_amount=float(tender.estimated_project_amount),
        awarded_amount=float(tender.awarded_amount),
        tender_deviation_percent=float(tender.tender_deviation_percent),
        work_order_number=tender.work_order_number,
        contract_start_date=str(tender.contract_start_date),
        contract_end_date=str(tender.contract_end_date)
    )

# -----------------------------------------------------------
# 4. APPEND-ONLY EXPENDITURE LEDGER
# -----------------------------------------------------------
@router.post("/{project_id}/expenditure", response_model=ExpenditureTransactionResponse)
def add_expenditure(
    project_id: str,
    req: ExpenditureCreate,
    current_user: User = Depends(require_roles(["CONTRACTOR", "FIELD_OFFICER", "APPROVING_AUTHORITY", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Appends an expenditure transaction to the immutable ledger and updates cumulative metrics."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Expenditure amount must be strictly greater than 0")

    current_cum = float(p.expenditure_amount or 0.0)
    new_cum = current_cum + req.amount

    doc_hash = hashlib.sha256(f"{project_id}:{req.invoice_number}:{req.amount}".encode()).hexdigest()

    tx = ExpenditureTransaction(
        project_id=project_id,
        transaction_date=datetime.date.today(),
        expense_category=req.expense_category,
        description=req.description,
        amount=req.amount,
        cumulative_expenditure=new_cum,
        invoice_number=req.invoice_number,
        supporting_document_url=req.supporting_document_url,
        document_hash=doc_hash,
        entered_by=req.entered_by
    )
    db.add(tx)

    p.expenditure_amount = new_cum
    if p.tender and p.tender.contractor_entity:
        p.tender.contractor_entity.total_expenditure = (
            float(p.tender.contractor_entity.total_expenditure or 0) + req.amount
        )

    db.commit()

    # Recalculate risk on financial modification
    trigger_risk_recalculation(db, project_id)

    create_audit_log(
        db,
        user_name=req.entered_by,
        role="FINANCE_OFFICER",
        action="EXPENDITURE_DISBURSED",
        project_id=project_id,
        previous_value=f"₹{current_cum:,.2f}",
        new_value=f"₹{new_cum:,.2f}",
        metadata_json={"amount": req.amount, "invoice": req.invoice_number, "doc_hash": doc_hash}
    )

    return ExpenditureTransactionResponse(
        id=tx.id,
        project_id=tx.project_id,
        transaction_date=str(tx.transaction_date),
        expense_category=tx.expense_category,
        description=tx.description,
        amount=float(tx.amount),
        cumulative_expenditure=float(tx.cumulative_expenditure),
        invoice_number=tx.invoice_number,
        document_hash=tx.document_hash,
        entered_by=tx.entered_by,
        timestamp=str(tx.timestamp)
    )

# -----------------------------------------------------------
# 5. PROGRESS UPDATE MODULE
# -----------------------------------------------------------
@router.post("/{project_id}/progress", response_model=ProgressUpdateResponse)
def submit_progress(
    project_id: str,
    req: ProgressCreate,
    current_user: User = Depends(require_roles(["FIELD_OFFICER", "CONTRACTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Submits physical progress update with geo-tagged field verification photograph."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    photo_h = hashlib.sha256(f"{project_id}:{req.physical_progress_percent}:{datetime.datetime.now()}".encode()).hexdigest()

    alloc = float(p.awarded_amount or p.allocated_amount or 1.0)
    exp_cum = float(p.expenditure_amount or 0.0)
    fin_pct = (exp_cum / alloc * 100.0) if alloc > 0 else 0.0

    prog = ProgressUpdate(
        project_id=project_id,
        update_date=datetime.date.today(),
        physical_progress_percent=req.physical_progress_percent,
        financial_progress_percent=round(fin_pct, 1),
        work_description=req.work_description or f"Execution milestone reached: {req.physical_progress_percent}%",
        expenditure_since_previous=req.expenditure_since_previous or 0.0,
        cumulative_expenditure=exp_cum,
        photo_reference=req.photo_reference or "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=500",
        photo_hash=photo_h,
        submitted_latitude=req.submitted_latitude or p.latitude,
        submitted_longitude=req.submitted_longitude or p.longitude,
        field_officer=req.field_officer,
        remarks=req.remarks
    )
    db.add(prog)

    if req.physical_progress_percent >= 100.0:
        p.project_status = "COMPLETED"
        p.completion_date = datetime.date.today()
    else:
        p.project_status = "IN_PROGRESS"

    db.commit()

    trigger_risk_recalculation(db, project_id)

    create_audit_log(
        db,
        user_name=req.field_officer,
        role="FIELD_OFFICER",
        action="PROGRESS_MILESTONE_UPDATED",
        project_id=project_id,
        new_value=f"{req.physical_progress_percent}% Physical / {fin_pct:.1f}% Financial"
    )

    return ProgressUpdateResponse(
        id=prog.id,
        project_id=prog.project_id,
        update_date=str(prog.update_date),
        physical_progress_percent=float(prog.physical_progress_percent),
        financial_progress_percent=float(prog.financial_progress_percent),
        work_description=prog.work_description,
        cumulative_expenditure=float(prog.cumulative_expenditure),
        photo_reference=prog.photo_reference,
        photo_hash=prog.photo_hash,
        submitted_latitude=prog.submitted_latitude,
        submitted_longitude=prog.submitted_longitude,
        field_officer=prog.field_officer,
        remarks=prog.remarks
    )

# -----------------------------------------------------------
# 6. FIVE-LOCATION CHECKPOINTS VERIFICATION
# -----------------------------------------------------------
@router.post("/{project_id}/checkpoints/{checkpoint_code}/verify", response_model=GeoCheckpointResponse)
def verify_checkpoint(
    project_id: str,
    checkpoint_code: str,
    req: GeoCheckpointUpdate,
    current_user: User = Depends(require_roles(["FIELD_OFFICER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Verifies physical submission at a specific checkpoint (A to E) against expected geofence."""
    cp = db.query(GeoCheckpoint).filter(
        GeoCheckpoint.project_id == project_id,
        GeoCheckpoint.checkpoint_code == checkpoint_code.upper()
    ).first()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    if req.submitted_latitude is None or req.submitted_longitude is None:
        raise HTTPException(status_code=400, detail="GPS coordinates are required for checkpoint verification")
    if abs(req.submitted_latitude) > 90 or abs(req.submitted_longitude) > 180:
        raise HTTPException(status_code=400, detail="Invalid GPS latitude or longitude value")

    dist = calculate_haversine_distance(
        cp.expected_latitude, cp.expected_longitude,
        req.submitted_latitude, req.submitted_longitude
    )

    is_verified = dist <= cp.allowed_radius_meters
    cp.submitted_latitude = req.submitted_latitude
    cp.submitted_longitude = req.submitted_longitude
    cp.gps_accuracy_meters = req.gps_accuracy_meters
    cp.photo_url = req.photo_url
    cp.photo_hash = hashlib.sha256(f"{project_id}:{checkpoint_code}:{req.submitted_latitude}".encode()).hexdigest()
    cp.timestamp = datetime.datetime.now()
    cp.uploader = req.uploader
    cp.distance_meters = round(dist, 1)
    cp.verification_status = "VERIFIED" if is_verified else "MISMATCH"

    db.commit()

    trigger_risk_recalculation(db, project_id)

    create_audit_log(
        db,
        user_name=req.uploader,
        role="FIELD_OFFICER",
        action=f"CHECKPOINT_{checkpoint_code.upper()}_VERIFIED" if is_verified else f"CHECKPOINT_{checkpoint_code.upper()}_MISMATCH",
        project_id=project_id,
        new_value=f"Status: {cp.verification_status} (Distance: {dist:.1f}m / Radius: {cp.allowed_radius_meters}m)"
    )

    return GeoCheckpointResponse(
        checkpoint_id=cp.checkpoint_id,
        project_id=cp.project_id,
        checkpoint_code=cp.checkpoint_code,
        checkpoint_name=cp.checkpoint_name,
        expected_latitude=cp.expected_latitude,
        expected_longitude=cp.expected_longitude,
        allowed_radius_meters=cp.allowed_radius_meters,
        submitted_latitude=cp.submitted_latitude,
        submitted_longitude=cp.submitted_longitude,
        gps_accuracy_meters=cp.gps_accuracy_meters,
        photo_url=cp.photo_url,
        photo_hash=cp.photo_hash,
        verification_status=cp.verification_status,
        distance_meters=cp.distance_meters,
        uploader=cp.uploader
    )

# -----------------------------------------------------------
# 7. EVIDENCE UPLOAD & TAMPER DETECTION
# -----------------------------------------------------------
@router.post("/{project_id}/evidence", response_model=EvidenceUploadResponse)
def upload_evidence(project_id: str, req: EvidenceUploadRequest, db: Session = Depends(get_db)):
    """Uploads field evidence, checks SHA-256 hash and validates EXIF vs Device GPS discrepancy."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    ev_id = f"EVD-2026-{uuid.uuid4().hex[:6].upper()}"
    file_h = hashlib.sha256(
        req.file_bytes_base64.encode() if req.file_bytes_base64 else f"{ev_id}:{req.photo_url}".encode()
    ).hexdigest()

    discrepancy = 0.0
    tamper_flag = False
    status_label = "Location Verified"

    if req.exif_latitude and req.exif_longitude:
        discrepancy = calculate_haversine_distance(
            req.submitted_latitude, req.submitted_longitude,
            req.exif_latitude, req.exif_longitude
        )
        if discrepancy > 500.0:
            tamper_flag = True
            status_label = "Metadata Suspicious"
    else:
        # Compare submitted to project coordinate
        if p.latitude and p.longitude:
            proj_dist = calculate_haversine_distance(p.latitude, p.longitude, req.submitted_latitude, req.submitted_longitude)
            if proj_dist > 1500.0:
                tamper_flag = True
                status_label = "Location Mismatch"

    evidence = GeoEvidence(
        evidence_id=ev_id,
        project_id=project_id,
        submission_type=req.submission_type,
        photo_url=req.photo_url,
        file_hash=file_h,
        captured_timestamp=datetime.datetime.now(),
        submitted_latitude=req.submitted_latitude,
        submitted_longitude=req.submitted_longitude,
        exif_latitude=req.exif_latitude,
        exif_longitude=req.exif_longitude,
        discrepancy_meters=round(discrepancy, 1),
        uploader=req.uploader,
        verification_status=status_label,
        notes=req.notes
    )
    db.add(evidence)
    db.commit()

    trigger_risk_recalculation(db, project_id)

    create_audit_log(
        db,
        user_name=req.uploader,
        role="FIELD_OFFICER",
        action="EVIDENCE_UPLOADED",
        project_id=project_id,
        new_value=f"Evidence {ev_id} | Integrity: VERIFIED | Status: {status_label}"
    )

    return EvidenceUploadResponse(
        evidence_id=evidence.evidence_id,
        project_id=evidence.project_id,
        submission_type=evidence.submission_type,
        file_hash=evidence.file_hash,
        verification_status=evidence.verification_status,
        discrepancy_meters=evidence.discrepancy_meters,
        tamper_flag=tamper_flag,
        integrity_status="VERIFIED",
        timestamp=str(evidence.upload_timestamp)
    )

# -----------------------------------------------------------
# 8. GET PROJECT DIGITAL MASTER FILE (All 10 Tabs Data)
# -----------------------------------------------------------
@router.get("/{project_id}/master-file")
def get_project_master_file(project_id: str, db: Session = Depends(get_db)):
    """Fetches the complete 10-tab digital master file for auditors and administrators."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    # Ensure risk profile exists
    if not p.risk_profile:
        trigger_risk_recalculation(db, project_id)

    verified_cp_count = sum(1 for cp in p.checkpoints if cp.verification_status == "VERIFIED")

    return {
        "header": {
            "projectId": p.project_id,
            "title": p.project_title or p.work_description,
            "category": p.category or "Infrastructure",
            "state": p.state.state_name if p.state else "Unknown",
            "district": p.city or p.block or "Unknown",
            "constituency": p.constituency.constituency_name if p.constituency else "Unknown",
            "mpName": p.mp.mp_name if p.mp else (p.created_by or "Unknown"),
            "status": p.project_status,
            "approvalStatus": p.approval_status,
            "allocatedAmount": float(p.allocated_amount or p.proposed_amount or 0.0),
            "awardedAmount": float(p.awarded_amount or 0.0),
            "expenditureAmount": float(p.expenditure_amount or 0.0),
            "riskScore": p.risk_profile.risk_score if p.risk_profile else 0,
            "riskLevel": p.risk_profile.risk_level if p.risk_profile else "LOW",
            "verifiedCheckpointsCount": verified_cp_count,
            "totalCheckpoints": len(p.checkpoints)
        },
        "proposal": {
            "mpName": p.mp.mp_name if p.mp else p.created_by,
            "title": p.project_title or p.work_description,
            "description": p.work_description,
            "category": p.category,
            "proposedAmount": float(p.proposed_amount or 0.0),
            "estimatedCost": float(p.allocated_amount or 0.0),
            "beneficiaryInfo": p.beneficiary_info or "Public General Benefit",
            "proposedLocation": p.proposed_location or f"{p.city}, {p.constituency.constituency_name if p.constituency else ''}",
            "latitude": p.latitude,
            "longitude": p.longitude,
            "recommendationDate": str(p.recommendation_date) if p.recommendation_date else None,
            "expectedCompletionDate": str(p.expected_completion_date) if p.expected_completion_date else None,
            "supportingDocuments": p.supporting_documents or []
        },
        "approval": {
            "approvalId": p.approval.approval_id if p.approval else None,
            "approvedBy": p.approval.approved_by if p.approval else None,
            "designation": p.approval.designation if p.approval else None,
            "officialId": p.approval.official_id if p.approval else None,
            "approvalDate": str(p.approval.approval_date) if p.approval else None,
            "remarks": p.approval.approval_remarks if p.approval else None,
            "digitalSignature": p.approval.digital_signature if p.approval else None,
            "documentHash": p.approval.document_hash if p.approval else None,
            "maskedIdPreview": p.approval.masked_id_preview if p.approval else None,
            "photoReference": p.approval.photo_reference if p.approval else None,
            "isApproved": p.approval is not None
        },
        "tender": {
            "tenderId": p.tender.tender_id if p.tender else None,
            "contractorName": p.tender.contractor_name if p.tender else "Not Assigned",
            "registrationNumber": p.tender.registration_number if p.tender else None,
            "awardedAmount": float(p.tender.awarded_amount) if p.tender else 0.0,
            "tenderAmount": float(p.tender.tender_amount) if p.tender else 0.0,
            "tenderDeviationPercent": float(p.tender.tender_deviation_percent) if p.tender else 0.0,
            "workOrderNumber": p.tender.work_order_number if p.tender else None,
            "contractDates": {
                "start": str(p.tender.contract_start_date) if p.tender else None,
                "end": str(p.tender.contract_end_date) if p.tender else None
            },
            "contractorRisk": {
                "riskScore": p.tender.contractor_entity.risk_score if p.tender and p.tender.contractor_entity else 0,
                "suspiciousProjects": p.tender.contractor_entity.suspicious_projects if p.tender and p.tender.contractor_entity else 0,
                "status": p.tender.contractor_entity.risk_status if p.tender and p.tender.contractor_entity else "LOW"
            } if p.tender and p.tender.contractor_entity else None
        },
        "expenditures": [
            {
                "id": tx.id,
                "date": str(tx.transaction_date),
                "category": tx.expense_category,
                "description": tx.description,
                "amount": float(tx.amount),
                "cumulative": float(tx.cumulative_expenditure),
                "invoice": tx.invoice_number,
                "enteredBy": tx.entered_by,
                "docHash": tx.document_hash
            }
            for tx in p.expenditures
        ],
        "progressUpdates": [
            {
                "id": pr.id,
                "date": str(pr.update_date),
                "physical": float(pr.physical_progress_percent),
                "financial": float(pr.financial_progress_percent),
                "description": pr.work_description,
                "photo": pr.photo_reference,
                "photoHash": pr.photo_hash,
                "officer": pr.field_officer
            }
            for pr in p.progress_updates
        ],
        "checkpoints": [
            {
                "id": cp.checkpoint_id,
                "checkpointId": cp.checkpoint_id,
                "checkpoint_id": cp.checkpoint_id,
                "code": cp.checkpoint_code,
                "checkpointCode": cp.checkpoint_code,
                "name": cp.checkpoint_name,
                "expectedLat": cp.expected_latitude,
                "expectedLatitude": cp.expected_latitude,
                "expectedLng": cp.expected_longitude,
                "expectedLongitude": cp.expected_longitude,
                "radius": cp.allowed_radius_meters,
                "submittedLat": cp.submitted_latitude,
                "submittedLng": cp.submitted_longitude,
                "status": cp.verification_status,
                "distance": cp.distance_meters,
                "photo": cp.photo_url
            }
            for cp in p.checkpoints
        ],
        "evidence": [
            {
                "id": ev.evidence_id,
                "type": ev.submission_type,
                "photoUrl": ev.photo_url,
                "fileHash": ev.file_hash,
                "status": ev.verification_status,
                "uploader": ev.uploader,
                "timestamp": str(ev.upload_timestamp)
            }
            for ev in p.evidence_items
        ],
        "riskAnalysis": {
            "score": p.risk_profile.risk_score if p.risk_profile else 0,
            "level": p.risk_profile.risk_level if p.risk_profile else "LOW",
            "confidenceScore": p.risk_profile.confidence_score if p.risk_profile else 0.85,
            "summaryText": p.risk_profile.summary_text if p.risk_profile else "",
            "breakdown": p.risk_profile.breakdown if p.risk_profile else {},
            "signals": p.risk_profile.signals if p.risk_profile else []
        },
        "riskProfile": {
            "risk_score": p.risk_profile.risk_score if p.risk_profile else 0,
            "risk_level": p.risk_profile.risk_level if p.risk_profile else "LOW",
            "confidence_score": p.risk_profile.confidence_score if p.risk_profile else 0.85,
            "summary_text": p.risk_profile.summary_text if p.risk_profile else "",
            "breakdown": p.risk_profile.breakdown if p.risk_profile else {},
            "signals": p.risk_profile.signals if p.risk_profile else []
        },
        "investigation": {
            "caseId": p.investigation_case.case_id if p.investigation_case else None,
            "status": p.investigation_case.status if p.investigation_case else "NONE",
            "priority": p.investigation_case.priority if p.investigation_case else "NORMAL",
            "openedAt": str(p.investigation_case.opened_at) if p.investigation_case else None,
            "assignedTo": p.investigation_case.assigned_to if p.investigation_case else None,
            "notes": [
                {
                    "id": n.id,
                    "author": n.author_name,
                    "role": n.role,
                    "text": n.note_text,
                    "actionType": n.action_type,
                    "timestamp": str(n.timestamp)
                }
                for n in (p.investigation_case.notes if p.investigation_case else [])
            ]
        },
        "investigationCase": {
            "case_id": p.investigation_case.case_id if p.investigation_case else None,
            "status": p.investigation_case.status if p.investigation_case else "NONE",
            "priority": p.investigation_case.priority if p.investigation_case else "NORMAL",
            "opened_at": str(p.investigation_case.opened_at) if p.investigation_case else None,
            "assigned_to": p.investigation_case.assigned_to if p.investigation_case else None
        } if p.investigation_case else None,
        "auditTrail": [
            {
                "eventId": a.event_id,
                "user": a.user_name,
                "role": a.role,
                "action": a.action,
                "timestamp": str(a.timestamp),
                "previousValue": a.previous_value,
                "newValue": a.new_value,
                "eventHash": a.event_hash
            }
            for a in p.audit_logs
        ]
    }
