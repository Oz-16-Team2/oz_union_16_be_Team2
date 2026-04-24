from apps.core.choices import ProfileImageCode

PROFILE_IMAGE_URL_MAP: dict[str, str] = {
    ProfileImageCode.AVATAR_01.value: "https://jaksim-image-bucket-1.s3.ap-northeast-2.amazonaws.com/post_images/528f6967-3e29-4309-b57b-2c3ff3457794.png",
    ProfileImageCode.AVATAR_02.value: "https://jaksim-image-bucket-1.s3.ap-northeast-2.amazonaws.com/post_images/1faf9b4d-9a60-4fe2-9fe2-72e288cb4c65.png",
    ProfileImageCode.AVATAR_03.value: "https://jaksim-image-bucket-1.s3.ap-northeast-2.amazonaws.com/post_images/a169e590-203a-4ad6-a2bf-4bb05c73e4a2.png",
    ProfileImageCode.AVATAR_04.value: "https://jaksim-image-bucket-1.s3.ap-northeast-2.amazonaws.com/post_images/9b63cb03-9236-417f-99dc-9e69ce455f17.png",
}
