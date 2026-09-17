from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import ContractorRiskProfile, Tender, Project, State, Constituency
from schemas import ContractorResponse, ContractorDetailResponse, ProjectBase

router = APIRouter(prefix="/contractors", tags=["Contractor Entity Risk Database"])

@router.get("", response_model=List[ContractorResponse])
def get_contractors(
    search: Optional[str] = Query(None),
    risk_status: Optional[str] = Query(None),
    min_suspicious: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists registered contractor entities with their networked fraud risk profiles."""
    query = db.query(ContractorRiskProfile)
    if search:
        query = query.filter(
            (ContractorRiskProfile.contractor_name.ilike(f"%{search}%")) |
            (ContractorRiskProfile.registration_number.ilike(f"%{search}%"))
        )
    if risk_status:
        query = query.filter(ContractorRiskProfile.risk_status == risk_status)
    if min_suspicious is not None:
        query = query.filter(ContractorRiskProfile.suspicious_projects >= min_suspicious)

    entities = query.order_by(ContractorRiskProfile.suspicious_projects.desc(), ContractorRiskProfile.risk_score.desc()).all()

    return [
        ContractorResponse(
            contractor_id=c.contractor_id,
            contractor_name=c.contractor_name,
            registration_number=c.registration_number,
            total_projects=c.total_projects,
            completed_projects=c.completed_projects,
            delayed_projects=c.delayed_projects,
            suspicious_projects=c.suspicious_projects,
            red_flagged_projects=c.red_flagged_projects,
            total_project_value=float(c.total_project_value or 0.0),
            total_expenditure=float(c.total_expenditure or 0.0),
            risk_score=c.risk_score,
            risk_status=c.risk_status,
            last_updated=str(c.last_updated) if c.last_updated else None
        )
        for c in entities
    ]

@router.get("/{contractor_id}", response_model=ContractorDetailResponse)
def get_contractor_by_id(contractor_id: str, db: Session = Depends(get_db)):
    """Fetches full entity profile with all linked historical and active works."""
    c = db.query(ContractorRiskProfile).filter(ContractorRiskProfile.contractor_id == contractor_id).first()
    if not c:
        # Try matching by registration number
        c = db.query(ContractorRiskProfile).filter(ContractorRiskProfile.registration_number == contractor_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contractor entity not found")

    # Fetch associated projects via tenders
    tenders = db.query(Tender).filter(Tender.contractor_id == c.contractor_id).all()
    project_ids = [t.project_id for t in tenders]

    projects = db.query(Project).filter(Project.project_id.in_(project_ids)).all() if project_ids else []

    proj_list = []
    for p in projects:
        proj_list.append(ProjectBase(
            id=p.project_id,
            title=p.project_title or p.work_description,
            state=p.state.state_name if p.state else "Unknown",
            constituency=p.constituency.constituency_name if p.constituency else "Unknown",
            district=p.city or p.block or "Unknown",
            category=p.category or "Infrastructure",
            description=p.work_description or "Unknown",
            amount=float(p.awarded_amount or p.allocated_amount or 0.0),
            status=p.project_status or "Unknown",
            risk=p.risk_profile.risk_score if p.risk_profile else 0,
            risk_level=p.risk_profile.risk_level if p.risk_profile else "LOW",
            year=p.recommendation_date.year if p.recommendation_date else 2026,
            latitude=p.latitude,
            longitude=p.longitude
        ))

    return ContractorDetailResponse(
        contractor_id=c.contractor_id,
        contractor_name=c.contractor_name,
        registration_number=c.registration_number,
        total_projects=c.total_projects,
        completed_projects=c.completed_projects,
        delayed_projects=c.delayed_projects,
        suspicious_projects=c.suspicious_projects,
        red_flagged_projects=c.red_flagged_projects,
        total_project_value=float(c.total_project_value or 0.0),
        total_expenditure=float(c.total_expenditure or 0.0),
        risk_score=c.risk_score,
        risk_status=c.risk_status,
        last_updated=str(c.last_updated) if c.last_updated else None,
        associated_projects=proj_list
    )
