"""Video-related skills for AI Video Workflow."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import VideoGenerationResult
from src.repository import VideoGenerationRepository
from src.skills.base import BaseSkill, SkillResult
from src.video_generator import Veo3VideoGenerator


class GenerateVideoSkill(BaseSkill):
    """Skill to generate a video using Veo3 API."""

    name = "generate_video"
    description = "Generate a video from a text prompt using Veo3 API"

    def __init__(self, video_generator: Veo3VideoGenerator | None = None):
        self.video_generator = video_generator or Veo3VideoGenerator()

    async def execute(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        **kwargs: Any,
    ) -> SkillResult[VideoGenerationResult]:
        """Generate a single video from a prompt."""
        try:
            result = await self.video_generator.generate_video(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
            )
            return SkillResult.success(result)
        except Exception as e:
            return SkillResult.failed(f"Video generation failed: {e}")


class GenerateVideoSequenceSkill(BaseSkill):
    """Skill to generate a sequence of videos from multiple prompts."""

    name = "generate_video_sequence"
    description = "Generate multiple videos from prompts and merge them"

    def __init__(self, video_generator: Veo3VideoGenerator | None = None):
        self.video_generator = video_generator or Veo3VideoGenerator()

    async def execute(
        self,
        prompts: list[str],
        duration: int = 5,
        output_filename: str | None = None,
        **kwargs: Any,
    ) -> SkillResult[str]:
        """Generate a video sequence from multiple prompts."""
        try:
            video_path = await self.video_generator.generate_video_sequence(
                prompts=prompts,
                duration=duration,
                output_filename=output_filename,
            )
            return SkillResult.success(video_path)
        except Exception as e:
            return SkillResult.failed(f"Video sequence generation failed: {e}")


class MergeVideosSkill(BaseSkill):
    """Skill to merge multiple videos into one."""

    name = "merge_videos"
    description = "Merge multiple video files into a single video"

    def __init__(self, video_generator: Veo3VideoGenerator | None = None):
        self.video_generator = video_generator or Veo3VideoGenerator()

    async def execute(
        self,
        video_paths: list[str],
        output_filename: str,
        **kwargs: Any,
    ) -> SkillResult[str]:
        """Merge multiple videos into one."""
        try:
            output_path = await self.video_generator.merge_videos(
                video_paths=video_paths,
                output_filename=output_filename,
            )
            return SkillResult.success(output_path)
        except Exception as e:
            return SkillResult.failed(f"Video merge failed: {e}")


class SaveVideoGenerationSkill(BaseSkill):
    """Skill to save video generation record to database."""

    name = "save_video_generation"
    description = "Save video generation record to database"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        story_id: int,
        status: str = "processing",
        video_path: str | None = None,
        segments: list[dict] | None = None,
        **kwargs: Any,
    ) -> SkillResult[int]:
        """Save a video generation record."""
        try:
            repo = VideoGenerationRepository(self.db_session)
            db_video = await repo.create(
                story_id=story_id,
                status=status,
                video_path=video_path,
                segments=segments,
            )
            await self.db_session.commit()
            return SkillResult.success(db_video.id)
        except Exception as e:
            await self.db_session.rollback()
            return SkillResult.failed(f"Failed to save video generation: {e}")


class UpdateVideoGenerationSkill(BaseSkill):
    """Skill to update video generation record in database."""

    name = "update_video_generation"
    description = "Update video generation record in database"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        video_id: int,
        status: str | None = None,
        video_path: str | None = None,
        error_message: str | None = None,
        **kwargs: Any,
    ) -> SkillResult[bool]:
        """Update a video generation record."""
        try:
            repo = VideoGenerationRepository(self.db_session)
            await repo.update(
                video_id=video_id,
                status=status,
                video_path=video_path,
                error_message=error_message,
            )
            await self.db_session.commit()
            return SkillResult.success(True)
        except Exception as e:
            await self.db_session.rollback()
            return SkillResult.failed(f"Failed to update video generation: {e}")
