from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from clipster.models import Clip


class ApiTests(TestCase):
    def setUp(self):
        cache.clear()
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

    def test_register_has_no_server_side_password_rules(self):
        resp = self.client.post("/register/", {"username": "bob", "password": "x"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(User.objects.get(username="bob").check_password("x"))

    def test_register_rejects_missing_fields(self):
        resp = self.client.post("/register/", {"username": "bob"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())
        resp = self.client.post("/register/", ["not", "a", "dict"], format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_anonymous_api_access_is_denied(self):
        self.assertEqual(self.client.get("/copy-paste/").status_code, 403)
        self.assertEqual(self.client.post("/copy-paste/", {"text": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/", {"text": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/verify-user/").status_code, 403)
        self.assertFalse(Clip.objects.exists())

    def test_verify_user_rejects_wrong_password(self):
        User.objects.create_user("alice", password="a-long-password")
        self.client.credentials(HTTP_AUTHORIZATION="Basic YWxpY2U6d3Jvbmc=")
        self.assertIn(self.client.get("/verify-user/").status_code, (401, 403))

    def test_basic_auth_is_rate_limited(self):
        User.objects.create_user("alice", password="a-long-password")
        self.client.credentials(HTTP_AUTHORIZATION="Basic YWxpY2U6d3Jvbmc=")
        for _ in range(settings.LOGIN_FAILURE_LIMIT):
            self.client.get("/verify-user/")
        self.client.credentials(HTTP_AUTHORIZATION="Basic YWxpY2U6YS1sb25nLXBhc3N3b3Jk")
        self.assertIn(self.client.get("/verify-user/").status_code, (401, 403))
        cache.clear()
        self.assertEqual(self.client.get("/verify-user/").status_code, 200)

    def test_copy_paste_only_returns_own_clips(self):
        alice = User.objects.create_user("alice", password="a-long-password")
        other = User.objects.create_user("bob", password="a-long-password")
        Clip.objects.create(user=other, text="not yours")
        self.client.force_authenticate(alice)
        self.assertEqual(self.client.get("/copy-paste/").json(), [])

    def test_old_clips_are_removed(self):
        user = User.objects.create_user("carol", password="a-long-password")
        for i in range(settings.MAX_CLIPS_PER_USER + 3):
            Clip.objects.create(user=user, text=str(i))
        texts = list(Clip.objects.filter(user=user).values_list("text", flat=True))
        self.assertEqual(texts, [str(i) for i in range(3, settings.MAX_CLIPS_PER_USER + 3)])


class FrontendTests(TestCase):
    def setUp(self):
        cache.clear()

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

    def test_anonymous_cannot_share_clip(self):
        victim = User.objects.create_user("erin", password="a-long-password")
        Clip.objects.create(user=victim, text="keep")
        resp = self.client.post(
            "/share-clip/", {"user": victim.id, "text": "injected", "device": "x", "format": "txt"}
        )
        self.assertRedirects(resp, "/api-auth/login/", fetch_redirect_response=False)
        self.assertEqual(list(Clip.objects.values_list("text", flat=True)), ["keep"])

    def test_share_clip_ignores_submitted_user(self):
        victim = User.objects.create_user("frank", password="a-long-password")
        sharer = User.objects.create_user("grace", password="a-long-password")
        self.client.force_login(sharer)
        resp = self.client.post(
            "/share-clip/", {"user": victim.id, "text": "mine", "device": "x", "format": "txt"}
        )
        self.assertRedirects(resp, "/", fetch_redirect_response=False)
        self.assertFalse(Clip.objects.filter(user=victim).exists())
        self.assertEqual(Clip.objects.get(user=sharer).text, "mine")

    def test_login_is_rate_limited(self):
        User.objects.create_user("heidi", password="a-long-password")
        for _ in range(settings.LOGIN_FAILURE_LIMIT):
            resp = self.client.post("/api-auth/login/", {"username": "heidi", "password": "wrong"})
            self.assertNotContains(resp, "Too many failed login attempts")
        resp = self.client.post("/api-auth/login/", {"username": "heidi", "password": "a-long-password"})
        self.assertContains(resp, "Too many failed login attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rate_limit_uses_last_proxy_address(self):
        User.objects.create_user("ivan", password="a-long-password")
        for i in range(settings.LOGIN_FAILURE_LIMIT + 1):
            resp = self.client.post(
                "/api-auth/login/",
                {"username": "ivan", "password": "wrong"},
                HTTP_X_FORWARDED_FOR=f"10.0.0.{i}, 203.0.113.7",
            )
        self.assertContains(resp, "Too many failed login attempts")

    def test_successful_logins_are_not_limited(self):
        User.objects.create_user("judy", password="a-long-password")
        for _ in range(settings.LOGIN_FAILURE_LIMIT + 1):
            resp = self.client.post("/api-auth/login/", {"username": "judy", "password": "a-long-password"})
            self.assertRedirects(resp, "/accounts/profile/", fetch_redirect_response=False)

    def test_admin_login_is_rate_limited(self):
        User.objects.create_superuser("admin", password="a-long-admin-password")
        for _ in range(settings.LOGIN_FAILURE_LIMIT):
            self.client.post("/admin/login/", {"username": "admin", "password": "wrong"})
        resp = self.client.post("/admin/login/", {"username": "admin", "password": "a-long-admin-password"})
        self.assertContains(resp, "Too many failed login attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_login_works(self):
        User.objects.create_superuser("admin", password="a-long-admin-password")
        resp = self.client.post(
            "/admin/login/", {"username": "admin", "password": "a-long-admin-password", "next": "/admin/"}
        )
        self.assertRedirects(resp, "/admin/")

    def test_failures_on_one_path_count_for_all(self):
        User.objects.create_superuser("admin", password="a-long-admin-password")
        api = APIClient(HTTP_ACCEPT="application/json")
        api.credentials(HTTP_AUTHORIZATION="Basic YWRtaW46d3Jvbmc=")
        for _ in range(settings.LOGIN_FAILURE_LIMIT):
            api.get("/verify-user/")
        resp = self.client.post("/admin/login/", {"username": "admin", "password": "a-long-admin-password"})
        self.assertContains(resp, "Too many failed login attempts")

    def test_admin_passwords_must_be_strong(self):
        with self.assertRaises(ValidationError):
            validate_password("short")
        with self.assertRaises(ValidationError):
            validate_password("password1234")
        # What clients send instead of the password
        validate_password("q2Pt2r6Ux3ZPFa0Ts1n1Jj0U5Y9k3w2XoE5oQe8V1yI=")

    def test_https_hardening(self):
        user = User.objects.create_user("mallory", password="a-long-password")
        self.client.force_login(user)
        resp = self.client.get("/share-clip/", secure=True)
        self.assertIn("max-age=31536000", resp["Strict-Transport-Security"])
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME]["secure"])
        self.assertTrue(resp.cookies[settings.CSRF_COOKIE_NAME]["secure"])
