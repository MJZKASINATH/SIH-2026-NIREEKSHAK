from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, State, Constituency, MP, ProjectRisk
from schemas import ProjectListResponse, ProjectBase
from services.engine import engine

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=ProjectListResponse)
def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    constituency: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns registered projects from the database (the single source of truth).
    Filters across search query, state, constituency, category, risk, and status.
    """
    if not db:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    query = db.query(Project)\
        .outerjoin(State, Project.state_id == State.state_id)\
        .outerjoin(Constituency, Project.constituency_id == Constituency.constituency_id)\
        .outerjoin(ProjectRisk, Project.project_id == ProjectRisk.project_id)

    if search:
        s = search.strip()
        query = query.filter(
            (Project.work_description.ilike(f"%{s}%")) |
            (Project.project_title.ilike(f"%{s}%")) |
            (Project.project_id.ilike(f"%{s}%")) |
            (Project.city.ilike(f"%{s}%"))
        )
    if state and state != "All States":
        query = query.filter(State.state_name.ilike(f"%{state}%"))
    if constituency and constituency != "All Constituencies":
        query = query.filter(Constituency.constituency_name.ilike(f"%{constituency}%"))
    if category and category != "All Categories":
        query = query.filter(Project.category.ilike(f"%{category}%"))
    if status and status != "All Statuses":
        query = query.filter(Project.project_status.ilike(f"%{status}%"))

    if risk and risk != "All Risk Levels":
        r = risk.lower()
        if r in ["high", "critical", "red_flag", "red flag"]:
            query = query.filter(ProjectRisk.risk_score >= 60)
        elif r == "medium":
            query = query.filter(ProjectRisk.risk_score >= 30, ProjectRisk.risk_score < 60)
        elif r == "low":
            query = query.filter((ProjectRisk.risk_score < 30) | (ProjectRisk.risk_score == None))

    total_count = query.count()
    db_projects = query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for p in db_projects:
        year = 2026
        if p.recommendation_date:
            year = p.recommendation_date.year

        if p.risk_profile:
            r_score = p.risk_profile.risk_score
            r_level = p.risk_profile.risk_level
        else:
            r_score = 0
            r_level = "LOW"

        verified_cp = sum(1 for cp in p.checkpoints if cp.verification_status == "VERIFIED")

        items.append(ProjectBase(
            id=p.project_id,
            title=p.project_title or p.work_description or "MPLADS Project",
            description=p.work_description or "MPLADS Development Work",
            state=p.state.state_name if p.state else (p.city or "Unknown State"),
            constituency=p.constituency.constituency_name if p.constituency else (p.block or "General"),
            district=p.city or p.block or "District",
            category=p.category or "Infrastructure",
            amount=float(p.awarded_amount or p.allocated_amount or p.proposed_amount or 0.0),
            allocated_amount=float(p.allocated_amount or p.proposed_amount or 0.0),
            expenditure_amount=float(p.expenditure_amount or 0.0),
            awarded_amount=float(p.awarded_amount or 0.0),
            status=p.project_status or "SUBMITTED",
            lifecycle_status=p.project_status,
            approval_status=p.approval_status,
            year=year,
            recommendation_date=p.recommendation_date.isoformat() if p.recommendation_date else None,
            approval_date=p.approval_date.isoformat() if p.approval_date else None,
            risk=r_score,
            risk_level=r_level,
            latitude=p.latitude,
            longitude=p.longitude,
            contractor_name=p.tender.contractor_name if p.tender else None,
            checkpoints_verified=verified_cp,
            total_checkpoints=len(p.checkpoints)
        ))

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }

@router.get("/{project_id}", response_model=ProjectBase)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """Retrieves a single project from the database."""
    if not db:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
        
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if p:
        year = 2026
        if p.recommendation_date:
            year = p.recommendation_date.year

        r_score = p.risk_profile.risk_score if p.risk_profile else 0
        r_level = p.risk_profile.risk_level if p.risk_profile else "LOW"
        verified_cp = sum(1 for cp in p.checkpoints if cp.verification_status == "VERIFIED")

        return ProjectBase(
            id=p.project_id,
            title=p.project_title or p.work_description,
            description=p.work_description or "MPLADS Development Work",
            state=p.state.state_name if p.state else "Unknown State",
            constituency=p.constituency.constituency_name if p.constituency else "Unknown",
            district=p.city or p.block or "Unknown",
            category=p.category or "Infrastructure",
            amount=float(p.awarded_amount or p.allocated_amount or p.proposed_amount or 0.0),
            allocated_amount=float(p.allocated_amount or p.proposed_amount or 0.0),
            expenditure_amount=float(p.expenditure_amount or 0.0),
            awarded_amount=float(p.awarded_amount or 0.0),
            status=p.project_status or "SUBMITTED",
            lifecycle_status=p.project_status,
            approval_status=p.approval_status,
            year=year,
            recommendation_date=p.recommendation_date.isoformat() if p.recommendation_date else None,
            approval_date=p.approval_date.isoformat() if p.approval_date else None,
            risk=r_score,
            risk_level=r_level,
            latitude=p.latitude,
            longitude=p.longitude,
            contractor_name=p.tender.contractor_name if p.tender else None,
            checkpoints_verified=verified_cp,
            total_checkpoints=len(p.checkpoints)
        )

    raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found in database")