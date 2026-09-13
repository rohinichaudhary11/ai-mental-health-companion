"""
Fast, robust unit and integration tests for Mental Health Companion API endpoints.
"""

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.api.main import app


class TestMentalHealthAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._client_ctx.__exit__(None, None, None)

    def test_01_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("endpoints", data)

    def test_02_healthcheck(self):
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("model_loaded", data)
        self.assertTrue(data["model_loaded"])

    def test_03_predict_success(self):
        response = self.client.post("/predict", json={"text": "I feel so happy and excited today!"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["emotion"], "joy")
        self.assertGreaterEqual(data["confidence"], 0.0)
        self.assertIn("recommendation", data)

    def test_04_predict_short_text(self):
        response = self.client.post("/predict", json={"text": "hi"})
        self.assertEqual(response.status_code, 400)

    def test_05_predict_batch(self):
        response = self.client.post("/predict/batch", json=[
            "I feel so overwhelmed and stressed with work",
            "I am terrified of what might happen",
        ])
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)

    def test_06_chat_endpoint(self):
        response = self.client.post("/api/chat", json={
            "message": "I am feeling really anxious about my exams tomorrow."
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("reply", data)
        self.assertIn("cbt_techniques", data)

    @patch("src.api.routers.medical.lookup_ip_location", return_value=None)
    def test_07_symptom_support(self, mock_ip):
        response = self.client.post("/api/symptom-support", json={
            "text": "My chest feels tight and my heart is racing and I feel dizzy"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detected_conditions", data)
        self.assertIn("coping_techniques", data)
        self.assertIn("disclaimer", data)

    def test_08_mood_log(self):
        response = self.client.post("/api/mood-log", json={
            "mood": "high",
            "emoji": "😊",
            "note": "Great day today!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

        # Fetch mood logs
        get_resp = self.client.get("/api/mood-log")
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn("items", get_resp.json())

    def test_09_journal(self):
        response = self.client.post("/api/journal", json={
            "content": "Today was a quiet day. I felt peaceful and relaxed taking a walk in the park."
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("dominant_emotions", data)
        self.assertIn("summary", data)

    def test_10_analytics(self):
        response = self.client.get("/api/emotion-analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("top_emotions", data)


if __name__ == "__main__":
    unittest.main()
