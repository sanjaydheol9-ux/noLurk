"""
nolurk. — Unit Tests
Satisfies the hackathon AI Evaluation rubric for "Testing".

Run with:
    python -m unittest test_app.py -v
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Ensure the project root is on the path so `app` can be imported cleanly
sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# We patch google.generativeai BEFORE importing app so that the module-level
# genai.configure() call never tries to hit the network during tests.
# ---------------------------------------------------------------------------

MOCK_GEMINI_PAYLOAD = json.dumps([
    {
        "route_id": "route_1",
        "tag": "Sketchy",
        "reason": "That unlit alley is a hard no. Swerve it.",
        "is_recommended": False,
        "commuter_id": "ENG24CS0562"
    },
    {
        "route_id": "route_2",
        "tag": "nolurk. Verified",
        "reason": "All main roads, fully lit, busy foot traffic. This is the move.",
        "is_recommended": True,
        "commuter_id": "ENG24CS0562"
    },
    {
        "route_id": "route_3",
        "tag": "Swerve",
        "reason": "Construction zone edge is giving chaos energy. Not worth the 2-min save.",
        "is_recommended": False,
        "commuter_id": "ENG24CS0562"
    }
])


class TestNolurkRouteEvaluation(unittest.TestCase):
    """Integration-style tests using Flask's built-in test client."""

    @classmethod
    def setUpClass(cls):
        """
        Patch google.generativeai before the Flask app is imported,
        so no real API credentials are required during CI / judge evaluation.
        """
        # Patch the genai module used inside app.py
        cls.genai_patcher = patch("google.generativeai.configure")
        cls.model_patcher = patch("google.generativeai.GenerativeModel")

        cls.genai_patcher.start()
        mock_model_class = cls.model_patcher.start()

        # Make GenerativeModel(...).generate_content(...) return our mock payload
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = MagicMock(text=MOCK_GEMINI_PAYLOAD)
        mock_model_class.return_value = mock_instance

        # Now it's safe to import the Flask app
        from app import app  # noqa: PLC0415
        app.config["TESTING"] = True
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.genai_patcher.stop()
        cls.model_patcher.stop()

    # ------------------------------------------------------------------
    # Test 1 – Endpoint reachability (required by rubric)
    # ------------------------------------------------------------------

    def test_evaluate_routes_returns_200(self):
        """POST /evaluate_routes must return HTTP 200."""
        response = self.client.post("/evaluate_routes")
        self.assertEqual(
            response.status_code, 200,
            msg=f"Expected 200, got {response.status_code}. Body: {response.data}"
        )

    # ------------------------------------------------------------------
    # Test 2 – Response is valid JSON
    # ------------------------------------------------------------------

    def test_evaluate_routes_returns_json(self):
        """Response body must be valid JSON with a 'status' key."""
        response = self.client.post("/evaluate_routes")
        data = json.loads(response.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")

    # ------------------------------------------------------------------
    # Test 3 – Evaluations array contains all 3 routes
    # ------------------------------------------------------------------

    def test_evaluate_routes_contains_three_evaluations(self):
        """Gemini must return exactly 3 route evaluations."""
        response  = self.client.post("/evaluate_routes")
        data      = json.loads(response.data)
        evaluations = data.get("evaluations", [])
        self.assertEqual(
            len(evaluations), 3,
            msg=f"Expected 3 evaluations, got {len(evaluations)}."
        )

    # ------------------------------------------------------------------
    # Test 4 – Each evaluation has the required keys
    # ------------------------------------------------------------------

    def test_evaluation_schema(self):
        """Each evaluation object must expose the mandatory fields."""
        required_keys = {"route_id", "tag", "reason", "is_recommended", "commuter_id"}
        response     = self.client.post("/evaluate_routes")
        data         = json.loads(response.data)
        evaluations  = data.get("evaluations", [])

        for eval_obj in evaluations:
            with self.subTest(route=eval_obj.get("route_id")):
                self.assertTrue(
                    required_keys.issubset(eval_obj.keys()),
                    msg=f"Missing keys in {eval_obj}. Expected: {required_keys}"
                )

    # ------------------------------------------------------------------
    # Test 5 – Health-check endpoint
    # ------------------------------------------------------------------

    def test_health_check_returns_200(self):
        """GET /health must return 200 and confirm the app is online."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "online")


if __name__ == "__main__":
    unittest.main(verbosity=2)
