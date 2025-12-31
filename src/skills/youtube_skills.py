"""YouTube 관련 스킬"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import YouTubeUploadResult
from src.repository import YouTubeUploadRepository
from src.skills.base import BaseSkill, SkillResult
from src.youtube_uploader import YouTubeUploader


class UploadVideoSkill(BaseSkill):
    """YouTube 영상 업로드 스킬"""

    name = "upload_video"
    description = "Upload a video to YouTube"

    def __init__(self, uploader: YouTubeUploader | None = None):
        self.uploader = uploader or YouTubeUploader()

    async def execute(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy_status: str = "public",
        **kwargs: Any,
    ) -> SkillResult[YouTubeUploadResult]:
        """YouTube에 영상 업로드"""
        try:
            result = await self.uploader.upload(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                is_shorts=True,
            )
            return SkillResult.success(result)
        except Exception as e:
            return SkillResult.failed(f"Upload failed: {e}")


class GetVideoInfoSkill(BaseSkill):
    """YouTube 영상 정보 조회 스킬"""

    name = "get_video_info"
    description = "Get video information from YouTube"

    def __init__(self, uploader: YouTubeUploader | None = None):
        self.uploader = uploader or YouTubeUploader()

    async def execute(self, video_id: str, **kwargs: Any) -> SkillResult[dict]:
        """YouTube 영상 정보 조회"""
        try:
            info = await self.uploader.get_video_info(video_id)
            return SkillResult.success(info)
        except Exception as e:
            return SkillResult.failed(f"Failed to get video info: {e}")


class SaveYouTubeUploadSkill(BaseSkill):
    """YouTube 업로드 기록 저장 스킬"""

    name = "save_youtube_upload"
    description = "Save YouTube upload record to database"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        story_id: int,
        video_id: str,
        video_url: str,
        title: str,
        video_generation_id: int | None = None,
        privacy_status: str = "public",
        **kwargs: Any,
    ) -> SkillResult[int]:
        """업로드 기록 저장"""
        try:
            repo = YouTubeUploadRepository(self.db_session)
            record = await repo.create(
                story_id=story_id,
                video_id=video_id,
                video_url=video_url,
                title=title,
                video_generation_id=video_generation_id,
                privacy_status=privacy_status,
            )
            await self.db_session.commit()
            return SkillResult.success(record.id)
        except Exception as e:
            await self.db_session.rollback()
            return SkillResult.failed(f"Failed to save upload record: {e}")
