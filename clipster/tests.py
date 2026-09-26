from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from clipster.models import Clip


@override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"anon": None, "user": None}})
class ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient(HTTP_ACCEPT="application/json")

    def test_register_verify_and_copy_paste(self):
        creds = {"username": "alice", "password": "a-long-password"}
        resp = self.client.post("/register/", creds, format="json")
        self.assertEqual(resp.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION="Basic YWxpY2U6YS1sb25nLXBhc3N3b3Jk")
        self.assertEqual(self.client.get("/verify-user/").status_code, 200)

        resp = self.client.post("/copy-paste/", {"text": "hello", "device": "test"}, format="json")
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/copy-paste/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["text"], "hello")

    def test_register_rejects_short_password(self):
        resp = self.client.post("/register/", {"username": "bob", "password": "x"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_old_clips_are_removed(self):
        user = User.objects.create_user("carol", password="a-long-password")
        for i in range(settings.MAX_CLIPS_PER_USER + 3):
            Clip.objects.create(user=user, text=str(i))
        texts = list(Clip.objects.filter(user=user).values_list("text", flat=True))
        self.assertEqual(texts, [str(i) for i in range(3, settings.MAX_CLIPS_PER_USER + 3)])


@override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"anon": None, "user": None}})
class FrontendTests(TestCase):
    def test_anonymous_pages(self):
        self.assertRedirects(self.client.get("/"), "/api-auth/login/")
        self.assertEqual(self.client.get("/api-auth/login/").status_code, 200)
        self.assertEqual(self.client.get("/register/").status_code, 200)

    def test_authenticated_pages_and_logout(self):
        user = User.objects.create_user("dave", password="a-long-password")
        Clip.objects.create(user=user, text="secret")
        self.client.force_login(user)

        resp = self.client.get("/")
        self.assertContains(resp, "secret")
        self.assertContains(resp, 'id="logoutForm"')
        self.assertEqual(self.client.get("/share-clip/").status_code, 200)

        self.client.post("/api-auth/logout/")
        self.assertRedirects(self.client.get("/"), "/api-auth/login/")
