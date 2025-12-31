"""Project manager agent for AI Video Workflow."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import BaseAgent
from src.agents.story_agent import StoryAgent
from src.agents.video_agent import VideoAgent
from src.agents.youtube_agent import YouTubeAgent
from src.skills.project_skills import (
    CheckProjectStatusSkill,
    CleanupFilesSkill,
    InitializeDatabaseSkill,
    ProjectStatus,
    RunDatabaseMigrationSkill,
    RunWorkflowSkill,
    ViewHistorySkill,
    WorkflowRunResult,
)


class ProjectManagerResult(BaseModel):
    """Result of project manager operations."""

    success: bool = False
    message: str = ""
    data: dict | None = None

    class Config:
        arbitrary_types_allowed = True


class ProjectManagerAgent(BaseAgent):
    """
    Agent for managing the AI Video Workflow project.

    This agent provides high-level project management capabilities including:
    - Running the complete video generation workflow
    - Checking project and API status
    - Managing database migrations
    - Viewing history and statistics
    - Cleaning up old files

    Can be used by Claude or other AI assistants to manage the project.
    """

    name = "project_manager_agent"
    description = "Manages the AI Video Workflow project including workflow execution, status monitoring, and maintenance"

    def __init__(self, db_session: AsyncSession | None = None):
        super().__init__(db_session)

        # Sub-agents for specialized tasks
        self.story_agent = StoryAgent(db_session=db_session)
        self.video_agent = VideoAgent(db_session=db_session)
        self.youtube_agent = YouTubeAgent(db_session=db_session)

        self._setup_skills()

    def _setup_skills(self) -> None:
        """Register project management skills."""
        self.register_skill(CheckProjectStatusSkill(self.db_session))
        self.register_skill(RunWorkflowSkill())
        self.register_skill(RunDatabaseMigrationSkill())
        self.register_skill(CleanupFilesSkill())
        self.register_skill(InitializeDatabaseSkill())
        if self.db_session:
            self.register_skill(ViewHistorySkill(self.db_session))

    async def get_status(self) -> ProjectStatus | None:
        """Get overall project status."""
        result = await self.execute_skill("check_project_status")
        return result.data if result.is_success else None

    async def run_workflow(
        self, episode: int | None = None, private: bool = False
    ) -> WorkflowRunResult | None:
        """Run the video generation workflow."""
        result = await self.execute_skill("run_workflow", episode=episode, private=private)
        return result.data if result.is_success else None

    async def view_history(self, limit: int = 10) -> list[dict]:
        """View recent story history."""
        if not self.db_session:
            return []
        result = await self.execute_skill("view_history", limit=limit)
        return result.data if result.is_success else []

    async def run_migration(
        self,
        action: str = "upgrade",
        revision: str = "head",
    ) -> str | None:
        """Run database migration."""
        result = await self.execute_skill(
            "run_database_migration",
            action=action,
            revision=revision,
        )
        return result.data if result.is_success else None

    async def cleanup(
        self,
        older_than_days: int = 7,
        dry_run: bool = True,
    ) -> dict | None:
        """Clean up old files."""
        result = await self.execute_skill(
            "cleanup_files",
            older_than_days=older_than_days,
            dry_run=dry_run,
        )
        return result.data if result.is_success else None

    async def initialize_database(self) -> bool:
        """Initialize the database."""
        result = await self.execute_skill("initialize_database")
        return result.is_success

    async def generate_episode(
        self, episode: int | None = None, private: bool = False
    ) -> ProjectManagerResult:
        """
        Generate a complete episode (story + video + upload).

        This is the main entry point for generating content.
        """
        mode = "PRIVATE" if private else "PUBLIC"
        print(f"[ProjectManager] Starting episode generation ({mode})...")

        # Check status first
        status = await self.get_status()
        if status:
            print(f"[ProjectManager] Current episodes: {status.total_episodes}")
            print(f"[ProjectManager] API keys configured: {status.api_keys_configured}")

        # Run workflow
        workflow_result = await self.run_workflow(episode=episode, private=private)

        if not workflow_result:
            return ProjectManagerResult(
                success=False,
                message="Workflow execution failed",
            )

        if workflow_result.success:
            return ProjectManagerResult(
                success=True,
                message=f"Episode {workflow_result.episode} generated successfully!",
                data={
                    "episode": workflow_result.episode,
                    "video_url": workflow_result.video_url,
                    "duration_seconds": workflow_result.duration_seconds,
                },
            )
        else:
            return ProjectManagerResult(
                success=False,
                message=f"Episode generation failed: {workflow_result.error}",
                data={"error": workflow_result.error},
            )

    async def run(self, command: str = "status", **kwargs: Any) -> ProjectManagerResult:
        """
        Run project manager commands.

        Available commands:
        - status: Check project status
        - generate: Generate a new episode
        - history: View episode history
        - migrate: Run database migrations
        - cleanup: Clean up old files
        - init: Initialize database
        """
        try:
            if command == "status":
                status = await self.get_status()
                if status:
                    return ProjectManagerResult(
                        success=True,
                        message="Project status retrieved",
                        data=status.model_dump(),
                    )
                return ProjectManagerResult(success=False, message="Failed to get status")

            elif command == "generate":
                episode = kwargs.get("episode")
                private = kwargs.get("private", False)
                return await self.generate_episode(episode=episode, private=private)

            elif command == "history":
                limit = kwargs.get("limit", 10)
                history = await self.view_history(limit=limit)
                return ProjectManagerResult(
                    success=True,
                    message=f"Retrieved {len(history)} episodes",
                    data={"episodes": history},
                )

            elif command == "migrate":
                action = kwargs.get("action", "upgrade")
                revision = kwargs.get("revision", "head")
                result = await self.run_migration(action=action, revision=revision)
                if result:
                    return ProjectManagerResult(
                        success=True,
                        message="Migration completed",
                        data={"output": result},
                    )
                return ProjectManagerResult(success=False, message="Migration failed")

            elif command == "cleanup":
                older_than_days = kwargs.get("older_than_days", 7)
                dry_run = kwargs.get("dry_run", True)
                result = await self.cleanup(
                    older_than_days=older_than_days,
                    dry_run=dry_run,
                )
                if result:
                    return ProjectManagerResult(
                        success=True,
                        message="Cleanup completed" if not dry_run else "Dry run completed",
                        data=result,
                    )
                return ProjectManagerResult(success=False, message="Cleanup failed")

            elif command == "init":
                success = await self.initialize_database()
                return ProjectManagerResult(
                    success=success,
                    message="Database initialized" if success else "Initialization failed",
                )

            else:
                return ProjectManagerResult(
                    success=False,
                    message=f"Unknown command: {command}. Available: status, generate, history, migrate, cleanup, init",
                )

        except Exception as e:
            return ProjectManagerResult(
                success=False,
                message=f"Command execution failed: {e}",
            )
