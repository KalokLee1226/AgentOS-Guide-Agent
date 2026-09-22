import unittest

from fastapi.testclient import TestClient

from api_server import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_does_not_require_api_key(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "0.2.0")

    def test_voice_request_is_validated(self):
        response = self.client.post(
            "/v1/voice/transcripts",
            json={"transcript": ""},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
