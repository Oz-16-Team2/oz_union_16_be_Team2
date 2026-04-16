import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """
    DRF API 요청을 위한 클라이언트 픽스처입니다.
    모든 API 테스트에서 인자로 주입받아 사용할 수 있습니다.
    """
    return APIClient()


# @pytest.fixture
# def test_user(db: Any) -> User:
#     """
#     테스트용 유저를 생성하는 픽스처입니다.
#     db 인자를 통해 데이터베이스 접근 권한을 가집니다.
#     """
#     return User.objects.create_user(email="testtest@test.com", nickname="testuser00", password="password123")


# @pytest.fixture
# def test_post(db: Any, test_user: User) -> Post:
#     """
#     테스트용 게시글을 생성하는 픽스처입니다.
#     이미 생성된 test_user 픽스처를 주입받아 관계를 맺습니다.
#     """
#     post = Post.objects.create(user_id=test_user.id)
#     return post


"""
  File "/app/apps/users/views.py", line 87, in post
    result = signup_user(**serializer.validated_data)
  File "/app/apps/users/services.py", line 34, in signup_user
    raise ConflictException(errors)
apps.core.exceptions.ConflictException: {'nickname': ['이미 사용 중인 닉네임입니다.']}
============================================================= short test summary info =============================================================
FAILED apps/users/tests.py::AccountsAPITestCase::test_check_nickname_conflict - apps.core.exceptions.ConflictException: {'nickname': ['이미 사용 중인 닉네임입니다.']}
FAILED apps/users/tests.py::AccountsAPITestCase::test_signup_duplicate_email - apps.core.exceptions.ConflictException: {'email': ['이미 가입된 이메일입니다.']}
FAILED apps/users/tests.py::AccountsAPITestCase::test_signup_duplicate_nickname - apps.core.exceptions.ConflictException: {'nickname': ['이미 사용 중인 닉네임입니다.']}
위 테스트들이 409 CONFLICT 응답을 기대하지만 exception handler가 ConflictException 을 못잡고 그대로 던져서 테스트 프로세스 중단
"""
