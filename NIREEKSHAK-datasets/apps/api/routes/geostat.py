from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Dict, Any
from database import get_db
from models import Project, ProjectRisk, ContractorRiskProfile, State, Constituency, GeoCheckpoint

router = APIRouter(prefix="/geostat", tags=["Geostatistical Intelligence"])

@router.get("/projects")
def get_geostat_projects(
    search: Optional[str] = Query(None, description="Search by title, project ID, or contractor"),
    state: Optional[str] = Query(None, description="Filter by State name"),
    risk_level: Optional[str] = Query(None, description="Filter by Risk Level (LOW, MEDIUM, HIGH, RED_FLAG)"),
    contractor: Optional[str] = Query(None, description="Filter by Contractor name"),
    status_filter: Optional[str] = Query(None, description="Filter by Project Status"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns actual project geospatial coordinates, risk assessments, financial metrics,
    and checkpoint verification counts from the database for the Leaflet Geostatistical Map.
    Zero mock/placeholder data. If 15 projects have coordinates in the DB, exactly 15 are returned.
    """
    if not db:
        return {"total": 0, "projects": [], "filters": {"states": [], "contractors": [], "categories": []}}

    # Base query: only projects that have valid latitude and longitude coordinates
    query = db.query(Project).filter(
        Project.latitude.isnot(None),
        Project.longitude.isnot(None)
    )

    # Optional status filter
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Project.project_status == status_filter.upper())

    projects = query.all()

    items = []
    all_states = set()
    all_contractors = set()
    all_categories = set()

    for p in projects:
        state_name = p.state.state_name if p.state else (p.city or "Unknown")
        constituency_name = p.constituency.constituency_name if p.constituency else "General"
        district_name = p.city or constituency_name
        category_name = p.category or "General"
        
        contractor_name = p.tender.contractor_name if p.tender else "Not Assigned"
        contractor_suspicious = (
            p.tender.contractor_entity.suspicious_projects
            if (p.tender and p.tender.contractor_entity) else 0
        )

        score = p.risk_profile.risk_score if p.risk_profile else 0
        level = p.risk_profile.risk_level if p.risk_profile else "LOW"
        is_red = score >= 80 or p.project_status == "RED_FLAGGED"

        cost_val = float(p.awarded_amount or p.allocated_amount or p.proposed_amount or 0.0)
        exp_val = float(p.expenditure_amount or 0.0)

        # Calculate latest physical progress
        phys_pct = 0.0
        if p.progress_updates:
            phys_pct = float(p.progress_updates[-1].physical_progress_percent)

        # Financial utilization percentage
        fin_util = round((exp_val / cost_val * 100), 1) if cost_val > 0 else 0.0

        # Checkpoints counts
        total_ck = len(p.checkpoints) if p.checkpoints else 0
        verified_ck = len([c for c in p.checkpoints if getattr(c, 'verification_status', None) == 'VERIFIED' or getattr(c, 'is_verified', False)]) if p.checkpoints else 0

        # Collect distinct filters metadata before filtering
        if state_name and state_name != "Unknown":
            all_states.add(state_name)
        if contractor_name and contractor_name != "Not Assigned":
            all_contractors.add(contractor_name)
        if category_name:
            all_categories.add(category_name)

        # Apply state filter
        if state and state.upper() != "ALL":
            if state.lower() not in state_name.lower():
                continue

        # Apply risk level filter
        if risk_level and risk_level.upper() != "ALL":
            req_risk = risk_level.upper()
            if req_risk == "RED_FLAG" and not is_red and score < 80:
                continue
            elif req_risk == "HIGH" and (score < 60 or score >= 80):
                continue
            elif req_risk == "MEDIUM" and (score < 30 or score >= 60):
                continue
            elif req_risk == "LOW" and score >= 30:
                continue

        # Apply contractor filter
        if contractor and contractor.upper() != "ALL":
            if contractor.lower() not in contractor_name.lower():
                continue

        # Apply search query
        if search:
            q = search.lower().strip()
            title_match = (p.project_title or "").lower().find(q) >= 0
            id_match = (p.project_id or "").lower().find(q) >= 0
            vendor_match = contractor_name.lower().find(q) >= 0
            constituency_match = constituency_name.lower().find(q) >= 0
            if not (title_match or id_match or vendor_match or constituency_match):
                continue

        items.append({
            "projectId": p.project_id,
            "project_id": p.project_id,
            "title": p.project_title or p.work_description or "MPLADS Project",
            "latitude": float(p.latitude),
            "longitude": float(p.longitude),
            "riskScore": score,
            "risk_score": score,
            "riskLevel": level,
            "risk_level": level,
            "cost": cost_val,
            "awarded_amount": cost_val,
            "expenditure": exp_val,
            "expenditure_amount": exp_val,
            "physicalProgress": phys_pct,
            "physical_progress": phys_pct,
            "financialUtilization": fin_util,
            "financial_utilization": fin_util,
            "status": p.project_status or "SUBMITTED",
            "project_status": p.project_status or "SUBMITTED",
            "state": state_name,
            "district": district_name,
            "constituency": constituency_name,
            "contractor": contractor_name,
            "contractorSuspicious": contractor_suspicious,
            "contractor_suspicious": contractor_suspicious,
            "isRedFlag": is_red,
            "is_red_flag": is_red,
            "category": category_name,
            "checkpointsVerified": verified_ck,
            "checkpoints_verified": verified_ck,
            "totalCheckpoints": total_ck,
            "total_checkpoints": total_ck
        })

    return {
        "total": len(items),
        "projects": items,
        "markers": items,
        "filters": {
            "states": sorted(list(all_states)),
            "contractors": sorted(list(all_contractors)),
            "categories": sorted(list(all_categories))
        }
    }
