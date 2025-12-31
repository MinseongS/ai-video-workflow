"""YouTube API를 사용한 영상 업로드"""

import asyncio

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import settings
from src.models import YouTubeUploadResult

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


class YouTubeUploader:
    """YouTube API를 사용하여 영상을 업로드하는 클래스"""

    def __init__(self):
        self.credentials: Credentials | None = None
        self.youtube = None

        if settings.youtube_refresh_token:
            try:
                self._init_client()
            except Exception as e:
                print(f"[YouTubeUploader] 초기화 실패 (나중에 재시도): {e}")

    def _init_client(self) -> None:
        """YouTube API 클라이언트 초기화"""
        self.credentials = Credentials(
            token=None,
            refresh_token=settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
        )
        self.credentials.refresh(Request())
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def get_auth_url(self) -> str:
        """OAuth 인증 URL 생성"""
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.youtube_client_id,
                    "client_secret": settings.youtube_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            SCOPES,
        )
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        return auth_url

    def exchange_code(self, code: str) -> dict:
        """인증 코드로 토큰 교환"""
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.youtube_client_id,
                    "client_secret": settings.youtube_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            SCOPES,
        )
        flow.fetch_token(code=code)
        self.credentials = flow.credentials
        self.youtube = build("youtube", "v3", credentials=self.credentials)

        return {
            "access_token": self.credentials.token,
            "refresh_token": self.credentials.refresh_token,
        }

    async def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        *,
        privacy_status: str = "public",
        is_shorts: bool = True,
    ) -> YouTubeUploadResult:
        """영상을 YouTube에 업로드"""
        if not self.youtube:
            raise RuntimeError("YouTube API 클라이언트가 초기화되지 않았습니다.")

        if is_shorts:
            title = f"{title} #Shorts"
            tags = (tags or []) + ["Shorts", "쇼츠"]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": "24",  # Entertainment
                "defaultLanguage": "ko",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        def _do_upload():
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"업로드 진행률: {int(status.progress() * 100)}%")
            return response

        response = await asyncio.to_thread(_do_upload)

        return YouTubeUploadResult(
            video_id=response["id"],
            url=f"https://www.youtube.com/watch?v={response['id']}",
            title=response["snippet"]["title"],
        )

    async def get_video_info(self, video_id: str) -> dict:
        """업로드된 영상 정보 조회"""
        if not self.youtube:
            raise RuntimeError("YouTube API 클라이언트가 초기화되지 않았습니다.")

        def _get():
            return (
                self.youtube.videos()
                .list(
                    part="snippet,statistics",
                    id=video_id,
                )
                .execute()
            )

        response = await asyncio.to_thread(_get)
        return response["items"][0] if response.get("items") else {}
