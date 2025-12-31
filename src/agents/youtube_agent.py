"""YouTube upload agent for AI Video Workflow."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import BaseAgent
from src.models import YouTubeUploadResult
from src.skills.youtube_skills import (
    GetVideoInfoSkill,
    SaveYouTubeUploadSkill,
    UploadVideoSkill,
)
from src.youtube_uploader import YouTubeUploader


class YouTubeAgentResult(BaseModel):
    """Result of YouTube agent execution."""

    video_id: str | None = None
    video_url: str | None = None
    upload_record_id: int | None = None
    success: bool = False
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True


class YouTubeAgent(BaseAgent):
    """Agent responsible for YouTube uploads and management."""

    name = "youtube_agent"
    description = "Uploads videos to YouTube and manages upload records"

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        youtube_uploader: YouTubeUploader | None = None,
    ):
        super().__init__(db_session)
        self.youtube_uploader = youtube_uploader or YouTubeUploader()
        self._setup_skills()

    def _setup_skills(self) -> None:
        """Register skills for this agent."""
        self.register_skill(UploadVideoSkill(self.youtube_uploader))
        self.register_skill(GetVideoInfoSkill(self.youtube_uploader))
        if self.db_session:
            self.register_skill(SaveYouTubeUploadSkill(self.db_session))

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy_status: str = "public",
    ) -> YouTubeUploadResult | None:
        """Upload a video to YouTube."""
        result = await self.execute_skill(
            "upload_video",
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
        )
        return result.data if result.is_success else None

    async def get_video_info(self, video_id: str) -> dict | None:
        """Get video information from YouTube."""
        result = await self.execute_skill("get_video_info", video_id=video_id)
        return result.data if result.is_success else None

    async def save_upload_record(
        self,
        story_id: int,
        video_id: str,
        video_url: str,
        title: str,
        video_generation_id: int | None = None,
        privacy_status: str = "public",
    ) -> int | None:
        """Save upload record to database."""
        if not self.db_session:
            return None

        result = await self.execute_skill(
            "save_youtube_upload",
            story_id=story_id,
            video_id=video_id,
            video_url=video_url,
            title=title,
            video_generation_id=video_generation_id,
            privacy_status=privacy_status,
        )
        return result.data if result.is_success else None

    async def run(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy_status: str = "public",
        story_id: int | None = None,
        video_generation_id: int | None = None,
        **kwargs: Any,
    ) -> YouTubeAgentResult:
        """
        Run the YouTube agent to upload a video.

        Args:
            video_path: Path to the video file.
            title: Video title.
            description: Video description.
            tags: Video tags.
            privacy_status: Privacy status (public, private, unlisted).
            story_id: Associated story ID for database tracking.
            video_generation_id: Associated video generation ID.

        Returns:
            YouTubeAgentResult with upload details.
        """
        try:
            print(f"[YouTubeAgent] Uploading video: {title}")

            # Upload to YouTube
            upload_result = await self.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
            )

            if not upload_result:
                return YouTubeAgentResult(
                    success=False,
                    error="Failed to upload video to YouTube",
                )

            print(f"[YouTubeAgent] Uploaded: {upload_result.url}")

            # Save to database
            upload_record_id = None
            if story_id and self.db_session:
                upload_record_id = await self.save_upload_record(
                    story_id=story_id,
                    video_id=upload_result.video_id,
                    video_url=upload_result.url,
                    title=upload_result.title,
                    video_generation_id=video_generation_id,
                    privacy_status=privacy_status,
                )
                if upload_record_id:
                    print(f"[YouTubeAgent] Saved upload record: {upload_record_id}")

            return YouTubeAgentResult(
                video_id=upload_result.video_id,
                video_url=upload_result.url,
                upload_record_id=upload_record_id,
                success=True,
            )

        except Exception as e:
            return YouTubeAgentResult(
                success=False,
                error=str(e),
            )
