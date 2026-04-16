from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AccountsAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.signup_url = reverse("signup")
        self.nickname_check_url = reverse("check-nickname")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.token_refresh_url = reverse("token-refresh")
        self.change_password_url = reverse("change-password")

        self.password = "testpass123!"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.password,
            nickname="tester",
            profile_image="avatar_1",
        )

    def test_signup_success(self) -> None:
        payload = {
            "email": "newuser@example.com",
            "password": "newpass123!",
            "nickname": "newtester",
            "profile_image": "avatar_1",
            "email_token": "verified-email-token",
        }

        response = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"detail": "회원가입이 완료되었습니다."})
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_signup_duplicate_email(self) -> None:
        payload = {
            "email": "test@example.com",
            "password": "newpass123!",
            "nickname": "anothernick",
            "profile_image": "avatar_1",
            "email_token": "verified-email-token",
        }

        response = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json(),
            {"error_detail": {"email": ["이미 가입된 이메일입니다."]}},
        )

    def test_signup_duplicate_nickname(self) -> None:
        payload = {
            "email": "another@example.com",
            "password": "newpass123!",
            "nickname": "tester",
            "profile_image": "avatar_1",
            "email_token": "verified-email-token",
        }

        response = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json(),
            {"error_detail": {"nickname": ["이미 사용 중인 닉네임입니다."]}},
        )

    def test_check_nickname_success(self) -> None:
        response = self.client.get(
            self.nickname_check_url,
            {"nickname": "available_nick"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"detail": "사용가능한 닉네임입니다."})

    def test_check_nickname_conflict(self) -> None:
        response = self.client.get(self.nickname_check_url, {"nickname": "tester"})

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.json(),
            {"error_detail": {"nickname": ["이미 사용 중인 닉네임입니다."]}},
        )

    def test_login_success(self) -> None:
        payload = {
            "email": "test@example.com",
            "password": self.password,
        }

        response = self.client.post(self.login_url, payload, format="json")
        body = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", body)
        self.assertNotIn("refresh_token", body)
        self.assertIn("refresh_token", response.cookies)

    def test_login_fail_invalid_password(self) -> None:
        payload = {
            "email": "test@example.com",
            "password": "wrong-password",
        }

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {"error_detail": "이메일 또는 비밀번호가 올바르지 않습니다."},
        )

    def test_token_refresh_success(self) -> None:
        login_response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": self.password},
            format="json",
        )
        refresh_token = login_response.cookies["refresh_token"].value

        response = self.client.post(
            self.token_refresh_url,
            {"refresh_token": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.json())

    def test_token_refresh_fail_missing_token(self) -> None:
        response = self.client.post(self.token_refresh_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"error_detail": {"refresh_token": ["이 필드는 필수 항목입니다."]}},
        )

    def test_logout_success(self) -> None:
        login_response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": self.password},
            format="json",
        )
        refresh_token = login_response.cookies["refresh_token"].value

        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"detail": "로그아웃 되었습니다."})

    def test_logout_success_without_cookie(self) -> None:
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"detail": "로그아웃 되었습니다."})

    def test_change_password_success(self) -> None:
        login_response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": self.password},
            format="json",
        )
        access_token = login_response.json()["access_token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        payload = {
            "password": self.password,
            "new_password": "changedpass123!",
            "new_password_confirm": "changedpass123!",
        }

        response = self.client.patch(self.change_password_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"detail": "비밀번호가 변경되었습니다."})

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("changedpass123!"))

    def test_change_password_fail_wrong_current_password(self) -> None:
        login_response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": self.password},
            format="json",
        )
        access_token = login_response.json()["access_token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        payload = {
            "password": "wrong-password",
            "new_password": "changedpass123!",
            "new_password_confirm": "changedpass123!",
        }

        response = self.client.patch(self.change_password_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json(),
            {"error_detail": "기존 비밀번호가 일치하지 않습니다."},
        )

    def test_change_password_fail_unauthorized(self) -> None:
        payload = {
            "password": self.password,
            "new_password": "changedpass123!",
            "new_password_confirm": "changedpass123!",
        }

        response = self.client.patch(self.change_password_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_fail_password_confirm_mismatch(self) -> None:
        login_response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": self.password},
            format="json",
        )
        access_token = login_response.json()["access_token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        payload = {
            "password": self.password,
            "new_password": "changedpass123!",
            "new_password_confirm": "differentpass123!",
        }

        response = self.client.patch(self.change_password_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"error_detail": {"new_password_confirm": ["비밀번호가 일치하지 않습니다."]}},
        )
