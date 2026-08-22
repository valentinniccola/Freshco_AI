import sys
import unittest
import requests
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import User, PredictionRecord, AdminLog, AgentRecipeLog
from auth import get_password_hash, create_access_token

BASE_URL = "http://127.0.0.1:8000"

class TestAdminAndAgentFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db = SessionLocal()
        # Clean existing test users
        db.query(User).filter(User.username.in_(["test_admin", "test_regular_user", "test_suspended_user"])).delete(synchronize_session=False)
        db.commit()

        cls.admin_user = User(
            username="test_admin",
            email="admin_test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            role="admin",
            is_active=True
        )
        cls.regular_user = User(
            username="test_regular_user",
            email="regular_test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            role="user",
            is_active=True
        )
        cls.suspended_user = User(
            username="test_suspended_user",
            email="suspended_test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            role="user",
            is_active=False
        )
        db.add_all([cls.admin_user, cls.regular_user, cls.suspended_user])
        db.commit()
        db.refresh(cls.admin_user)
        db.refresh(cls.regular_user)
        db.refresh(cls.suspended_user)

        # Add sample scans for the regular user
        scan1 = PredictionRecord(
            user_id=cls.regular_user.id,
            image_path="/static/samples/banana_spotted.jpg",
            original_filename="banana_1.jpg",
            food_category="Fruit",
            freshness_status="Nearly Spoiled",
            confidence_score=0.92,
            probabilities_json='{"Fresh": 0.05, "Nearly Spoiled": 0.92, "Spoiled": 0.03}',
            shelf_life_days=2,
            defect_metrics_json='{"food_type": "Banana"}'
        )
        scan2 = PredictionRecord(
            user_id=cls.regular_user.id,
            image_path="/static/samples/apple_fresh.jpg",
            original_filename="apple_1.jpg",
            food_category="Fruit",
            freshness_status="Nearly Spoiled",
            confidence_score=0.88,
            probabilities_json='{"Fresh": 0.10, "Nearly Spoiled": 0.88, "Spoiled": 0.02}',
            shelf_life_days=1,
            defect_metrics_json='{"food_type": "Apple"}'
        )
        db.add_all([scan1, scan2])
        db.commit()

        cls.admin_token = create_access_token({"sub": str(cls.admin_user.id), "username": cls.admin_user.username, "role": "admin"})
        cls.regular_token = create_access_token({"sub": str(cls.regular_user.id), "username": cls.regular_user.username, "role": "user"})
        cls.suspended_token = create_access_token({"sub": str(cls.suspended_user.id), "username": cls.suspended_user.username, "role": "user"})

        db.close()

    def test_01_non_admin_forbidden(self):
        """Regular user must receive 403 Forbidden on admin endpoints"""
        headers = {"Authorization": f"Bearer {self.regular_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        self.assertEqual(res.status_code, 403, "Non-admin user should get 403 Forbidden")
        self.assertIn("Administrator privileges required", res.json()["detail"])

    def test_02_admin_get_stats(self):
        """Admin can access platform stats"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_users", data)
        self.assertIn("total_scans_platform", data)
        self.assertIn("platform_fresh_pct", data)

    def test_03_admin_get_users(self):
        """Admin can list all registered users without exposing passwords"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        self.assertEqual(res.status_code, 200)
        users = res.json()
        self.assertGreater(len(users), 0)
        for u in users:
            self.assertNotIn("hashed_password", u)
            self.assertIn("role", u)
            self.assertIn("is_active", u)
            self.assertIn("total_scans", u)

    def test_04_admin_get_user_detail(self):
        """Admin can view detailed history and scans for a user"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/users/{self.regular_user.id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["id"], self.regular_user.id)
        self.assertGreaterEqual(len(data["scans"]), 2)

    def test_05_admin_toggle_user_status_and_audit_log(self):
        """Admin can disable a user account and an audit log entry is created"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = requests.patch(
            f"{BASE_URL}/api/admin/users/{self.regular_user.id}/status",
            json={"is_active": False, "reason": "Test suspension"},
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["is_active"], False)

        # Check audit log
        logs_res = requests.get(f"{BASE_URL}/api/admin/logs", headers=headers)
        self.assertEqual(logs_res.status_code, 200)
        logs = logs_res.json()
        self.assertTrue(any(l["action"] == "DISABLE_USER" and l["target_user_id"] == self.regular_user.id for l in logs))

        # Re-enable user
        res_enable = requests.patch(
            f"{BASE_URL}/api/admin/users/{self.regular_user.id}/status",
            json={"is_active": True, "reason": "Re-activation"},
            headers=headers
        )
        self.assertEqual(res_enable.status_code, 200)
        self.assertEqual(res_enable.json()["is_active"], True)

    def test_06_agentic_multi_item_recipe_suggestion(self):
        """Agentic recipe endpoint synthesizes multi-item zero-waste recipe"""
        headers = {"Authorization": f"Bearer {self.regular_token}"}
        res = requests.post(f"{BASE_URL}/api/agent/recipe-suggestion?days=7", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recipe_title", data)
        self.assertIn("used_ingredients", data)
        self.assertIn("instructions", data)
        self.assertIn("chef_zero_waste_tip", data)
        self.assertTrue(data.get("is_agentic", False))

if __name__ == "__main__":
    unittest.main()
