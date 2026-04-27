from __future__ import annotations

import uuid

import boto3
from botocore.config import Config
from django.conf import settings
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import parsers, status
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import detail_response, error_response
from apps.goals.serializers.goal_create import ErrorDetailSerializer

TAG_POSTS = "Posts"


class PresignedUrlAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    ALLOWED_TYPES: dict[str, str] = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
    }

    @extend_schema(
        tags=[TAG_POSTS],
        summary="이미지 업로드용 URL 발급",
        description="AWS S3에 이미지를 직접 업로드 하기 위한 Presigned URL을 발급합니다.\n\n"
        "1. 이 API로 presigned_url 발급\n"
        "2. 발급받은 presigned_url로 PUT 요청하여 S3에 직접 업로드\n"
        "3. 반환된 image_url을 게시글 작성 시 사용",
        request=inline_serializer(
            name="PresignedUrlRequest",
            fields={
                "filename": drf_serializers.CharField(help_text="업로드할 파일명 (예: image.jpg)"),
                "content_type": drf_serializers.CharField(
                    help_text="파일 MIME 타입 (예: image/jpeg, image/png, image/gif, image/webp)"
                ),
            },
        ),
        responses={
            200: dict,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            500: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "요청 예시",
                value={"filename": "image.jpg", "content_type": "image/jpeg"},
                request_only=True,
            ),
            OpenApiExample(
                "200 OK",
                value={
                    "presigned_url": "https://jaksim-image-bucket-1.s3.amazonaws.com/...",
                    "image_url": "https://jaksim-image-bucket-1.s3.amazonaws.com/post_images/image.jpg",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "400 잘못된 파일 형식",
                value={"error_detail": {"filename": ["허용되지 않는 파일 형식입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        original_filename = request.data.get("filename", "")
        content_type = request.data.get("content_type", "")

        if not original_filename:
            return error_response({"filename": ["파일명은 필수입니다."]}, status.HTTP_400_BAD_REQUEST)

        if not content_type:
            return error_response({"content_type": ["content_type은 필수입니다."]}, status.HTTP_400_BAD_REQUEST)

        if content_type not in self.ALLOWED_TYPES:
            return error_response(
                {
                    "content_type": [
                        "허용되지 않는 파일 형식입니다. (image/jpeg, image/png, image/gif, image/webp 만 허용)"
                    ]
                },
                status.HTTP_400_BAD_REQUEST,
            )

        ext = self.ALLOWED_TYPES[content_type]
        unique_filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"post_images/{unique_filename}"

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

        try:
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "Key": file_path,
                    "ContentType": content_type,
                },
                ExpiresIn=300,
            )

            image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"

            return detail_response({"presigned_url": presigned_url, "image_url": image_url}, status.HTTP_200_OK)

        except Exception as e:
            return error_response({"server_error": [str(e)]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
