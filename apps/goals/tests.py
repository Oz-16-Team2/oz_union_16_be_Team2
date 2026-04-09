from django.test import TestCase


class HealthCheckTest(TestCase):
    def test_swagger_returns_200(self) -> None:
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)

    def test_schema_returns_200(self) -> None:
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)

    def test_admin_redirects(self) -> None:
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
