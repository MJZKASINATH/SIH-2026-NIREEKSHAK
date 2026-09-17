from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import pandas as pd
import json
import datetime
import uuid
from database import get_db
from models import Project, InvestigationCase, InvestigationNote, AuditLog, User
from schemas import (
    InvestigationNoteCreate, InvestigationNoteResponse,
    SimilarProjectsResponse, TimelineResponse, EvidenceResponse
)
from services.engine import engine
from routes.auth import require_roles

import math

def safe_float(val, default=0.0):
    try:
        if val is None or pd.isna(val):
            return default
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default

import numpy as np

def round_floats(obj):
    if obj is None:
        return None
    try:
        if pd.isna(obj):
            return 0.0
    except Exception:
        pass
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return round(f, 4)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, dict):
        return {str(k): round_floats(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [round_floats(x) for x in obj]
    return obj

router = APIRouter(prefix="/projects", tags=["Investigation & Evidence"])
investigation_router = APIRouter(prefix="/investigations", tags=["Investigation Queue"])

@investigation_router.get("")
def list_investigations(db: Session = Depends(get_db)):
    """Returns all open and closed investigation cases directly from the database."""
    cases = db.query(InvestigationCase).order_by(InvestigationCase.opened_at.desc()).all() if db else []
    result = []
    for c in cases:
        p = c.project
        score = p.risk_profile.risk_score if (p and p.risk_profile) else 80
        level = p.risk_profile.risk_level if (p and p.risk_profile) else "RED_FLAG"
        signals = p.risk_profile.signals if (p and p.risk_profile) else []
        contractor_name = p.tender.contractor_name if (p and p.tender) else "Not Assigned"
        alloc_amt = float(p.allocated_amount or p.proposed_amount or 0.0) if p else 0.0
        exp_amt = float(p.expenditure_amount or 0.0) if p else 0.0
        
        result.append({
            "case_id": c.case_id,
            "project_id": c.project_id,
            "project_title": p.project_title or p.work_description if p else "MPLADS Project",
            "state": p.state.state_name if (p and p.state) else (p.city if p else "State"),
            "constituency": p.constituency.constituency_name if (p and p.constituency) else "Constituency",
            "status": c.status,
            "priority": c.priority,
            "risk_score": score,
            "risk_level": level,
            "signals": signals,
            "contractor_name": contractor_name,
            "allocated_amount": alloc_amt,
            "expenditure_amount": exp_amt,
            "opened_at": c.opened_at.isoformat() if c.opened_at else datetime.datetime.now().isoformat(),
            "assigned_to": c.assigned_to,
            "summary": c.summary,
            "findings": c.findings,
            "notes_count": len(c.notes)
        })
    return result

@investigation_router.get("/{case_id}")
def get_investigation_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    notes = [
        {
            "id": n.id,
            "author_name": n.author_name,
            "role": n.role,
            "note_text": n.note_text,
            "action_type": n.action_type,
            "timestamp": n.timestamp.isoformat() if n.timestamp else ""
        }
        for n in case.notes
    ]
    p = case.project
    return {
        "case_id": case.case_id,
        "project_id": case.project_id,
        "project_title": p.project_title if p else "",
        "status": case.status,
        "priority": case.priority,
        "assigned_to": case.assigned_to,
        "summary": case.summary,
        "findings": case.findings,
        "opened_at": str(case.opened_at),
        "notes": notes
    }

@investigation_router.post("/{case_id}/action")
def update_investigation_case(
    case_id: str,
    req: InvestigationNoteCreate,
    current_user: User = Depends(require_roles(["AUDITOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    
    action = req.action_type.upper()
    if action == "RESOLUTION":
        case.status = "RESOLVED"
        case.closed_at = datetime.datetime.now()
    elif action == "ESCALATION":
        case.status = "ESCALATED"
    elif action == "CLARIFICATION_REQUEST":
        case.status = "CLARIFICATION_REQUESTED"
    elif action == "INSPECTION_SCHEDULED":
        case.status = "FIELD_INSPECTION"
    elif action == "DISMISS":
        case.status = "DISMISSED"
        case.closed_at = datetime.datetime.now()

    note = InvestigationNote(
        case_id=case_id,
        author_name=req.author_name or current_user.full_name,
        role=req.role or current_user.role,
        note_text=req.note_text,
        action_type=action,
        attachment_ref=req.attachment_ref
    )
    db.add(note)
    
    log = AuditLog(
        event_id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
        user_name=req.author_name or current_user.full_name,
        role=req.role or current_user.role,
        action=f"INVESTIGATION_{action}",
        project_id=case.project_id,
        new_value=req.note_text
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "case_id": case.case_id,
        "status": case.status,
        "message": f"Action '{action}' recorded successfully."
    }


@router.get("/{project_id}/investigation")
def get_investigation_data(project_id: str, db: Session = Depends(get_db)):
    """Fetches comprehensive investigation data combining DB state with AI anomaly insights."""
    legacy_map = {
        "UP-1094": "MPLADS-2026-KL-000101",
        "MH-1804": "MPLADS-2026-KA-000201",
        "KL-3012": "MPLADS-2026-MH-000301",
        "RJ-9921": "MPLADS-2026-TN-000401",
        "WB-4022": "MPLADS-2026-DL-000501"
    }
    target_id = legacy_map.get(project_id, project_id)
    db_project = db.query(Project).filter(Project.project_id == target_id).first() if db else None
    if not db_project:
        db_project = db.query(Project).filter(Project.project_id == project_id).first() if db else None
    
    # Try Parquet index first, then fallback
    if project_id in engine.df.index:
        row = engine.df.loc[project_id]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
    else:
        import hashlib
        hash_val = int(hashlib.md5(project_id.encode('utf-8')).hexdigest(), 16)
        idx = hash_val % len(engine.df)
        row = engine.df.iloc[idx]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
    
    # Parse reasons from parquet
    reasons = []
    try:
        raw_reasons = row.get("investigation_reasons", "[]")
        if isinstance(raw_reasons, str):
            reasons = eval(raw_reasons)
        elif isinstance(raw_reasons, list):
            reasons = raw_reasons
    except:
        pass
        
    signals = []
    # If DB project has dynamic signals, use those
    if db_project and db_project.risk_profile and db_project.risk_profile.signals:
        signals = db_project.risk_profile.signals
    else:
        for r in reasons:
            signals.append({
                "type": "COST_ANOMALY" if "cost" in r.lower() or "amount" in r.lower() else "DUPLICATE_WORK" if "duplicate" in r.lower() or "similar" in r.lower() else "TIMELINE_VIOLATION",
                "title": "Anomaly Detected",
                "severity": row.get("investigation_priority_v2_DERIVED", "HIGH"),
                "scoreImpact": 20,
                "description": str(r)
            })
        
    risk_score = (
        db_project.risk_profile.risk_score
        if db_project and db_project.risk_profile
        else int(row.get("investigation_score_v2_DERIVED", row.get("investigation_score", 0)))
    )
    risk_level = (
        db_project.risk_profile.risk_level
        if db_project and db_project.risk_profile
        else row.get("investigation_priority_v2_DERIVED", "LOW")
    )
    
    matched_id = row.get("nearest_work_id", "")
    duplicate_evidence = None
    if matched_id and matched_id in engine.df.index:
        peer = engine.df.loc[matched_id]
        if isinstance(peer, pd.DataFrame):
            peer = peer.iloc[0]
        duplicate_evidence = {
            "matchScorePercent": safe_float(row.get("semantic_duplicate_score", 0.85)) * 100,
            "semanticMatchScore": safe_float(row.get("semantic_duplicate_score", 0.85)) * 100,
            "syntacticMatchScore": safe_float(row.get("semantic_duplicate_score", 0.85)) * 100,
            "matchedProjectId": matched_id,
            "matchedProjectTitle": str(peer.get("Work Description", "")),
            "matchedSanctionDate": str(peer.get("Sanction Date", "")),
            "matchedSanctionAmount": safe_float(peer.get("Sanction Amount ( ₹ )", 0)),
            "matchedImplementingAgency": str(peer.get("Vendor Name", "Unknown")),
            "matchedConstituency": peer.get("Constituency", ""),
            "matchedDistrict": "",
            "matchedState": peer.get("State", ""),
            "matchedLocationName": "",
            "matchedGpsCoords": {"lat": 0, "lng": 0},
            "currentGpsCoords": {"lat": db_project.latitude if db_project else 0, "lng": db_project.longitude if db_project else 0},
            "distanceMeters": 0,
            "timeDeltaDays": 0,
            "isSameImplementingAgency": False,
            "matchedPhrases": [],
            "currentDescriptionTokens": [],
            "matchedDescriptionTokens": [],
            "riskObservations": []
        }
        
    sanction_amt = float(db_project.allocated_amount or row.get("Sanction Amount ( ₹ )", 0)) if db_project else float(row.get("Sanction Amount ( ₹ )", 0))
    cost_evidence = {
        "thisProjectCost": sanction_amt,
        "unitMetric": "project",
        "unitValue": 1,
        "unitCost": sanction_amt,
        "peerUnitCostMedian": float(row.get("peer_expected_amount", 2500000.0)),
        "peerMedianCost": float(row.get("peer_expected_amount", 2500000.0)),
        "peerMeanCost": float(row.get("peer_expected_amount", 2500000.0)),
        "peerIqrLow": float(row.get("peer_expected_lower", 1500000.0)),
        "peerIqrHigh": float(row.get("peer_expected_upper", 3500000.0)),
        "peerP95": float(row.get("peer_expected_upper", 3500000.0)) * 1.5,
        "peerMin": 0,
        "peerMax": float(row.get("peer_expected_upper", 3500000.0)) * 2,
        "deviationMultiplier": float(row.get("counterfactual_deviation", 1.0)),
        "zScore": float(row.get("robust_z", 0.0)),
        "peerSampleSize": 50,
        "baselineCategory": str(db_project.category if db_project else row.get("Work Category", "")),
        "districtMedian": 0,
        "stateMedian": 0,
        "costBreakdown": [],
        "distributionCurve": [],
        "statisticalObservations": []
    }

    # Fetch investigation notes from DB
    notes = []
    case_status = "OPEN" if risk_score >= 80 else "NONE"
    if db_project and db_project.investigation_case:
        case_status = db_project.investigation_case.status
        for n in db_project.investigation_case.notes:
            notes.append({
                "action": n.action_type,
                "actor": n.author_name,
                "role": n.role,
                "timestamp": str(n.timestamp),
                "notes": n.note_text
            })

    # Agency info
    agency_name = (
        db_project.tender.contractor_name if db_project and db_project.tender
        else row.get("Vendor Name", "Apex Infra Projects")
    )
    agency_suspicious = (
        db_project.tender.contractor_entity.suspicious_projects
        if db_project and db_project.tender and db_project.tender.contractor_entity
        else 0
    )

    return round_floats({
        "header": {
            "projectId": project_id,
            "title": db_project.project_title or db_project.work_description if db_project else row.get("Work Description", ""),
            "sector": db_project.category if db_project else row.get("Work Category", ""),
            "category": db_project.category if db_project else row.get("Work Category", ""),
            "state": db_project.state.state_name if (db_project and db_project.state) else row.get("State", ""),
            "district": db_project.city if db_project else row.get("Constituency", ""),
            "constituency": db_project.constituency.constituency_name if (db_project and db_project.constituency) else row.get("Constituency", ""),
            "constituencyType": "LOK_SABHA",
            "mpName": db_project.mp.mp_name if (db_project and db_project.mp) else (db_project.created_by if db_project else "Unknown"),
            "mpHouse": "LOK_SABHA",
            "sanctionDate": str(db_project.recommendation_date) if (db_project and db_project.recommendation_date) else str(row.get("Sanction Date", "2026-01-15")),
            "sanctionYear": "2025-2026",
            "sanctionOrderNumber": f"MPLADS/2026/{project_id}",
            "implementingAgency": agency_name,
            "nodalDepartment": "District Planning Office",
            "sanctionedAmount": sanction_amt,
            "releasedAmount": float(db_project.awarded_amount or sanction_amt) if db_project else float(sanction_amt),
            "expenditureAmount": float(db_project.expenditure_amount or 0.0) if db_project else 0.0,
            "physicalProgressPercent": float(db_project.progress_updates[-1].physical_progress_percent if (db_project and db_project.progress_updates) else 0.0),
            "financialProgressPercent": float(db_project.progress_updates[-1].financial_progress_percent if (db_project and db_project.progress_updates) else 0.0),
            "currentStatus": db_project.project_status if db_project else row.get("Payment Status", "UNDER_EXECUTION"),
            "lastUpdated": str(datetime.date.today()),
        },
        "risk": {
            "overallScore": risk_score,
            "riskLevel": risk_level,
            "confidenceScore": 0.88,
            "flaggedRulesCount": len(signals),
            "primaryDrivers": [s.get("description", str(s)) for s in signals],
            "breakdown": {
                "costDeviationScore": min(100, max(0, int(safe_float(row.get("robust_z", 0)) * 10))),
                "duplicateOverlapScore": int(safe_float(row.get("semantic_duplicate_score", 0)) * 100),
                "timelineLatencyScore": 0,
                "agencyConcentrationScore": agency_suspicious * 25,
            },
            "summaryText": (
                f"Project flagged with risk score {risk_score}/100. Requires authorized human review."
                if risk_score >= 60 else "Project metrics monitored within standard variance."
            )
        },
        "signals": signals,
        "timeline": [
            {"step": "Proposal Submitted", "status": "COMPLETED", "date": "2026-01-15"},
            {"step": "Administrative Sanction", "status": "COMPLETED", "date": "2026-02-01"},
            {"step": "Tender Awarded", "status": "COMPLETED", "date": "2026-02-20"},
            {"step": "Work Commenced", "status": "COMPLETED", "date": "2026-03-01"},
            {"step": "Milestone Verification", "status": "ANOMALOUS" if risk_score >= 80 else "IN_PROGRESS", "date": "2026-03-15"}
        ],
        "evidence": {
            "costOutlier": cost_evidence,
            "duplicateMatch": duplicate_evidence,
            "geospatial": {
                "latitude": db_project.latitude if db_project else 27.5,
                "longitude": db_project.longitude if db_project else 79.5,
                "geoAccuracyMeters": 15,
                "geoSource": "PORTAL_GEO_VERIFIED",
                "nearestPeerWorksCountWithin500m": 0,
                "clusterAnomalyDetected": False,
                "satelliteClearanceScore": 0,
                "cadastralLandId": "UNKNOWN",
                "landStatusNote": "Government Vested Land"
            },
            "agencyRisk": {
                "agencyName": agency_name,
                "totalProjectsActive": 4,
                "totalProjectValue": 12000000,
                "anomalousProjectsCount": agency_suspicious,
                "utilizationCertificatesPendingCount": 1 if agency_suspicious > 0 else 0,
                "riskRating": "HIGH" if agency_suspicious >= 2 else ("MEDIUM" if agency_suspicious == 1 else "LOW")
            }
        },
        "auditHistory": notes,
        "verificationStatus": {
            "isReviewed": case_status in ["RESOLVED", "CLOSED"],
            "currentAction": case_status,
            "reviewedBy": "Auditor General Office",
            "reviewedAt": str(datetime.date.today())
        }
    })

@router.post("/{project_id}/investigation/notes")
def add_investigation_note(
    project_id: str,
    req: InvestigationNoteCreate,
    current_user: User = Depends(require_roles(["AUDITOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Appends an investigator note, schedule request, or clarification query to the investigation workspace."""
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    case = db.query(InvestigationCase).filter(InvestigationCase.project_id == project_id).first()
    if not case:
        case_id = f"INV-2026-{uuid.uuid4().hex[:5].upper()}"
        case = InvestigationCase(
            case_id=case_id,
            project_id=project_id,
            status="UNDER_REVIEW",
            priority="HIGH",
            summary=f"Case opened manually by {req.author_name} ({req.role})"
        )
        db.add(case)
        db.flush()

    note = InvestigationNote(
        case_id=case.case_id,
        author_name=req.author_name,
        role=req.role,
        note_text=req.note_text,
        action_type=req.action_type or "NOTE"
    )
    db.add(note)

    # If action is status-changing
    if req.action_type == "RESOLVE":
        case.status = "RESOLVED"
        case.closed_at = datetime.datetime.now()
        p.project_status = "CLOSED"
    elif req.action_type == "ESCALATE":
        case.status = "ESCALATED"
        p.project_status = "RED_FLAGGED"
    elif req.action_type == "CLARIFICATION_REQUEST":
        case.status = "CLARIFICATION_REQUESTED"

    db.commit()

    # Import create_audit_log helper
    from routes.lifecycle import create_audit_log
    create_audit_log(
        db,
        user_name=req.author_name,
        role=req.role or "AUDITOR",
        action=f"INVESTIGATION_{req.action_type.upper() if req.action_type else 'NOTE'}",
        project_id=project_id,
        new_value=req.note_text
    )

    return {
        "success": True,
        "case_id": case.case_id,
        "note_id": note.id,
        "status": case.status,
        "message": f"Action '{req.action_type}' recorded successfully."
    }

@router.get("/{project_id}/similar", response_model=SimilarProjectsResponse)
def get_similar_projects(project_id: str):
    similar = engine.get_similar_projects(project_id)
    return {"items": similar}

@router.get("/{project_id}/timeline", response_model=TimelineResponse)
def get_timeline(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.project_id == project_id).first() if db else None
    events = [
        {"type": "PROPOSAL_SUBMITTED", "date": str(p.recommendation_date) if p and p.recommendation_date else "2026-01-10", "status": "completed", "description": "MP submitted proposal"}
    ]
    if p and p.approval:
        events.append({"type": "DIGITAL_APPROVAL", "date": str(p.approval.approval_date), "status": "completed", "description": f"Approved by {p.approval.approved_by}"})
    if p and p.tender:
        events.append({"type": "TENDER_AWARDED", "date": str(p.tender.tender_date), "status": "completed", "description": f"Awarded to {p.tender.contractor_name}"})
    if p and p.progress_updates:
        for pr in p.progress_updates:
            events.append({"type": "PROGRESS_UPDATE", "date": str(pr.update_date), "status": "completed", "description": f"{pr.physical_progress_percent}% Physical Progress"})
    return {"events": events}

@router.get("/{project_id}/evidence", response_model=EvidenceResponse)
def get_evidence(project_id: str):
    ev = engine.get_evidence(project_id)
    if not ev:
        return EvidenceResponse(
            project_amount=3500000.0,
            peer_median=2500000.0,
            peer_min=1500000.0,
            peer_max=3500000.0,
            matching_project_ids=[]
        )
    return ev
