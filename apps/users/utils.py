from typing import Any

from apps.users.constants import PROFILE_IMAGE_URL_MAP


def get_user_display_info(user: Any) -> tuple[str, str]:
    is_general_user = user.has_usable_password()

    if is_general_user:
        display_nickname = user.nickname
        display_profile_url = PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")
        return display_nickname, display_profile_url

    social_logins = list(user.social_logins.all())
    social_info = social_logins[0] if social_logins else None

    display_nickname = user.nickname
    display_profile_url = PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")

    if social_info:
        if social_info.social_nickname:
            display_nickname = social_info.social_nickname
        if social_info.social_profile_image_url:
            display_profile_url = social_info.social_profile_image_url

    elif getattr(user, "social_profile_image_url", None):
        display_profile_url = user.social_profile_image_url

    return display_nickname, display_profile_url
