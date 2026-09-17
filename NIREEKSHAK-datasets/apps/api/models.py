from sqlalchemy import (
    Column, String, Integer, ForeignKey, JSON, Date, Text,
    Numeric, TIMESTAMP, Float, Boolean, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime

class State(Base):
    __tablename__ = "states"
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(150), unique=True, nullable=False)

class Constituency(Base):
    __tablename__ = "constituencies"
    constituency_id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(Integer, ForeignKey("states.state_id"), nullable=False)
    constituency_name = Column(String(200), nullable=False)
    state = relationship("State")

class MP(Base):
    __tablename__ = "mps"
    mp_id = Column(Integer, primary_key=True, autoincrement=True)
    mp_name = Column(String(250), nullable=False)
    house = Column(String(50))
    constituency_id = Column(Integer, ForeignKey("constituencies.constituency_id"))
    constituency = relationship("Constituency")

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="MP") 
    # Roles: MP, APPROVING_AUTHORITY, CONTRACTOR, FIELD_OFFICER, AUDITOR, ADMIN
    full_name = Column(String(200), nullable=False)
    designation = Column(String(200), nullable=True)
    official_id = Column(String(100), nullable=True) # Official Badge / Employee ID
    constituency_id = Column(Integer, ForeignKey("constituencies.constituency_id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String(50), primary_key=True)
    project_title = Column(String(500), nullable=True)
    mp_id = Column(Integer, ForeignKey("mps.mp_id"), nullable=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.constituency_id"), nullable=True)
    state_id = Column(Integer, ForeignKey("states.state_id"), nullable=True)
    
    work_description = Column(Text, nullable=True)
    category = Column(String(250), nullable=True)
    city = Column(String(250), nullable=True)
    ward = Column(String(250), nullable=True)
    block = Column(String(250), nullable=True)
    village = Column(String(250), nullable=True)
    
    # Financial metrics
    proposed_amount = Column(Numeric(15, 2), default=0.0)
    allocated_amount = Column(Numeric(15, 2), default=0.0)
    expenditure_amount = Column(Numeric(15, 2), default=0.0)
    awarded_amount = Column(Numeric(15, 2), default=0.0)
    
    # Geographic location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    proposed_location = Column(String(300), nullable=True)
    
    # Dates
    recommendation_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    expected_completion_date = Column(Date, nullable=True)
    
    # Statuses
    # Lifecycle: DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, TENDERING, WORK_STARTED, IN_PROGRESS, INSPECTION_REQUIRED, COMPLETED, RED_FLAGGED, UNDER_INVESTIGATION, CLOSED
    project_status = Column(String(150), default="SUBMITTED")
    approval_status = Column(String(150), default="PENDING")
    
    beneficiary_info = Column(String(500), nullable=True)
    supporting_documents = Column(JSON, default=list)
    created_by = Column(String(100), default="MP")
    
    source_row_number = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # --- Relationships ---
    state = relationship("State")
    constituency = relationship("Constituency")
    mp = relationship("MP")
    risk_profile = relationship("ProjectRisk", back_populates="project", uselist=False, cascade="all, delete-orphan")
    approval = relationship("ProjectApproval", back_populates="project", uselist=False, cascade="all, delete-orphan")
    tender = relationship("Tender", back_populates="project", uselist=False, cascade="all, delete-orphan")
    expenditures = relationship("ExpenditureTransaction", back_populates="project", cascade="all, delete-orphan")
    progress_updates = relationship("ProgressUpdate", back_populates="project", cascade="all, delete-orphan")
    checkpoints = relationship("GeoCheckpoint", back_populates="project", cascade="all, delete-orphan")
    evidence_items = relationship("GeoEvidence", back_populates="project", cascade="all, delete-orphan")
    investigation_case = relationship("InvestigationCase", back_populates="project", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")

class ProjectRisk(Base):
    __tablename__ = "project_risks"
    project_id = Column(String(50), ForeignKey("projects.project_id"), primary_key=True)
    risk_score = Column(Integer, default=0)
    risk_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, RED_FLAG
    confidence_score = Column(Float, default=0.85)
    signals = Column(JSON, default=list)
    breakdown = Column(JSON, default=dict)
    summary_text = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="risk_profile")

class ProjectApproval(Base):
    __tablename__ = "project_approvals"
    approval_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("projects.project_id"), unique=True, nullable=False)
    approved_by = Column(String(200), nullable=False)
    designation = Column(String(200), nullable=False)
    official_id = Column(String(100), nullable=False)
    approval_date = Column(Date, default=datetime.date.today)
    approval_remarks = Column(Text, nullable=True)
    digital_signature = Column(String(255), nullable=False) # SHA signature / cryptographic token
    document_hash = Column(String(64), nullable=False) # SHA-256 of scanned ID proof
    masked_id_preview = Column(String(50), default="GOV-ID-XXXX-8921") # Redacted display ID
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    photo_reference = Column(String(500), nullable=True)
    photo_hash = Column(String(64), nullable=True)
    audit_event_id = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="approval")

class ContractorRiskProfile(Base):
    __tablename__ = "contractor_risk_profiles"
    contractor_id = Column(String(50), primary_key=True)
    contractor_name = Column(String(250), nullable=False)
    registration_number = Column(String(100), unique=True, nullable=False)
    normalized_name = Column(String(250), nullable=False)
    total_projects = Column(Integer, default=0)
    completed_projects = Column(Integer, default=0)
    delayed_projects = Column(Integer, default=0)
    suspicious_projects = Column(Integer, default=0)
    red_flagged_projects = Column(Integer, default=0)
    total_project_value = Column(Numeric(15, 2), default=0.0)
    total_expenditure = Column(Numeric(15, 2), default=0.0)
    risk_score = Column(Integer, default=0) # 0-100
    risk_status = Column(String(50), default="LOW")
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(300), nullable=True)
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenders = relationship("Tender", back_populates="contractor_entity")

class Tender(Base):
    __tablename__ = "tenders"
    tender_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("projects.project_id"), unique=True, nullable=False)
    contractor_id = Column(String(50), ForeignKey("contractor_risk_profiles.contractor_id"), nullable=True)
    contractor_name = Column(String(250), nullable=False)
    registration_number = Column(String(100), nullable=False)
    tender_date = Column(Date, default=datetime.date.today)
    tender_amount = Column(Numeric(15, 2), default=0.0)
    estimated_project_amount = Column(Numeric(15, 2), default=0.0)
    awarded_amount = Column(Numeric(15, 2), default=0.0)
    tender_deviation_percent = Column(Float, default=0.0)
    bid_information = Column(Text, nullable=True)
    work_order_number = Column(String(100), nullable=True)
    work_order_date = Column(Date, nullable=True)
    contract_start_date = Column(Date, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    supporting_documents = Column(JSON, default=list)
    created_at = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="tender")
    contractor_entity = relationship("ContractorRiskProfile", back_populates="tenders")

class ExpenditureTransaction(Base):
    __tablename__ = "expenditure_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False)
    transaction_date = Column(Date, default=datetime.date.today)
    expense_category = Column(String(150), nullable=False) # Material, Labor, Equipment, Inspection, Milestone
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    cumulative_expenditure = Column(Numeric(15, 2), nullable=False)
    invoice_number = Column(String(100), nullable=True)
    supporting_document_url = Column(String(500), nullable=True)
    document_hash = Column(String(64), nullable=True)
    entered_by = Column(String(100), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="expenditures")

class ProgressUpdate(Base):
    __tablename__ = "progress_updates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False)
    update_date = Column(Date, default=datetime.date.today)
    physical_progress_percent = Column(Float, nullable=False) # 0-100
    financial_progress_percent = Column(Float, nullable=False) # 0-100
    work_description = Column(Text, nullable=True)
    expenditure_since_previous = Column(Numeric(15, 2), default=0.0)
    cumulative_expenditure = Column(Numeric(15, 2), default=0.0)
    expected_progress_percent = Column(Float, default=0.0)
    photo_reference = Column(String(500), nullable=True)
    photo_hash = Column(String(64), nullable=True)
    submitted_latitude = Column(Float, nullable=True)
    submitted_longitude = Column(Float, nullable=True)
    field_officer = Column(String(200), nullable=False)
    remarks = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    project = relationship("Project", back_populates="progress_updates")

class GeoCheckpoint(Base):
    __tablename__ = "geo_checkpoints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(String(50), unique=True, nullable=False)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False)
    checkpoint_code = Column(String(10), nullable=False) # A, B, C, D, E
    checkpoint_name = Column(String(200), nullable=False) # e.g. Location A - Project Entrance
    expected_latitude = Column(Float, nullable=False)
    expected_longitude = Column(Float, nullable=False)
    allowed_radius_meters = Column(Float, default=150.0)
    submitted_latitude = Column(Float, nullable=True)
    submitted_longitude = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)
    photo_url = Column(String(500), nullable=True)
    photo_hash = Column(String(64), nullable=True)
    timestamp = Column(TIMESTAMP, nullable=True)
    uploader = Column(String(200), nullable=True)
    verification_status = Column(String(50), default="PENDING") # PENDING, VERIFIED, MISMATCH
    distance_meters = Column(Float, nullable=True)

    project = relationship("Project", back_populates="checkpoints")

class GeoEvidence(Base):
    __tablename__ = "geo_evidence"
    evidence_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False)
    submission_type = Column(String(50), nullable=False) # APPROVAL, SITE_BASELINE, PROGRESS, INSPECTION, COMPLETION, OTHER
    photo_url = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False) # SHA-256
    captured_timestamp = Column(TIMESTAMP, nullable=True)
    upload_timestamp = Column(TIMESTAMP, server_default=func.now())
    submitted_latitude = Column(Float, nullable=True)
    submitted_longitude = Column(Float, nullable=True)
    exif_latitude = Column(Float, nullable=True)
    exif_longitude = Column(Float, nullable=True)
    discrepancy_meters = Column(Float, default=0.0)
    uploader = Column(String(200), nullable=False)
    verification_status = Column(String(50), default="VERIFIED") # Location Verified, Location Mismatch, GPS Unavailable, Metadata Suspicious
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="evidence_items")

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"
    case_id = Column(String(50), primary_key=True) # INV-2026-00128
    project_id = Column(String(50), ForeignKey("projects.project_id"), unique=True, nullable=False)
    status = Column(String(50), default="OPEN") # OPEN, UNDER_REVIEW, CLARIFICATION_REQUESTED, FIELD_INSPECTION, RESOLVED, ESCALATED, CLOSED
    priority = Column(String(20), default="HIGH")
    opened_at = Column(TIMESTAMP, server_default=func.now())
    assigned_to = Column(String(200), default="Auditor General / Vigilance Officer")
    summary = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    closed_at = Column(TIMESTAMP, nullable=True)

    project = relationship("Project", back_populates="investigation_case")
    notes = relationship("InvestigationNote", back_populates="case", cascade="all, delete-orphan")

class InvestigationNote(Base):
    __tablename__ = "investigation_notes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("investigation_cases.case_id"), nullable=False)
    author_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False)
    note_text = Column(Text, nullable=False)
    action_type = Column(String(50), default="NOTE") # NOTE, CLARIFICATION_REQUEST, INSPECTION_SCHEDULED, RESOLUTION, ESCALATION
    attachment_ref = Column(String(500), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    case = relationship("InvestigationCase", back_populates="notes")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    event_id = Column(String(50), primary_key=True)
    user_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    ip_address = Column(String(50), default="127.0.0.1")
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    event_hash = Column(String(64), nullable=True) # Cryptographic hash of audit event

    project = relationship("Project", back_populates="audit_logs")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_role = Column(String(50), nullable=False)
    title = Column(String(250), nullable=False)
    message = Column(Text, nullable=False)
    project_id = Column(String(50), nullable=True)
    severity = Column(String(20), default="INFO") # INFO, WARNING, CRITICAL
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
