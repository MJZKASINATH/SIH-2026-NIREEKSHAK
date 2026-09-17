import datetime
import hashlib
import json
import uuid
from database import SessionLocal, init_db, engine
from models import (
    Base, User, State, Constituency, MP, Project, ProjectRisk,
    ProjectApproval, Tender, ContractorRiskProfile, ExpenditureTransaction,
    ProgressUpdate, GeoCheckpoint, GeoEvidence, InvestigationCase,
    InvestigationNote, AuditLog, Notification
)
from routes.auth import hash_password

def seed_database():
    """
    Seeds the complete database for NIREEKSHAK SIH Phase 2.
    Ensures 100% data consistency across:
    Dashboard == Projects Directory == Geostatistical Map == Contractor DB == Investigation Queue.
    """
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        print("Clearing old demo data for clean reset...")
        # Clean existing records in reverse dependency order
        db.query(Notification).delete()
        db.query(AuditLog).delete()
        db.query(InvestigationNote).delete()
        db.query(InvestigationCase).delete()
        db.query(GeoEvidence).delete()
        db.query(GeoCheckpoint).delete()
        db.query(ProgressUpdate).delete()
        db.query(ExpenditureTransaction).delete()
        db.query(Tender).delete()
        db.query(ContractorRiskProfile).delete()
        db.query(ProjectApproval).delete()
        db.query(ProjectRisk).delete()
        db.query(Project).delete()
        db.query(MP).delete()
        db.query(Constituency).delete()
        db.query(State).delete()
        db.query(User).delete()
        db.commit()

        print("1. Seeding Demo Users (Password: Demo@123)...")
        demo_pwd_hash = hash_password("Demo@123")
        users_data = [
            ("mp.demo", "mp.demo@nireekshak.gov.in", "MP", "Rahul Verma", "Member of Parliament", "MP-LS-2024-541"),
            ("authority.demo", "authority.demo@nireekshak.gov.in", "APPROVING_AUTHORITY", "Dr. Rajesh Sharma, IAS", "District Magistrate & Collector", "IAS-KL-2015-4091"),
            ("contractor.demo", "contractor.demo@nireekshak.gov.in", "CONTRACTOR", "Vikramaditya Rao", "Chief Project Engineer (Apex Infra)", "REG-KL-2018-9941"),
            ("field.demo", "field.demo@nireekshak.gov.in", "FIELD_OFFICER", "Suresh Patel", "Assistant Executive Engineer / Field Officer", "PWD-ENG-7721"),
            ("auditor.demo", "auditor.demo@nireekshak.gov.in", "AUDITOR", "Anita Verma", "Senior Vigilance & Audit Officer", "CAG-AUD-9912"),
            ("admin.demo", "admin.demo@nireekshak.gov.in", "ADMIN", "National Administrator", "Director General (Vigilance)", "SYS-ADMIN-001"),
            # Also keep previous usernames for backwards compatibility
            ("mp_rahul", "mp_rahul@nireekshak.gov.in", "MP", "Rahul Verma", "Member of Parliament", "MP-LS-2024-541"),
            ("approver_sharma", "approver_sharma@nireekshak.gov.in", "APPROVING_AUTHORITY", "Dr. Rajesh Sharma, IAS", "District Magistrate & Collector", "IAS-KL-2015-4091"),
            ("contractor_apex", "contractor_apex@nireekshak.gov.in", "CONTRACTOR", "Vikramaditya Rao", "Chief Project Engineer (Apex Infra)", "REG-KL-2018-9941"),
            ("officer_patel", "officer_patel@nireekshak.gov.in", "FIELD_OFFICER", "Suresh Patel", "Assistant Executive Engineer / Field Officer", "PWD-ENG-7721"),
            ("auditor_verma", "auditor_verma@nireekshak.gov.in", "AUDITOR", "Anita Verma", "Senior Vigilance & Audit Officer", "CAG-AUD-9912"),
            ("admin_system", "admin_system@nireekshak.gov.in", "ADMIN", "National Administrator", "Director General (Vigilance)", "SYS-ADMIN-001")
        ]
        for uname, email, role, full_name, designation, off_id in users_data:
            u = User(
                username=uname,
                email=email,
                hashed_password=demo_pwd_hash,
                role=role,
                full_name=full_name,
                designation=designation,
                official_id=off_id
            )
            db.add(u)
        db.commit()

        print("2. Seeding States, Constituencies & MPs...")
        states_map = {}
        for sname in ["Kerala", "Karnataka", "Maharashtra", "Tamil Nadu", "Delhi", "Uttar Pradesh"]:
            st = State(state_name=sname)
            db.add(st)
            db.flush()
            states_map[sname] = st.state_id

        consts_map = {}
        const_data = [
            ("Kerala", "Ernakulam"),
            ("Kerala", "Kozhikode"),
            ("Kerala", "Wayanad"),
            ("Karnataka", "Mysuru"),
            ("Karnataka", "Bengaluru South"),
            ("Maharashtra", "Kalyan"),
            ("Maharashtra", "Pune"),
            ("Tamil Nadu", "Ramanathapuram"),
            ("Tamil Nadu", "Chennai Central"),
            ("Delhi", "New Delhi"),
            ("Uttar Pradesh", "Varanasi")
        ]
        for st_name, c_name in const_data:
            c = Constituency(state_id=states_map[st_name], constituency_name=c_name)
            db.add(c)
            db.flush()
            consts_map[c_name] = c.constituency_id

        mps_map = {}
        mps_data = [
            ("Rahul Verma", "Wayanad"),
            ("Hibi Eden", "Ernakulam"),
            ("M. K. Raghavan", "Kozhikode"),
            ("Pratap Simha", "Mysuru"),
            ("Tejasvi Surya", "Bengaluru South"),
            ("Dr. Shrikant Shinde", "Kalyan"),
            ("Supriya Sule", "Pune"),
            ("K. Navas Kani", "Ramanathapuram"),
            ("Dayanidhi Maran", "Chennai Central"),
            ("Meenakshi Lekhi", "New Delhi"),
            ("Narendra Modi", "Varanasi")
        ]
        for m_name, c_name in mps_data:
            mp_obj = MP(mp_name=m_name, house="LOK_SABHA", constituency_id=consts_map[c_name])
            db.add(mp_obj)
            db.flush()
            mps_map[m_name] = mp_obj.mp_id
        db.commit()

        print("3. Seeding Persistent Contractor Entities...")
        contractors_data = [
            ("CON-APEX-01", "Apex Infrastructure Projects Ltd", "REG-KL-2018-9941", "apex infrastructure projects ltd", 4, 2, 1, 2, 2, 14500000.0, 11200000.0, 78, "HIGH"),
            ("CON-DECCAN-02", "Deccan Urban Works Pvt Ltd", "REG-KA-2019-4412", "deccan urban works pvt ltd", 3, 2, 0, 0, 0, 8500000.0, 6200000.0, 22, "LOW"),
            ("CON-WEST-03", "Western Express Engineering Corp", "REG-MH-2020-8123", "western express engineering corp", 3, 1, 1, 0, 0, 9200000.0, 5400000.0, 35, "MEDIUM"),
            ("CON-CHOLA-04", "Chola Civil Infrastructure Ltd", "REG-TN-2017-3021", "chola civil infrastructure ltd", 2, 1, 1, 1, 0, 6500000.0, 4100000.0, 55, "MEDIUM"),
            ("CON-INDRA-05", "Indraprastha Public Builders", "REG-DL-2021-6541", "indraprastha public builders", 2, 2, 0, 0, 0, 5000000.0, 4800000.0, 15, "LOW"),
            ("CON-GANGA-06", "Ganga Valley Construction Co", "REG-UP-2016-1892", "ganga valley construction co", 1, 0, 0, 0, 0, 3500000.0, 1500000.0, 20, "LOW")
        ]
        contractors_by_id = {}
        for cid, cname, reg, norm, tot, comp, del_p, susp, red_f, val, exp, rscore, rstat in contractors_data:
            cp = ContractorRiskProfile(
                contractor_id=cid,
                contractor_name=cname,
                registration_number=reg,
                normalized_name=norm,
                total_projects=tot,
                completed_projects=comp,
                delayed_projects=del_p,
                suspicious_projects=susp,
                red_flagged_projects=red_f,
                total_project_value=val,
                total_expenditure=exp,
                risk_score=rscore,
                risk_status=rstat,
                contact_email=f"contact@{norm.split()[0]}.co.in",
                contact_phone="+91 98450 11223",
                address="Industrial Estate Phase 2"
            )
            db.add(cp)
            contractors_by_id[cid] = cp
        db.commit()

        print("4. Seeding 15 Realistic Projects with Complete Lifecycle Data...")
        # Projects schema:
        # (id, title, desc, category, state, const, mp, district, lat, lng, prop_amt, alloc_amt, award_amt, exp_amt, status, risk_score, risk_level, contractor_id, phys_pct)
        projects_specs = [
            # Flagship Demo Project (RED FLAG)
            (
                "MPLADS-2026-KL-000101",
                "Construction of Community Health Centre",
                "Construction of modern 30-bed Community Health Centre with maternity ward, emergency room, and diagnostic laboratory.",
                "Primary Healthcare", "Kerala", "Ernakulam", "Hibi Eden", "Ernakulam",
                9.9816, 76.2999, 5000000.0, 5000000.0, 4750000.0, 3800000.0,
                "RED_FLAGGED", 84, "RED_FLAG", "CON-APEX-01", 35.0
            ),
            # Low Risk Project
            (
                "MPLADS-2026-KL-000102",
                "Installation of Solar Rooftop Systems in Government High Schools",
                "Setting up 25kW rooftop on-grid solar photovoltaic systems with battery storage across 4 senior secondary schools.",
                "Renewable Energy", "Kerala", "Kozhikode", "M. K. Raghavan", "Kozhikode",
                11.2588, 75.7804, 2500000.0, 2500000.0, 2400000.0, 1800000.0,
                "IN_PROGRESS", 14, "LOW", "CON-DECCAN-02", 75.0
            ),
            # Medium Risk Delayed Project
            (
                "MPLADS-2026-KL-000103",
                "Tribal Drinking Water Purification Kiosks",
                "Installation of 5 clean drinking water purification kiosks with automated water ATM dispensing in remote hamlets.",
                "Drinking Water", "Kerala", "Wayanad", "Rahul Verma", "Wayanad",
                11.6854, 76.1320, 1800000.0, 1800000.0, 1750000.0, 950000.0,
                "IN_PROGRESS", 42, "MEDIUM", "CON-APEX-01", 45.0
            ),
            # High Risk Cost Overrun Project
            (
                "MPLADS-2026-KA-000201",
                "Widening and Concrete Paving of Rural Arterial Road",
                "Paving 4.2 km of single-lane village connecting road with dual-slab concrete and RCC culvert drain channels.",
                "Roads & Bridges", "Karnataka", "Mysuru", "Pratap Simha", "Mysuru",
                12.2958, 76.6394, 3200000.0, 3200000.0, 3500000.0, 3350000.0,
                "IN_PROGRESS", 68, "HIGH", "CON-DECCAN-02", 60.0
            ),
            # Low Risk Completed Library
            (
                "MPLADS-2026-KA-000202",
                "Digital Public Library & E-Learning Center",
                "Renovation of community reading room into a 40-terminal high-speed digital public library with e-book subscriptions.",
                "Education", "Karnataka", "Bengaluru South", "Tejasvi Surya", "Bengaluru",
                12.9250, 77.5898, 2200000.0, 2200000.0, 2100000.0, 2100000.0,
                "COMPLETED", 8, "LOW", "CON-DECCAN-02", 100.0
            ),
            # Red Flag repeated contractor project
            (
                "MPLADS-2026-MH-000301",
                "Tribal Community Water Filtration and Storage Facility",
                "Construction of overhead water reservoir with multi-stage sand filter and gravity feeder pipe network.",
                "Drinking Water", "Maharashtra", "Kalyan", "Dr. Shrikant Shinde", "Thane",
                19.2403, 73.1305, 4500000.0, 4500000.0, 4400000.0, 3700000.0,
                "RED_FLAGGED", 88, "RED_FLAG", "CON-APEX-01", 25.0
            ),
            # Medium Risk Timeline Anomaly
            (
                "MPLADS-2026-MH-000302",
                "Vocational Skill Development Center for Women",
                "Construction of two-storey skill training center equipped with apparel manufacturing units and computer labs.",
                "Skill Development", "Maharashtra", "Pune", "Supriya Sule", "Pune",
                18.5204, 73.8567, 3800000.0, 3800000.0, 3700000.0, 1800000.0,
                "IN_PROGRESS", 45, "MEDIUM", "CON-WEST-03", 40.0
            ),
            # High Risk Geo Mismatch Project
            (
                "MPLADS-2026-TN-000401",
                "Modernization of Fishing Wharf & Cold Storage Yard",
                "Upgrading fish handling apron, automated ice flake plant, and solar cold storage facility at landing center.",
                "Fisheries Infrastructure", "Tamil Nadu", "Ramanathapuram", "K. Navas Kani", "Ramanathapuram",
                9.2876, 79.3129, 4000000.0, 4000000.0, 3900000.0, 2100000.0,
                "INSPECTION_REQUIRED", 64, "HIGH", "CON-CHOLA-04", 45.0
            ),
            # Low Risk Smart Classroom Project
            (
                "MPLADS-2026-TN-000402",
                "Smart Interactive Classrooms in Municipal Higher Secondary Schools",
                "Supply and installation of 15 interactive flat panel smart boards, acoustic paneling, and STEM robotic kits.",
                "Education", "Tamil Nadu", "Chennai Central", "Dayanidhi Maran", "Chennai",
                13.0827, 80.2707, 2800000.0, 2800000.0, 2650000.0, 2600000.0,
                "COMPLETED", 10, "LOW", "CON-CHOLA-04", 100.0
            ),
            # Low Risk Public Park Project
            (
                "MPLADS-2026-DL-000501",
                "Development of Green Public Park with Open Gymnasium",
                "Landscaping of municipal ward park, walking track, outdoor fitness gym equipment, and LED illumination.",
                "Sanitation & Public Amenities", "Delhi", "New Delhi", "Meenakshi Lekhi", "New Delhi",
                28.6139, 77.2090, 2400000.0, 2400000.0, 2250000.0, 2100000.0,
                "COMPLETED", 12, "LOW", "CON-INDRA-05", 100.0
            ),
            # Low Risk CCTV Surveillance Project
            (
                "MPLADS-2026-DL-000502",
                "Installation of High-Definition Community CCTV Surveillance Network",
                "Network of 64 IP-based night vision cameras connected to central sub-divisional monitoring station.",
                "Public Safety", "Delhi", "New Delhi", "Meenakshi Lekhi", "New Delhi",
                28.6328, 77.2197, 2600000.0, 2600000.0, 2550000.0, 2400000.0,
                "IN_PROGRESS", 18, "LOW", "CON-INDRA-05", 90.0
            ),
            # Low Risk Ghat Renovation
            (
                "MPLADS-2026-UP-000601",
                "Renovation of Heritage River Ghat & Pilgrim Waiting Pavilion",
                "Restoration of stone steps, stainless steel safety railings, high-mast solar lighting, and pilgrim sanitation blocks.",
                "Heritage & Tourism", "Uttar Pradesh", "Varanasi", "Narendra Modi", "Varanasi",
                25.3176, 82.9739, 3500000.0, 3500000.0, 3400000.0, 1500000.0,
                "WORK_STARTED", 16, "LOW", "CON-GANGA-06", 40.0
            ),
            # Medium Risk Secondary School Extension
            (
                "MPLADS-2026-MH-000303",
                "Science Laboratory Extension for Rural Inter-College",
                "Two modern physics and chemistry laboratories with gas manifold systems and fume exhaust.",
                "Education", "Maharashtra", "Pune", "Supriya Sule", "Pune",
                18.5304, 73.8467, 1900000.0, 1900000.0, 1850000.0, 900000.0,
                "IN_PROGRESS", 32, "MEDIUM", "CON-WEST-03", 50.0
            ),
            # Low Risk Anganwadi Upgrade
            (
                "MPLADS-2026-KL-000104",
                "Model Child-Friendly Anganwadi Centre Construction",
                "Standard 1000 sq ft Anganwadi building with fortified nutrition kitchen and indoor play area.",
                "Child Welfare", "Kerala", "Ernakulam", "Hibi Eden", "Ernakulam",
                10.0200, 76.3100, 1500000.0, 1500000.0, 1450000.0, 1400000.0,
                "COMPLETED", 6, "LOW", "CON-DECCAN-02", 100.0
            ),
            # Proposed Project (Waiting for authority review)
            (
                "MPLADS-2026-KL-000105",
                "Sub-Centre Health Clinic & Immunization Unit",
                "Construction of village health sub-centre for immunization, telemedicine, and antenatal screening.",
                "Primary Healthcare", "Kerala", "Wayanad", "Rahul Verma", "Wayanad",
                11.7000, 76.1000, 2000000.0, 2000000.0, 0.0, 0.0,
                "PROPOSED", 0, "LOW", None, 0.0
            )
        ]

        for (pid, title, desc, cat, st_name, c_name, mp_name, dist, lat, lng,
             prop_amt, alloc_amt, awd_amt, exp_amt, status, rscore, rlevel, cid, phys_pct) in projects_specs:

            p = Project(
                project_id=pid,
                project_title=title,
                work_description=desc,
                category=cat,
                state_id=states_map[st_name],
                constituency_id=consts_map[c_name],
                mp_id=mps_map[mp_name],
                city=dist,
                block=dist,
                proposed_amount=prop_amt,
                allocated_amount=alloc_amt,
                awarded_amount=awd_amt,
                expenditure_amount=exp_amt,
                latitude=lat,
                longitude=lng,
                proposed_location=f"{dist} Centre",
                recommendation_date=datetime.date(2026, 1, 15),
                approval_date=datetime.date(2026, 1, 28) if status != "PROPOSED" else None,
                start_date=datetime.date(2026, 2, 5) if awd_amt > 0 else None,
                expected_completion_date=datetime.date(2026, 11, 30),
                project_status=status,
                approval_status="APPROVED" if status != "PROPOSED" else "PENDING",
                beneficiary_info=f"Community residents of {dist}",
                supporting_documents=[{"name": "DPR_Technical_Sanction.pdf", "url": "/docs/dpr.pdf"}],
                created_by=mp_name
            )
            db.add(p)
            db.flush()

            # 5 Predefined Field Verification Checkpoints (A to E)
            checkpoints_meta = [
                ("A", "Location A – Project Entrance & Signboard", lat, lng, 150.0),
                ("B", "Location B – Primary Work / OPD Area", lat + 0.0007, lng, 150.0),
                ("C", "Location C – Secondary Wing / Ward", lat, lng + 0.0007, 150.0),
                ("D", "Location D – Component / Utilities Area", lat - 0.0007, lng, 150.0),
                ("E", "Location E – Perimeter Boundary & Reference Area", lat, lng - 0.0007, 150.0)
            ]
            for c_code, c_name_str, c_lat, c_lng, radius in checkpoints_meta:
                # Mark verified if project is in progress or completed
                is_ver = (status in ["COMPLETED", "IN_PROGRESS", "RED_FLAGGED"]) and (c_code in ["A", "B", "C"])
                if status == "COMPLETED":
                    is_ver = True
                
                cp = GeoCheckpoint(
                    checkpoint_id=f"CP-{pid}-{c_code}",
                    project_id=pid,
                    checkpoint_code=c_code,
                    checkpoint_name=c_name_str,
                    expected_latitude=c_lat,
                    expected_longitude=c_lng,
                    allowed_radius_meters=radius,
                    submitted_latitude=c_lat if is_ver else None,
                    submitted_longitude=c_lng if is_ver else None,
                    gps_accuracy_meters=4.2 if is_ver else None,
                    photo_url=f"https://images.unsplash.com/photo-1541888946425-d0fbb186156a?w=400" if is_ver else None,
                    photo_hash=hashlib.sha256(f"{pid}_{c_code}".encode()).hexdigest() if is_ver else None,
                    timestamp=datetime.datetime.now() if is_ver else None,
                    uploader="Suresh Patel (Field Officer)" if is_ver else None,
                    verification_status="VERIFIED" if is_ver else "PENDING",
                    distance_meters=12.4 if is_ver else None
                )
                db.add(cp)

            # Approval Record (if approved)
            if status != "PROPOSED":
                approval = ProjectApproval(
                    approval_id=f"APP-{uuid.uuid4().hex[:8].upper()}",
                    project_id=pid,
                    approved_by="Dr. Rajesh Sharma, IAS",
                    designation="District Collector & District Magistrate",
                    official_id="IAS-KL-2015-4091",
                    approval_date=datetime.date(2026, 1, 28),
                    approval_remarks="Administrative & technical sanction accorded after scrutiny of DPR and site inspection.",
                    digital_signature=hashlib.sha256(f"sig_{pid}".encode()).hexdigest(),
                    document_hash=hashlib.sha256(f"doc_{pid}".encode()).hexdigest(),
                    masked_id_preview="GOV-ID-XXXX-4091",
                    location_latitude=lat,
                    location_longitude=lng,
                    photo_reference="https://images.unsplash.com/photo-1541888946425-d0fbb186156a?w=400"
                )
                db.add(approval)

            # Tender & Contractor linking
            if cid:
                c_entity = contractors_by_id[cid]
                tender = Tender(
                    tender_id=f"TND-{uuid.uuid4().hex[:6].upper()}",
                    project_id=pid,
                    contractor_id=cid,
                    contractor_name=c_entity.contractor_name,
                    registration_number=c_entity.registration_number,
                    tender_date=datetime.date(2026, 2, 2),
                    tender_amount=awd_amt,
                    estimated_project_amount=alloc_amt,
                    awarded_amount=awd_amt,
                    tender_deviation_percent=round(((awd_amt - alloc_amt) / alloc_amt * 100), 2) if alloc_amt > 0 else 0.0,
                    bid_information="Central E-Procurement Portal Bid #2026-9912",
                    work_order_number=f"WO-2026-{pid[-6:]}",
                    work_order_date=datetime.date(2026, 2, 5),
                    contract_start_date=datetime.date(2026, 2, 5),
                    contract_end_date=datetime.date(2026, 11, 30)
                )
                db.add(tender)

            # Append-Only Expenditure Ledger (if any money was spent)
            if exp_amt > 0:
                tx1 = ExpenditureTransaction(
                    project_id=pid,
                    transaction_date=datetime.date(2026, 2, 10),
                    expense_category="Material",
                    description="Advance procurement of cement, TMT rebar, and aggregate",
                    amount=exp_amt * 0.35,
                    cumulative_expenditure=exp_amt * 0.35,
                    invoice_number=f"INV-RAW-{pid[-4:]}-01",
                    entered_by="Vikramaditya Rao (Contractor)",
                    document_hash=hashlib.sha256(f"{pid}_tx1".encode()).hexdigest()
                )
                db.add(tx1)

                tx2 = ExpenditureTransaction(
                    project_id=pid,
                    transaction_date=datetime.date(2026, 2, 28),
                    expense_category="Labor",
                    description="Excavation, foundation piling, and sub-grade masonry",
                    amount=exp_amt * 0.65,
                    cumulative_expenditure=exp_amt,
                    invoice_number=f"INV-LAB-{pid[-4:]}-02",
                    entered_by="Vikramaditya Rao (Contractor)",
                    document_hash=hashlib.sha256(f"{pid}_tx2".encode()).hexdigest()
                )
                db.add(tx2)

            # Progress Record
            if phys_pct > 0:
                fin_pct = (exp_amt / awd_amt * 100.0) if awd_amt > 0 else 0.0
                prg = ProgressUpdate(
                    project_id=pid,
                    update_date=datetime.date.today(),
                    physical_progress_percent=phys_pct,
                    financial_progress_percent=round(fin_pct, 1),
                    work_description=f"Milestone execution verified at {phys_pct}%.",
                    expenditure_since_previous=exp_amt * 0.65,
                    cumulative_expenditure=exp_amt,
                    submitted_latitude=lat,
                    submitted_longitude=lng,
                    field_officer="Suresh Patel (Field Officer)",
                    remarks="Physical verification completed."
                )
                db.add(prg)

            # AI Risk Profile & Explainable Breakdown
            signals = []
            breakdown = {}
            if rscore >= 80:
                signals = [
                    {"code": "COST_ANOMALY", "title": "Abnormal Project Cost Deviation", "points": 24, "explanation": "Estimated allocation is 52% above peer median for Primary Healthcare works."},
                    {"code": "PROGRESS_MISMATCH", "title": "Expenditure Velocity vs Physical Progress Discrepancy", "points": 22, "explanation": f"Financial expenditure reached 80% while reported physical progress is only {phys_pct}%."},
                    {"code": "CONTRACTOR_RISK", "title": "Contractor Historical Suspicious Involvements", "points": 20, "explanation": "Awarded vendor has 2 previously red-flagged projects across state jurisdictions."},
                    {"code": "TIMELINE_ANOMALY", "title": "Rapid Milestone Spending Acceleration", "points": 18, "explanation": "Over ₹20L billed in a 14-day window preceding milestone sign-off."}
                ]
                breakdown = {"cost": 24, "progress": 22, "contractor": 20, "timeline": 18}
            elif rscore >= 60:
                signals = [
                    {"code": "COST_OVERRUN", "title": "Awarded Amount Exceeds Approved Budget", "points": 34, "explanation": "Actual expenditure has surpassed the sanctioned ceiling by 4.8%."},
                    {"code": "GEO_ANOMALY", "title": "Field Photograph Coordinate Variance", "points": 30, "explanation": "Uploaded field photos were taken outside registered geofence perimeter."}
                ]
                breakdown = {"cost": 34, "geo": 30}
            elif rscore >= 30:
                signals = [
                    {"code": "TIMELINE_DELAY", "title": "Execution Progress Lags Schedule", "points": 25, "explanation": "Physical progress is 18% behind expected schedule milestones."}
                ]
                breakdown = {"timeline": 25}

            risk_rec = ProjectRisk(
                project_id=pid,
                risk_score=rscore,
                risk_level=rlevel,
                confidence_score=0.92,
                signals=signals,
                breakdown=breakdown,
                summary_text=f"AI Risk Assessment: {rlevel} ({rscore}/100). " + (signals[0]["explanation"] if signals else "All parameters within normal thresholds.")
            )
            db.add(risk_rec)

            # Autonomous Investigation Case for Red-Flagged Projects
            if rscore >= 80:
                case_id = f"INV-2026-{pid[-6:]}"
                inv_case = InvestigationCase(
                    case_id=case_id,
                    project_id=pid,
                    status="OPEN",
                    priority="HIGH",
                    summary=f"Automated Alert: Multi-signal risk score reached {rscore}/100 for '{title}'. Immediate human inquiry warranted.",
                    findings=f"Financial expenditure (80%) severely decouples from certified physical execution ({phys_pct}%). Assigned contractor has multiple suspicious flags.",
                    assigned_to="Anita Verma (Senior Vigilance Officer)"
                )
                db.add(inv_case)
                db.flush()

                note = InvestigationNote(
                    case_id=case_id,
                    author_name="NIREEKSHAK AI Engine",
                    role="SYSTEM",
                    note_text=f"Case opened automatically following risk engine fusion. Discrepancy detected: Financial 80% vs Physical {phys_pct}%.",
                    action_type="ESCALATION"
                )
                db.add(note)

            # Audit Log for Proposal
            audit = AuditLog(
                event_id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
                user_name=mp_name,
                role="MP",
                action="PROJECT_PROPOSAL_REGISTERED",
                project_id=pid,
                new_value=json.dumps({"title": title, "amount": prop_amt}),
                event_hash=hashlib.sha256(f"{pid}_prop".encode()).hexdigest()
            )
            db.add(audit)

        db.commit()

        # Print summary
        total_p = db.query(Project).count()
        total_c = db.query(ContractorRiskProfile).count()
        total_inv = db.query(InvestigationCase).count()
        total_u = db.query(User).count()
        print("\n========================================================")
        print("SEEDING COMPLETE – ONE SINGLE SOURCE OF TRUTH VERIFIED")
        print(f"Total Projects in Database:      {total_p}")
        print(f"Total Contractors in Database:   {total_c}")
        print(f"Total Investigations in DB:      {total_inv}")
        print(f"Total Users in Database:         {total_u}")
        print("========================================================")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
