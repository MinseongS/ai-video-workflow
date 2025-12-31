"""Project management skills for AI Video Workflow."""

import subprocess
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db_models import StoryHistory, VideoGeneration, WorkflowExecution, YouTubeUpload
from src.skills.base import BaseSkill, SkillResult


class ProjectStatus(BaseModel):
    """Project status information."""

    total_episodes: int = 0
    total_videos: int = 0
    total_uploads: int = 0
    last_execution: str | None = None
    last_execution_status: str | None = None
    database_connected: bool = False
    api_keys_configured: dict[str, bool] = {}


class WorkflowRunResult(BaseModel):
    """Result of workflow execution."""

    success: bool
    episode: int | None = None
    video_url: str | None = None
    error: str | None = None
    duration_seconds: float | None = None


class CheckProjectStatusSkill(BaseSkill):
    """Skill to check overall project status."""

    name = "check_project_status"
    description = "Check the overall status of the AI Video Workflow project"

    def __init__(self, db_session: AsyncSession | None = None):
        self.db_session = db_session

    async def execute(self, **kwargs: Any) -> SkillResult[ProjectStatus]:
        """Check project status including database and API configuration."""
        try:
            status = ProjectStatus()

            # Check API keys configuration
            status.api_keys_configured = {
                "google": bool(settings.google_api_key),
                "youtube": bool(settings.youtube_client_id and settings.youtube_refresh_token),
            }

            # Check database if session available
            if self.db_session:
                try:
                    # Count stories
                    result = await self.db_session.execute(select(func.count(StoryHistory.id)))
                    status.total_episodes = result.scalar() or 0

                    # Count videos
                    result = await self.db_session.execute(select(func.count(VideoGeneration.id)))
                    status.total_videos = result.scalar() or 0

                    # Count uploads
                    result = await self.db_session.execute(select(func.count(YouTubeUpload.id)))
                    status.total_uploads = result.scalar() or 0

                    # Last execution
                    result = await self.db_session.execute(
                        select(WorkflowExecution)
                        .order_by(WorkflowExecution.started_at.desc())
                        .limit(1)
                    )
                    last_exec = result.scalar_one_or_none()
                    if last_exec:
                        status.last_execution = last_exec.started_at.isoformat()
                        status.last_execution_status = last_exec.status

                    status.database_connected = True
                except Exception:
                    status.database_connected = False

            return SkillResult.success(status)
        except Exception as e:
            return SkillResult.failed(f"Failed to check project status: {e}")


class RunWorkflowSkill(BaseSkill):
    """Skill to run the video generation workflow."""

    name = "run_workflow"
    description = "Run the video generation workflow for an episode"

    async def execute(
        self,
        episode: int | None = None,
        private: bool = False,
        **kwargs: Any,
    ) -> SkillResult[WorkflowRunResult]:
        """Run the workflow for a specific episode."""
        try:
            from src.database import AsyncSessionLocal
            from src.workflow import VideoWorkflowAgent

            start_time = datetime.now()

            async with AsyncSessionLocal() as session:
                agent = VideoWorkflowAgent(db_session=session)
                result = await agent.run(episode_number=episode, private=private)

            duration = (datetime.now() - start_time).total_seconds()

            if result.error:
                return SkillResult.success(
                    WorkflowRunResult(
                        success=False,
                        episode=episode,
                        error=result.error,
                        duration_seconds=duration,
                    )
                )

            return SkillResult.success(
                WorkflowRunResult(
                    success=True,
                    episode=len(result.story_history) if result.story_history else episode,
                    video_url=result.upload_result.url if result.upload_result else None,
                    duration_seconds=duration,
                )
            )
        except Exception as e:
            return SkillResult.failed(f"Workflow execution failed: {e}")


class ViewHistorySkill(BaseSkill):
    """Skill to view story and video history."""

    name = "view_history"
    description = "View story and video generation history"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        limit: int = 10,
        **kwargs: Any,
    ) -> SkillResult[list[dict]]:
        """View recent history."""
        try:
            result = await self.db_session.execute(
                select(StoryHistory).order_by(StoryHistory.created_at.desc()).limit(limit)
            )
            stories = result.scalars().all()

            history = []
            for story in stories:
                history.append(
                    {
                        "episode": story.episode,
                        "title": story.title,
                        "dish": story.dish,
                        "date": story.date,
                        "created_at": story.created_at.isoformat() if story.created_at else None,
                    }
                )

            return SkillResult.success(history)
        except Exception as e:
            return SkillResult.failed(f"Failed to view history: {e}")


class RunDatabaseMigrationSkill(BaseSkill):
    """Skill to run database migrations."""

    name = "run_database_migration"
    description = "Run Alembic database migrations"

    async def execute(
        self,
        action: str = "upgrade",
        revision: str = "head",
        **kwargs: Any,
    ) -> SkillResult[str]:
        """Run database migration."""
        try:
            if action not in ("upgrade", "downgrade", "current", "history"):
                return SkillResult.failed(f"Invalid action: {action}")

            cmd = ["alembic", action]
            if action in ("upgrade", "downgrade"):
                cmd.append(revision)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=settings.data_dir.parent,
            )

            if result.returncode != 0:
                return SkillResult.failed(f"Migration failed: {result.stderr}")

            return SkillResult.success(result.stdout or "Migration completed successfully")
        except Exception as e:
            return SkillResult.failed(f"Migration error: {e}")


class CleanupFilesSkill(BaseSkill):
    """Skill to clean up old generated files."""

    name = "cleanup_files"
    description = "Clean up old video files and logs"

    async def execute(
        self,
        older_than_days: int = 7,
        dry_run: bool = True,
        **kwargs: Any,
    ) -> SkillResult[dict]:
        """Clean up old files."""
        try:
            from datetime import timedelta

            cutoff = datetime.now() - timedelta(days=older_than_days)
            deleted_files = []
            total_size = 0

            # Clean video files
            video_dir = settings.output_dir / "videos"
            if video_dir.exists():
                for file in video_dir.glob("*.mp4"):
                    if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                        size = file.stat().st_size
                        if not dry_run:
                            file.unlink()
                        deleted_files.append(str(file))
                        total_size += size

            # Clean log files
            log_dir = settings.logs_dir
            if log_dir.exists():
                for file in log_dir.glob("*.log"):
                    if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                        size = file.stat().st_size
                        if not dry_run:
                            file.unlink()
                        deleted_files.append(str(file))
                        total_size += size

            return SkillResult.success(
                {
                    "files_count": len(deleted_files),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "dry_run": dry_run,
                    "files": deleted_files[:10],  # Show first 10
                }
            )
        except Exception as e:
            return SkillResult.failed(f"Cleanup failed: {e}")


class InitializeDatabaseSkill(BaseSkill):
    """Skill to initialize the database."""

    name = "initialize_database"
    description = "Initialize database tables"

    async def execute(self, **kwargs: Any) -> SkillResult[str]:
        """Initialize the database."""
        try:
            from src.database import init_db

            await init_db()
            return SkillResult.success("Database initialized successfully")
        except Exception as e:
            return SkillResult.failed(f"Database initialization failed: {e}")
