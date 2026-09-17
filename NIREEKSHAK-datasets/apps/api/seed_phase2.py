import datetime
import hashlib
import json
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import (
    User, State, Constituency, MP, Project, ProjectRisk,
    ProjectApproval, Tender, ContractorRiskProfile, ExpenditureTransaction,
    ProgressUpdate, GeoCheckpoint, GeoEvidence, InvestigationCase,
    InvestigationNote, AuditLog, Notification
)
from routes.auth import hash_password

def seed_demo_data():
    init_db()
    db: Session = SessionLocal()
    if not db:
        print("Could not connect to database for seeding.")
        return

    # 1. Check if demo projects already exist
    existing_p = db.query(Project).filter(Project.project_id == "MPLADS-2026-KL-000101").first()
    if existing_p:
        print("Demo data already seeded. Skipping.")
        db.close()
        return

    print("Seeding NIREEKSHAK Phase 2 Demonstration Dataset...")

    # --- SEED USERS ---
    users_data = [
        ("mp_rahul", "mp.rahul@nireekshak.gov.in", "Rahul Gandhi", "MP", "Member of Parliament", "MP-LS-2024-541"),
        ("approver_sharma", "magistrate.sharma@nireekshak.gov.in", "Dr. Rajesh Sharma, IAS", "APPROVING_AUTHORITY", "District Magistrate & District Collector", "IAS-KL-2015-4091"),
        ("contractor_apex", "director@apexinfra.co.in", "Vikramaditya Rao", "CONTRACTOR", "Managing Director, Apex Infra", "REG-KL-2018-9941"),
        ("officer_patel", "inspections.patel@pwd.gov.in", "Suresh Patel", "FIELD_OFFICER", "Executive Engineer & Chief Inspection Officer", "PWD-ENG-7721"),
        ("auditor_verma", "auditor.verma@cag.gov.in", "Anita Verma", "AUDITOR", "Senior Vigilance Audit Officer", "CAG-AUD-9912"),
        ("admin_system", "admin@nireekshak.gov.in", "National Administrator", "ADMIN", "Director General (Vigilance Systems)", "SYS-ADMIN-001")
    ]
    for username, email, full_name, role, desig, off_id in users_data:
        if not db.query(User).filter(User.username == username).first():
            u = User(
                username=username,
                email=email,
                hashed_password=hash_password("password123"),
                role=role,
                full_name=full_name,
                designation=desig,
                official_id=off_id
            )
            db.add(u)
    db.commit()

    # --- SEED CONTRACTORS ---
    contractors = [
        ContractorRiskProfile(
            contractor_id="CON-APEX-01",
            contractor_name="Apex Infrastructure Projects Ltd",
            registration_number="REG-KL-2018-9941",
            normalized_name="APEX",
            total_projects=18,
            completed_projects=15,
            delayed_projects=2,
            suspicious_projects=0,
            red_flagged_projects=0,
            total_project_value=45000000.0,
            total_expenditure=41000000.0,
            risk_score=15,
            risk_status="LOW",
            contact_email="contact@apexinfra.co.in",
            contact_phone="+91 94471 23456"
        ),
        ContractorRiskProfile(
            contractor_id="CON-VANGUARD-02",
            contractor_name="Vanguard Projects Ltd",
            registration_number="REG-IND-2016-1188",
            normalized_name="VANGUARD",
            total_projects=27,
            completed_projects=19,
            delayed_projects=5,
            suspicious_projects=3,
            red_flagged_projects=2,
            total_project_value=124000000.0,
            total_expenditure=112000000.0,
            risk_score=85,
            risk_status="HIGH",
            contact_email="bids@vanguardprojects.in",
            contact_phone="+91 98840 98765"
        ),
        ContractorRiskProfile(
            contractor_id="CON-SOUTHERN-03",
            contractor_name="Southern Civic Builders Pvt Ltd",
            registration_number="REG-TN-2020-5512",
            normalized_name="SOUTHERN CIVIC",
            total_projects=12,
            completed_projects=9,
            delayed_projects=3,
            suspicious_projects=1,
            red_flagged_projects=0,
            total_project_value=32000000.0,
            total_expenditure=28000000.0,
            risk_score=55,
            risk_status="MEDIUM",
            contact_email="info@southerncivic.com",
            contact_phone="+91 98410 33445"
        ),
        ContractorRiskProfile(
            contractor_id="CON-UPRURAL-04",
            contractor_name="UP Rural Engineering Corp",
            registration_number="REG-UP-2017-8831",
            normalized_name="UP RURAL ENG",
            total_projects=15,
            completed_projects=10,
            delayed_projects=3,
            suspicious_projects=2,
            red_flagged_projects=1,
            total_project_value=58000000.0,
            total_expenditure=51000000.0,
            risk_score=78,
            risk_status="HIGH",
            contact_email="rural.works@uprec.org",
            contact_phone="+91 94500 11223"
        )
    ]
    for c in contractors:
        if not db.query(ContractorRiskProfile).filter(ContractorRiskProfile.contractor_id == c.contractor_id).first():
            db.add(c)
    db.commit()

    # --- STATES & CONSTITUENCIES ---
    states_dict = {}
    for st_name in ["Kerala", "Tamil Nadu", "Uttar Pradesh", "Karnataka", "Maharashtra", "Delhi", "West Bengal", "Rajasthan"]:
        st = db.query(State).filter(State.state_name == st_name).first()
        if not st:
            st = State(state_name=st_name)
            db.add(st)
            db.flush()
        states_dict[st_name] = st

    const_dict = {}
    const_data = [
        ("Wayanad", "Kerala"),
        ("Madurai", "Tamil Nadu"),
        ("Varanasi", "Uttar Pradesh"),
        ("Mysuru", "Karnataka"),
        ("Pune", "Maharashtra"),
        ("Ernakulam", "Kerala"),
        ("Chandni Chowk", "Delhi"),
        ("Kolkata South", "West Bengal"),
        ("Jaipur", "Rajasthan")
    ]
    for c_name, st_name in const_data:
        c = db.query(Constituency).filter(Constituency.constituency_name == c_name).first()
        if not c:
            c = Constituency(state_id=states_dict[st_name].state_id, constituency_name=c_name)
            db.add(c)
            db.flush()
        const_dict[c_name] = c

    # --- SEED SCENARIO PROJECTS ---

    # Scenario 1: Normal (Low Risk)
    p1 = Project(
        project_id="MPLADS-2026-KL-000101",
        project_title="Construction of Kalpetta Valley Rural Connectivity Road",
        work_description="Construction of 2.8 km bituminous road connecting Kalpetta tribal hamlet to main highway with proper side drains.",
        category="Roads & Bridges",
        state_id=states_dict["Kerala"].state_id,
        constituency_id=const_dict["Wayanad"].constituency_id,
        city="Wayanad",
        block="Kalpetta",
        proposed_amount=3500000.0,
        allocated_amount=3500000.0,
        awarded_amount=3420000.0,
        expenditure_amount=3420000.0,
        latitude=11.6854,
        longitude=76.1320,
        proposed_location="Kalpetta Hamlet Section IV, Wayanad",
        recommendation_date=datetime.date(2025, 4, 10),
        approval_date=datetime.date(2025, 5, 12),
        start_date=datetime.date(2025, 6, 1),
        completion_date=datetime.date(2026, 1, 15),
        project_status="COMPLETED",
        approval_status="APPROVED",
        beneficiary_info="850 tribal household residents",
        created_by="Rahul Gandhi"
    )
    db.add(p1)

    # Scenario 2: Cost Anomaly (High Risk)
    p2 = Project(
        project_id="MPLADS-2026-TN-000202",
        project_title="Upgradation of Urban Primary Health Centre at Sellur",
        work_description="Refurbishment and specialized diagnostics equipment setup for municipal clinic building.",
        category="Healthcare",
        state_id=states_dict["Tamil Nadu"].state_id,
        constituency_id=const_dict["Madurai"].constituency_id,
        city="Madurai",
        block="Sellur",
        proposed_amount=2000000.0,
        allocated_amount=2000000.0,
        awarded_amount=3100000.0, # +55% cost anomaly
        expenditure_amount=2850000.0,
        latitude=9.9252,
        longitude=78.1198,
        proposed_location="Near Vaigai River Bank, Sellur, Madurai",
        recommendation_date=datetime.date(2025, 8, 14),
        approval_date=datetime.date(2025, 9, 2),
        start_date=datetime.date(2025, 10, 1),
        project_status="IN_PROGRESS",
        approval_status="APPROVED",
        beneficiary_info="Ward 42 municipal residents",
        created_by="Su. Venkatesan"
    )
    db.add(p2)

    # Scenario 3: Progress Mismatch (High Risk / Red Flag)
    p3 = Project(
        project_id="MPLADS-2026-UP-000303",
        project_title="Construction of Model Community Skill Centre at Rohania",
        work_description="Construction of 2-storey vocational skill training auditorium and public digital library.",
        category="Community Infrastructure",
        state_id=states_dict["Uttar Pradesh"].state_id,
        constituency_id=const_dict["Varanasi"].constituency_id,
        city="Varanasi",
        block="Rohania",
        proposed_amount=8450000.0,
        allocated_amount=8450000.0,
        awarded_amount=8450000.0,
        expenditure_amount=6930000.0, # 82% financial vs 30% physical
        latitude=25.3176,
        longitude=82.9739,
        proposed_location="Rohania Block Administrative Centre, Varanasi",
        recommendation_date=datetime.date(2025, 3, 1),
        approval_date=datetime.date(2025, 4, 15),
        start_date=datetime.date(2025, 5, 1),
        project_status="RED_FLAGGED",
        approval_status="APPROVED",
        beneficiary_info="Local rural youth and SHGs",
        created_by="Narendra Modi"
    )
    db.add(p3)

    # Scenario 4: Contractor Risk History
    p4 = Project(
        project_id="MPLADS-2026-KA-000404",
        project_title="Drinking Water Desalination and Pipeline Infrastructure",
        work_description="Installation of 50,000 LPD reverse osmosis community drinking water plant and distribution lines.",
        category="Drinking Water",
        state_id=states_dict["Karnataka"].state_id,
        constituency_id=const_dict["Mysuru"].constituency_id,
        city="Mysuru",
        block="Nanjangud",
        proposed_amount=4800000.0,
        allocated_amount=4800000.0,
        awarded_amount=4800000.0,
        expenditure_amount=4200000.0,
        latitude=12.2958,
        longitude=76.6394,
        proposed_location="Nanjangud Industrial Belt Zone B, Mysuru",
        recommendation_date=datetime.date(2025, 6, 10),
        approval_date=datetime.date(2025, 7, 1),
        start_date=datetime.date(2025, 7, 20),
        project_status="RED_FLAGGED",
        approval_status="APPROVED",
        created_by="Pratap Simha"
    )
    db.add(p4)

    # Scenario 5: Geographic Anomaly
    p5 = Project(
        project_id="MPLADS-2026-MH-000505",
        project_title="Digital High School Smart Lab & Solar Installation",
        work_description="Procurement of 40 computer terminals, high-speed networking, and 10kW rooftop solar grid.",
        category="Education",
        state_id=states_dict["Maharashtra"].state_id,
        constituency_id=const_dict["Pune"].constituency_id,
        city="Pune",
        block="Haveli",
        proposed_amount=2700000.0,
        allocated_amount=2700000.0,
        awarded_amount=2700000.0,
        expenditure_amount=1950000.0,
        latitude=18.5204,
        longitude=73.8567,
        proposed_location="Zilla Parishad High School, Haveli, Pune",
        recommendation_date=datetime.date(2025, 7, 5),
        approval_date=datetime.date(2025, 8, 1),
        start_date=datetime.date(2025, 8, 20),
        project_status="IN_PROGRESS",
        approval_status="APPROVED",
        created_by="Supriya Sule"
    )
    db.add(p5)

    # Scenario 6: Multi-Anomaly Compound Red Flag
    p6 = Project(
        project_id="MPLADS-2026-KL-000606",
        project_title="Ernakulam Multi-Utility Coastal Community Health & Rehabilitation Centre",
        work_description="Multi-tier disaster relief shelter and primary health centre with emergency solar backup.",
        category="Healthcare",
        state_id=states_dict["Kerala"].state_id,
        constituency_id=const_dict["Ernakulam"].constituency_id,
        city="Ernakulam",
        block="Kochi Coastal Ward",
        proposed_amount=5000000.0,
        allocated_amount=5000000.0,
        awarded_amount=9500000.0, # Massive inflation + overrun
        expenditure_amount=8800000.0,
        latitude=9.9816,
        longitude=76.2999,
        proposed_location="Fort Kochi Coastal Strip, Ernakulam",
        recommendation_date=datetime.date(2025, 2, 10),
        approval_date=datetime.date(2025, 3, 5),
        start_date=datetime.date(2025, 4, 1),
        project_status="RED_FLAGGED",
        approval_status="APPROVED",
        created_by="Hibi Eden"
    )
    db.add(p6)
    db.flush()

    # --- SEED APPROVALS ---
    for p in [p1, p2, p3, p4, p5, p6]:
        appr = ProjectApproval(
            approval_id=f"APP-{p.project_id[-6:]}",
            project_id=p.project_id,
            approved_by="Dr. Rajesh Sharma, IAS",
            designation="District Magistrate & District Collector",
            official_id="IAS-KL-2015-4091",
            approval_date=p.approval_date or datetime.date(2025, 5, 1),
            approval_remarks="Sanctioned in accordance with statutory MPLADS guidelines.",
            digital_signature=hashlib.sha256(f"SIG:{p.project_id}:DM_SHARMA".encode()).hexdigest(),
            document_hash=hashlib.sha256(f"DOC:{p.project_id}:ID_SCAN_VERIFIED".encode()).hexdigest(),
            masked_id_preview="GOV-ID-XXXX-4091",
            location_latitude=p.latitude,
            location_longitude=p.longitude,
            photo_reference="https://images.unsplash.com/photo-1541888946425-d0fbb186156a?w=400"
        )
        db.add(appr)

    # --- SEED TENDERS ---
    tenders_data = [
        (p1, "CON-APEX-01", "Apex Infrastructure Projects Ltd", "REG-KL-2018-9941", 3420000.0, "WO-2025-0101"),
        (p2, "CON-SOUTHERN-03", "Southern Civic Builders Pvt Ltd", "REG-TN-2020-5512", 3100000.0, "WO-2025-0202"),
        (p3, "CON-UPRURAL-04", "UP Rural Engineering Corp", "REG-UP-2017-8831", 8450000.0, "WO-2025-0303"),
        (p4, "CON-VANGUARD-02", "Vanguard Projects Ltd", "REG-IND-2016-1188", 4800000.0, "WO-2025-0404"),
        (p5, "CON-APEX-01", "Apex Infrastructure Projects Ltd", "REG-KL-2018-9941", 2700000.0, "WO-2025-0505"),
        (p6, "CON-VANGUARD-02", "Vanguard Projects Ltd", "REG-IND-2016-1188", 9500000.0, "WO-2025-0606")
    ]
    for prj, c_id, c_name, reg_num, aw_amt, wo_num in tenders_data:
        t = Tender(
            tender_id=f"TND-{prj.project_id[-6:]}",
            project_id=prj.project_id,
            contractor_id=c_id,
            contractor_name=c_name,
            registration_number=reg_num,
            tender_date=prj.approval_date or datetime.date(2025, 5, 15),
            tender_amount=aw_amt,
            estimated_project_amount=float(prj.proposed_amount or aw_amt),
            awarded_amount=aw_amt,
            tender_deviation_percent=((aw_amt - float(prj.proposed_amount or aw_amt)) / float(prj.proposed_amount or aw_amt) * 100) if prj.proposed_amount else 0,
            work_order_number=wo_num,
            work_order_date=prj.start_date or datetime.date(2025, 6, 1),
            contract_start_date=prj.start_date or datetime.date(2025, 6, 1),
            contract_end_date=datetime.date(2026, 6, 1)
        )
        db.add(t)

    # --- SEED 5 CHECKPOINTS FOR EACH PROJECT ---
    for prj in [p1, p2, p3, p4, p5, p6]:
        lat, lng = prj.latitude or 20.0, prj.longitude or 78.0
        codes = [
            ("A", "Location A – Project entrance/reference point", lat, lng),
            ("B", "Location B – North/primary work area", lat + 0.0008, lng),
            ("C", "Location C – Secondary work area", lat, lng + 0.0008),
            ("D", "Location D – Infrastructure/component area", lat - 0.0008, lng),
            ("E", "Location E – Completion/reference area", lat, lng - 0.0008)
        ]
        for c_code, c_name, clat, clng in codes:
            # For scenario 5, intentionally mark D and E as MISMATCH
            is_mismatch = (prj.project_id == "MPLADS-2026-MH-000505" and c_code in ["D", "E"])
            sub_lat = clat + (0.16 if is_mismatch else 0.0001)
            sub_lng = clng + (0.16 if is_mismatch else 0.0001)
            dist = 18400.0 if is_mismatch else 14.0
            
            cp = GeoCheckpoint(
                checkpoint_id=f"CP-{prj.project_id[-6:]}-{c_code}",
                project_id=prj.project_id,
                checkpoint_code=c_code,
                checkpoint_name=c_name,
                expected_latitude=clat,
                expected_longitude=clng,
                allowed_radius_meters=150.0,
                submitted_latitude=sub_lat,
                submitted_longitude=sub_lng,
                gps_accuracy_meters=8.0,
                photo_url=f"https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?w=400",
                photo_hash=hashlib.sha256(f"PHOTO_{prj.project_id}_{c_code}".encode()).hexdigest(),
                timestamp=datetime.datetime.now() - datetime.timedelta(days=10),
                uploader="Suresh Patel (Field Officer)",
                verification_status="MISMATCH" if is_mismatch else "VERIFIED",
                distance_meters=dist
            )
            db.add(cp)

    # --- SEED EXPENDITURES ---
    exp_samples = [
        (p1, [("Civil Materials", "Aggregate, cement, and bituminous mix", 1200000), ("Labor & Masonry", "Grade IV workers wages", 1000000), ("Drainage Works", "Pre-cast culvert installations", 1220000)]),
        (p2, [("Diagnostic Machinery", "Ultrasound and clinical lab units", 1800000), ("Electrical Fittings", "Commercial 3-phase wiring", 1050000)]),
        (p3, [("Foundation Excavation", "Heavy earthmoving and piling", 2500000), ("Structural Framework", "R.C.C column and slab casting", 4430000)]),
        (p4, [("RO Membrane Units", "Imported reverse osmosis filter stacks", 2200000), ("Pipeline Laying", "Cast iron distribution network", 2000000)]),
        (p5, [("IT Hardware", "Desktop terminals and networking racks", 1200000), ("Solar Panels", "Polycrystalline rooftop array", 750000)]),
        (p6, [("Seawall Reinforcement", "Tetrapod and armor rock placement", 4500000), ("Main Pavilion Structure", "Steel truss and storm shelter", 4300000)])
    ]
    for prj, txs in exp_samples:
        cum = 0.0
        for cat, desc, amt in txs:
            cum += amt
            e = ExpenditureTransaction(
                project_id=prj.project_id,
                transaction_date=datetime.date(2025, 9, 1),
                expense_category=cat,
                description=desc,
                amount=amt,
                cumulative_expenditure=cum,
                invoice_number=f"INV-{hashlib.md5(desc.encode()).hexdigest()[:8].upper()}",
                document_hash=hashlib.sha256(f"{desc}:{amt}".encode()).hexdigest(),
                entered_by="Finance Section Officer"
            )
            db.add(e)

    # --- SEED PROGRESS UPDATES ---
    prog_samples = [
        (p1, 100.0, 100.0, "All surfacing, drainage, and road markings completed."),
        (p2, 60.0, 92.0, "Interior partitions installed; diagnostic machinery placed."),
        (p3, 30.0, 82.0, "Pillar footing cast. Superstructure brickwork awaiting materials."),
        (p4, 70.0, 87.5, "RO plant building ready. Pipeline trenching ongoing."),
        (p5, 55.0, 72.0, "Wiring complete. Computers delivered; solar panels awaiting hookup."),
        (p6, 35.0, 92.6, "Foundation works and structural framing started.")
    ]
    for prj, phys, fin, desc in prog_samples:
        pr = ProgressUpdate(
            project_id=prj.project_id,
            update_date=datetime.date(2026, 2, 1),
            physical_progress_percent=phys,
            financial_progress_percent=fin,
            work_description=desc,
            cumulative_expenditure=float(prj.expenditure_amount or 0.0),
            photo_reference="https://images.unsplash.com/photo-1541888946425-d0fbb186156a?w=500",
            photo_hash=hashlib.sha256(f"PROG_{prj.project_id}".encode()).hexdigest(),
            submitted_latitude=prj.latitude,
            submitted_longitude=prj.longitude,
            field_officer="Suresh Patel (Field Officer)"
        )
        db.add(pr)

    # --- SEED RISK PROFILES & INVESTIGATION CASES ---
    risk_data = [
        (p1, 18, "LOW", [], "Project execution adheres to engineering and financial benchmarks."),
        (p2, 76, "HIGH", [
            {"type": "COST_ANOMALY", "title": "Severe Cost Outlier Detected", "severity": "HIGH", "scoreImpact": 24, "description": "Cost (₹31,00,000) is 1.55× higher than peer benchmark median of ₹20,00,000 in Healthcare category."},
            {"type": "TENDER_ANOMALY", "title": "Inflated Tender Award", "severity": "MEDIUM", "scoreImpact": 16, "description": "Tender was awarded +55% above engineering sanctioned estimates."}
        ], "High risk project. Surface indicators suggest anomalous tender cost inflation requiring audit review."),
        (p3, 88, "RED_FLAG", [
            {"type": "PROGRESS_MISMATCH", "title": "Severe Physical vs Financial Discrepancy", "severity": "CRITICAL", "scoreImpact": 22, "description": "Financial expenditure (82.0%) substantially exceeds physical completion (30.0%) with a +52.0% divergence gap."},
            {"type": "EXPENDITURE_VELOCITY", "title": "Abnormal Expenditure Velocity", "severity": "CRITICAL", "scoreImpact": 20, "description": "Rapid fund disbursement with lagging brickwork execution."}
        ], "Project requires urgent investigation. Multiple independent risk signals detected."),
        (p4, 82, "RED_FLAG", [
            {"type": "AGENCY_RISK", "title": "High-Risk Contractor Entity Pattern", "severity": "CRITICAL", "scoreImpact": 20, "description": "Contractor 'Vanguard Projects Ltd' is associated with 3 previously flagged/suspicious MPLADS works."},
            {"type": "TIMELINE_VIOLATION", "title": "Milestone Delay", "severity": "MEDIUM", "scoreImpact": 12, "description": "Work execution delayed past expected statutory completion window."}
        ], "Project requires vigilance scrutiny due to repetitive vendor irregularity patterns."),
        (p5, 78, "HIGH", [
            {"type": "GEOSPATIAL_ANOMALY", "title": "Geofence Boundary Violation", "severity": "CRITICAL", "scoreImpact": 20, "description": "Field evidence was uploaded 18.4 km away from registered project coordinates (18.5204, 73.8567)."},
            {"type": "CHECKPOINT_FAILURE", "title": "2/5 Checkpoints Mismatched", "severity": "HIGH", "scoreImpact": 14, "description": "Checkpoints D and E failed physical site geofence tests."}
        ], "Geospatial location discrepancies detected in field verification submissions."),
        (p6, 92, "RED_FLAG", [
            {"type": "COST_OVERRUN", "title": "Contract Budget Overrun", "severity": "CRITICAL", "scoreImpact": 24, "description": "Expenditure (₹88,00,000) exceeds normal category limits by +76%."},
            {"type": "PROGRESS_MISMATCH", "title": "Severe Progress Divergence", "severity": "CRITICAL", "scoreImpact": 20, "description": "Financial disbursements (92.6%) outpace physical completion (35.0%)."},
            {"type": "AGENCY_RISK", "title": "Repeated Red Flags on Vendor", "severity": "HIGH", "scoreImpact": 18, "description": "Vendor Vanguard Projects Ltd exhibits repeated red-flag concentration."}
        ], "High-priority Red Flag investigation case opened.")
    ]

    for prj, score, level, signals, summary in risk_data:
        r = ProjectRisk(
            project_id=prj.project_id,
            risk_score=score,
            risk_level=level,
            confidence_score=0.92,
            signals=signals,
            summary_text=summary
        )
        db.add(r)

        # If RED_FLAG, open investigation case
        if level == "RED_FLAG":
            c_case = InvestigationCase(
                case_id=f"INV-2026-{prj.project_id[-5:]}",
                project_id=prj.project_id,
                status="OPEN",
                priority="HIGH",
                summary=f"Automated Case: Project flagged with risk score {score}/100.",
                findings=json.dumps(signals)
            )
            db.add(c_case)
            db.flush()

            note1 = InvestigationNote(
                case_id=c_case.case_id,
                author_name="NIREEKSHAK Risk Engine",
                role="SYSTEM",
                note_text=f"Triggered automated case opening due to compound score {score}/100. Signals: " + ", ".join([s["title"] for s in signals]),
                action_type="ESCALATION"
            )
            note2 = InvestigationNote(
                case_id=c_case.case_id,
                author_name="Anita Verma (Auditor)",
                role="AUDITOR",
                note_text="Audit case accepted into review queue. Requested certified measurement book (MB) and voucher ledger from implementing agency.",
                action_type="CLARIFICATION_REQUEST"
            )
            db.add(note1)
            db.add(note2)

    db.commit()
    db.close()
    print("NIREEKSHAK Phase 2 Demonstration Dataset seeded successfully!")

if __name__ == "__main__":
    seed_demo_data()
