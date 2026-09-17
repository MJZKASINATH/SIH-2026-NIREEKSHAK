import unittest
import sys
import os

# Add api directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestPhase2Lifecycle(unittest.TestCase):

    def test_01_health_check(self):
        resp = client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "2.0.0")

    def test_02_auth_login_demo_credentials(self):
        # Test MP Login
        resp_mp = client.post("/api/auth/login", json={
            "username": "mp.demo",
            "password": "Demo@123"
        })
        self.assertEqual(resp_mp.status_code, 200)
        data_mp = resp_mp.json()
        self.assertIn("access_token", data_mp)
        self.assertEqual(data_mp["user"]["role"], "MP")
        TestPhase2Lifecycle.mp_token = data_mp["access_token"]

        # Test Approving Authority Login
        resp_auth = client.post("/api/auth/login", json={
            "username": "authority.demo",
            "password": "Demo@123"
        })
        self.assertEqual(resp_auth.status_code, 200)
        data_auth = resp_auth.json()
        self.assertEqual(data_auth["user"]["role"], "APPROVING_AUTHORITY")
        TestPhase2Lifecycle.authority_token = data_auth["access_token"]

    def test_03_project_propose(self):
        proposal_payload = {
            "mp_name": "Rahul Verma",
            "mp_constituency": "Wayanad",
            "state": "Kerala",
            "district": "Wayanad",
            "local_body": "Sulthan Bathery",
            "title": "Automated Unit Test - Tribal Water Kiosk",
            "description": "Installation of 5 clean drinking water purification kiosks.",
            "category": "Drinking Water",
            "proposed_amount": 1500000.0,
            "estimated_cost": 1500000.0,
            "beneficiary_info": "300 tribal residents",
            "proposed_location": "Sulthan Bathery Junction",
            "latitude": 11.6664,
            "longitude": 76.2627
        }
        resp = client.post(
            "/api/projects/propose",
            json=proposal_payload,
            headers={"Authorization": f"Bearer {TestPhase2Lifecycle.mp_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["id"].startswith("MPLADS-2026-KE-"))
        self.assertEqual(data["status"], "SUBMITTED")
        TestPhase2Lifecycle.created_project_id = data["id"]

    def test_04_unauthorized_approval_attempt_by_mp(self):
        """Strict RBAC test: MP attempting to approve project MUST return 403 Forbidden."""
        pid = getattr(TestPhase2Lifecycle, "created_project_id", "MPLADS-2026-KL-000101")
        approval_payload = {
            "approved_by": "Rahul Verma",
            "designation": "MP",
            "official_id": "MP-LS-2024-541",
            "digital_signature": "ILLEGAL_SELF_APPROVAL_SIG",
            "scanned_id_demo_reference": "DEMO_ID",
            "location_latitude": 11.6664,
            "location_longitude": 76.2627
        }
        resp = client.post(
            f"/api/projects/{pid}/approve",
            json=approval_payload,
            headers={"Authorization": f"Bearer {TestPhase2Lifecycle.mp_token}"}
        )
        self.assertEqual(resp.status_code, 403, "MP must NOT be allowed to approve project")

    def test_05_authorized_project_approve(self):
        pid = getattr(TestPhase2Lifecycle, "created_project_id", "MPLADS-2026-KL-000101")
        approval_payload = {
            "approved_by": "Dr. Rajesh Sharma, IAS",
            "designation": "District Magistrate & Collector",
            "official_id": "IAS-KL-2015-4091",
            "digital_signature": "TEST_SIG_SHA256_HASH",
            "scanned_id_demo_reference": "DEMO_ID_VERIFIED_DOC",
            "location_latitude": 11.6664,
            "location_longitude": 76.2627
        }
        resp = client.post(
            f"/api/projects/{pid}/approve",
            json=approval_payload,
            headers={"Authorization": f"Bearer {TestPhase2Lifecycle.authority_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["project_id"], pid)
        self.assertIn("masked_id_preview", data)

    def test_06_tender_award(self):
        pid = getattr(TestPhase2Lifecycle, "created_project_id", "MPLADS-2026-KL-000101")
        tender_payload = {
            "contractor_name": "Apex Infrastructure Projects Ltd",
            "registration_number": "REG-KL-2018-9941",
            "tender_amount": 1480000.0,
            "awarded_amount": 1480000.0,
            "work_order_number": "WO-TEST-2026-001"
        }
        resp = client.post(
            f"/api/projects/{pid}/tender",
            json=tender_payload,
            headers={"Authorization": f"Bearer {TestPhase2Lifecycle.authority_token}"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["contractor_name"], "Apex Infrastructure Projects Ltd")
        self.assertEqual(data["awarded_amount"], 1480000.0)

    def test_07_checkpoint_verification(self):
        pid = getattr(TestPhase2Lifecycle, "created_project_id", "MPLADS-2026-KL-000101")
        verify_payload = {
            "checkpoint_code": "A",
            "submitted_latitude": 11.6664,
            "submitted_longitude": 76.2627,
            "photo_url": "https://example.com/checkpointA.jpg",
            "uploader": "Suresh Patel (Field Officer)"
        }
        resp = client.post(f"/api/projects/{pid}/checkpoints/A/verify", json=verify_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["verification_status"], "VERIFIED")
        self.assertLessEqual(data["distance_meters"], 150.0)

    def test_08_append_only_expenditure_ledger(self):
        pid = getattr(TestPhase2Lifecycle, "created_project_id", "MPLADS-2026-KL-000101")
        exp_payload = {
            "amount": 500000.0,
            "expense_category": "Mobilization Advance",
            "description": "Initial contractor mobilization and site surveying",
            "invoice_number": "INV-TEST-001",
            "entered_by": "Vikramaditya Rao"
        }
        resp = client.post(f"/api/projects/{pid}/expenditure", json=exp_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["amount"], 500000.0)
        self.assertEqual(data["cumulative_expenditure"], 500000.0)

    def test_09_audit_trail_immutable(self):
        resp = client.get("/api/audit-logs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(len(data), 0)
        self.assertTrue(all(item.get("event_hash") for item in data))

    def test_10_master_file_10_tabs_flagship(self):
        resp = client.get("/api/projects/MPLADS-2026-KL-000101/master-file")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("header", data)
        self.assertIn("proposal", data)
        self.assertIn("approval", data)
        self.assertIn("tender", data)
        self.assertIn("expenditures", data)
        self.assertIn("progressUpdates", data)
        self.assertIn("checkpoints", data)
        self.assertIn("evidence", data)
        self.assertIn("riskAnalysis", data)
        self.assertIn("investigation", data)
        self.assertIn("auditTrail", data)
        self.assertGreaterEqual(data["header"]["riskScore"], 80)
        self.assertEqual(data["header"]["riskLevel"], "RED_FLAG")

if __name__ == "__main__":
    unittest.main()
