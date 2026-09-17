from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# --- AUTH SCHEMAS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    full_name: str
    designation: Optional[str] = None
    official_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- PROJECT SCHEMAS ---
class ProjectBase(BaseModel):
    id: str
    title: Optional[str] = None
    state: Optional[str] = None
    constituency: Optional[str] = None
    district: Optional[str] = None
    category: Optional[str] = None
    description: str = "Unknown"
    amount: float = 0.0
    allocated_amount: Optional[float] = 0.0
    expenditure_amount: Optional[float] = 0.0
    awarded_amount: Optional[float] = 0.0
    status: str = "Unknown"
    lifecycle_status: Optional[str] = "SUBMITTED"
    approval_status: Optional[str] = "PENDING"
    risk: int = 0
    risk_level: str = "LOW"
    year: int = 2026
    recommendation_date: Optional[str] = None
    approval_date: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contractor_name: Optional[str] = None
    checkpoints_verified: Optional[int] = 0
    total_checkpoints: Optional[int] = 5

class ProjectCreate(BaseModel):
    mp_name: str
    mp_constituency: str
    state: str
    district: str
    local_body: Optional[str] = None
    title: str
    description: str
    category: str
    proposed_amount: float
    estimated_cost: float
    beneficiary_info: Optional[str] = None
    proposed_location: str
    latitude: float
    longitude: float
    expected_completion_date: Optional[str] = None
    supporting_documents: Optional[List[Any]] = []

class ProjectListResponse(BaseModel):
    items: List[ProjectBase]
    total: int
    page: int
    page_size: int

# --- APPROVAL SCHEMAS ---
class ApprovalSubmitRequest(BaseModel):
    approved_by: str
    designation: str
    official_id: str
    approval_date: Optional[str] = None
    remarks: Optional[str] = None
    digital_signature: str
    scanned_id_demo_reference: Optional[str] = "SYNTHETIC_GOV_ID_BATCH_2026"
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    approval_photo_url: Optional[str] = None

class ApprovalResponse(BaseModel):
    approval_id: str
    project_id: str
    approved_by: str
    designation: str
    official_id: str
    approval_date: str
    approval_remarks: Optional[str] = None
    digital_signature: str
    document_hash: str
    masked_id_preview: str
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    photo_reference: Optional[str] = None
    created_at: str

# --- TENDER & CONTRACTOR SCHEMAS ---
class TenderCreate(BaseModel):
    contractor_name: str
    registration_number: str
    tender_amount: float
    awarded_amount: float
    bid_information: Optional[str] = None
    work_order_number: str
    work_order_date: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    supporting_documents: Optional[List[Any]] = []

class TenderResponse(BaseModel):
    tender_id: str
    project_id: str
    contractor_name: str
    registration_number: str
    tender_date: str
    tender_amount: float
    estimated_project_amount: float
    awarded_amount: float
    tender_deviation_percent: float
    work_order_number: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None

class ContractorResponse(BaseModel):
    contractor_id: str
    contractor_name: str
    registration_number: str
    total_projects: int
    completed_projects: int
    delayed_projects: int
    suspicious_projects: int
    red_flagged_projects: int
    total_project_value: float
    total_expenditure: float
    risk_score: int
    risk_status: str
    last_updated: Optional[str] = None

class ContractorDetailResponse(ContractorResponse):
    associated_projects: List[ProjectBase] = []

# --- EXPENDITURE SCHEMAS ---
class ExpenditureCreate(BaseModel):
    expense_category: Optional[str] = "Civil Works & Equipment"
    description: str
    amount: float
    invoice_number: Optional[str] = None
    supporting_document_url: Optional[str] = None
    entered_by: Optional[str] = "Authorized Billing Engineer"

class ExpenditureTransactionResponse(BaseModel):
    id: int
    project_id: str
    transaction_date: str
    expense_category: str
    description: str
    amount: float
    cumulative_expenditure: float
    invoice_number: Optional[str] = None
    document_hash: Optional[str] = None
    entered_by: str
    timestamp: str

# --- PROGRESS SCHEMAS ---
class ProgressCreate(BaseModel):
    physical_progress_percent: float
    financial_progress_percent: Optional[float] = None
    work_description: Optional[str] = None
    expenditure_since_previous: Optional[float] = 0.0
    photo_reference: Optional[str] = None
    submitted_latitude: Optional[float] = None
    submitted_longitude: Optional[float] = None
    field_officer: Optional[str] = "Authorized Field Inspector"
    remarks: Optional[str] = None

class ProgressUpdateResponse(BaseModel):
    id: int
    project_id: str
    update_date: str
    physical_progress_percent: float
    financial_progress_percent: float
    work_description: Optional[str] = None
    cumulative_expenditure: float
    photo_reference: Optional[str] = None
    photo_hash: Optional[str] = None
    submitted_latitude: Optional[float] = None
    submitted_longitude: Optional[float] = None
    field_officer: str
    remarks: Optional[str] = None

# --- GEO CHECKPOINT SCHEMAS ---
class GeoCheckpointUpdate(BaseModel):
    checkpoint_code: Optional[str] = None
    submitted_latitude: float
    submitted_longitude: float
    gps_accuracy_meters: Optional[float] = 10.0
    photo_url: str
    uploader: str

class GeoCheckpointResponse(BaseModel):
    checkpoint_id: str
    project_id: str
    checkpoint_code: str
    checkpoint_name: str
    expected_latitude: float
    expected_longitude: float
    allowed_radius_meters: float
    submitted_latitude: Optional[float] = None
    submitted_longitude: Optional[float] = None
    gps_accuracy_meters: Optional[float] = None
    photo_url: Optional[str] = None
    photo_hash: Optional[str] = None
    verification_status: str # VERIFIED, MISMATCH, PENDING
    distance_meters: Optional[float] = None
    uploader: Optional[str] = None

# --- EVIDENCE TAMPER CHECK SCHEMAS ---
class EvidenceUploadRequest(BaseModel):
    submission_type: str # APPROVAL, SITE_BASELINE, PROGRESS, INSPECTION, COMPLETION, OTHER
    photo_url: str
    file_bytes_base64: Optional[str] = None # Optional for hash calculation
    submitted_latitude: float
    submitted_longitude: float
    exif_latitude: Optional[float] = None
    exif_longitude: Optional[float] = None
    uploader: str
    notes: Optional[str] = None

class EvidenceUploadResponse(BaseModel):
    evidence_id: str
    project_id: str
    submission_type: str
    file_hash: str
    verification_status: str
    discrepancy_meters: float
    tamper_flag: bool
    integrity_status: str = "VERIFIED"
    timestamp: str

# --- RISK & INVESTIGATION SCHEMAS ---
class RiskSignal(BaseModel):
    type: str
    title: str
    severity: str
    scoreImpact: int
    description: str

class RiskProfileResponse(BaseModel):
    project_id: str
    risk_score: int
    risk_level: str
    confidence_score: float = 0.85
    signals: List[RiskSignal] = []
    breakdown: Dict[str, Any] = {}
    summary_text: Optional[str] = None
    review_status: Optional[str] = None

class InvestigationNoteCreate(BaseModel):
    author_name: Optional[str] = "Senior Vigilance Auditor"
    role: Optional[str] = "AUDITOR"
    note_text: str
    action_type: Optional[str] = "NOTE"

class InvestigationNoteResponse(BaseModel):
    id: int
    case_id: str
    author_name: str
    role: str
    note_text: str
    action_type: str
    timestamp: str

class InvestigationCaseResponse(BaseModel):
    case_id: str
    project_id: str
    status: str
    priority: str
    opened_at: str
    assigned_to: str
    summary: Optional[str] = None
    findings: Optional[str] = None
    resolution_notes: Optional[str] = None
    notes: List[InvestigationNoteResponse] = []

# --- AUDIT & TIMELINE SCHEMAS ---
class AuditLogResponse(BaseModel):
    event_id: str
    user_name: str
    role: str
    action: str
    project_id: Optional[str] = None
    timestamp: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    event_hash: Optional[str] = None

class TimelineEvent(BaseModel):
    type: str
    date: Optional[str] = None
    status: str
    description: Optional[str] = None

class TimelineResponse(BaseModel):
    events: List[TimelineEvent]

class SimilarProject(BaseModel):
    project_id: str
    description: str
    similarity_score: float
    state: str
    constituency: str

class SimilarProjectsResponse(BaseModel):
    items: List[SimilarProject]

class EvidenceResponse(BaseModel):
    project_amount: float
    peer_median: float
    peer_min: float
    peer_max: float
    matching_project_ids: List[str]
    timeline_anomaly_details: Optional[Any] = None

class AnalyticsOverview(BaseModel):
    total_projects: int
    active_projects: int
    high_risk_projects: int
    medium_risk_projects: int
    low_risk_projects: int
    red_flagged_projects: int
    ongoing_investigations: int
    total_allocation: float
    total_expenditure: float
    flagged_amount: float
    risk_distribution: Dict[str, int]
    monthly_projects: Optional[List[Dict[str, Any]]] = []
