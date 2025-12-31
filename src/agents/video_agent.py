"""Video generation agent for AI Video Workflow."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import BaseAgent
from src.skills.video_skills import (
    GenerateVideoSequenceSkill,
    GenerateVideoSkill,
    MergeVideosSkill,
    SaveVideoGenerationSkill,
    UpdateVideoGenerationSkill,
)
from src.video_generator import Veo3VideoGenerator


class VideoAgentResult(BaseModel):
    """Result of video agent execution."""

    video_path: str | None = None
    video_generation_id: int | None = None
    segment_count: int = 0
    success: bool = False
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True


class VideoAgent(BaseAgent):
    """Agent responsible for video generation and management."""

    name = "video_agent"
    description = "Generates videos using Veo3 API and manages video files"

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        video_generator: Veo3VideoGenerator | None = None,
    ):
        super().__init__(db_session)
        self.video_generator = video_generator or Veo3VideoGenerator()
        self._setup_skills()

    def _setup_skills(self) -> None:
        """Register skills for this agent."""
        self.register_skill(GenerateVideoSkill(self.video_generator))
        self.register_skill(GenerateVideoSequenceSkill(self.video_generator))
        self.register_skill(MergeVideosSkill(self.video_generator))
        if self.db_session:
            self.register_skill(SaveVideoGenerationSkill(self.db_session))
            self.register_skill(UpdateVideoGenerationSkill(self.db_session))

    async def generate_single_video(
        self,
        prompt: str,
        duration: int = 5,
    ) -> str | None:
        """Generate a single video from a prompt."""
        result = await self.execute_skill(
            "generate_video",
            prompt=prompt,
            duration=duration,
        )
        if result.is_success and result.data:
            return result.data.file_path
        return None

    async def generate_video_sequence(
        self,
        prompts: list[str],
        duration: int = 5,
        output_filename: str | None = None,
    ) -> str | None:
        """Generate a video sequence from multiple prompts."""
        if output_filename is None:
            output_filename = f"video_{int(datetime.now().timestamp())}.mp4"

        result = await self.execute_skill(
            "generate_video_sequence",
            prompts=prompts,
            duration=duration,
            output_filename=output_filename,
        )
        return result.data if result.is_success else None

    async def merge_videos(
        self,
        video_paths: list[str],
        output_filename: str,
    ) -> str | None:
        """Merge multiple videos into one."""
        result = await self.execute_skill(
            "merge_videos",
            video_paths=video_paths,
            output_filename=output_filename,
        )
        return result.data if result.is_success else None

    async def save_generation_record(
        self,
        story_id: int,
        status: str = "processing",
    ) -> int | None:
        """Save a video generation record to database."""
        if not self.db_session:
            return None

        result = await self.execute_skill(
            "save_video_generation",
            story_id=story_id,
            status=status,
        )
        return result.data if result.is_success else None

    async def update_generation_record(
        self,
        video_id: int,
        status: str | None = None,
        video_path: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Update a video generation record."""
        if not self.db_session:
            return False

        result = await self.execute_skill(
            "update_video_generation",
            video_id=video_id,
            status=status,
            video_path=video_path,
            error_message=error_message,
        )
        return result.is_success

    async def run(
        self,
        prompts: list[str],
        story_id: int | None = None,
        duration: int = 5,
        output_filename: str | None = None,
        **kwargs: Any,
    ) -> VideoAgentResult:
        """
        Run the video agent to generate videos from prompts.

        Args:
            prompts: List of video prompts.
            story_id: Associated story ID for database tracking.
            duration: Duration of each video segment in seconds.
            output_filename: Output filename for the merged video.

        Returns:
            VideoAgentResult with the generated video path.
        """
        video_generation_id = None

        try:
            # Create database record if story_id provided
            if story_id and self.db_session:
                video_generation_id = await self.save_generation_record(
                    story_id=story_id,
                    status="processing",
                )
                print(f"[VideoAgent] Created generation record: {video_generation_id}")

            print(f"[VideoAgent] Generating {len(prompts)} video segments...")

            # Generate video sequence
            if output_filename is None:
                output_filename = f"video_{int(datetime.now().timestamp())}.mp4"

            video_path = await self.generate_video_sequence(
                prompts=prompts,
                duration=duration,
                output_filename=output_filename,
            )

            if not video_path:
                error_msg = "Failed to generate video sequence"
                if video_generation_id:
                    await self.update_generation_record(
                        video_id=video_generation_id,
                        status="failed",
                        error_message=error_msg,
                    )
                return VideoAgentResult(
                    video_generation_id=video_generation_id,
                    segment_count=len(prompts),
                    success=False,
                    error=error_msg,
                )

            print(f"[VideoAgent] Generated video: {video_path}")

            # Update database record
            if video_generation_id:
                await self.update_generation_record(
                    video_id=video_generation_id,
                    status="completed",
                    video_path=video_path,
                )

            return VideoAgentResult(
                video_path=video_path,
                video_generation_id=video_generation_id,
                segment_count=len(prompts),
                success=True,
            )

        except Exception as e:
            error_msg = str(e)
            if video_generation_id:
                await self.update_generation_record(
                    video_id=video_generation_id,
                    status="failed",
                    error_message=error_msg,
                )
            return VideoAgentResult(
                video_generation_id=video_generation_id,
                segment_count=len(prompts),
                success=False,
                error=error_msg,
            )
