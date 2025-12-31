"""Story-related skills for AI Video Workflow."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Story, StoryHistoryEntry
from src.repository import StoryRepository
from src.skills.base import BaseSkill, SkillResult
from src.story_generator import GeminiStoryGenerator


class GenerateStorySkill(BaseSkill):
    """Skill to generate a new story using Gemini API."""

    name = "generate_story"
    description = "Generate a cooking story for an episode using Gemini API"

    def __init__(self, story_generator: GeminiStoryGenerator | None = None):
        self.story_generator = story_generator or GeminiStoryGenerator()

    async def execute(
        self,
        episode_number: int,
        history: list[StoryHistoryEntry] | None = None,
        **kwargs: Any,
    ) -> SkillResult[Story]:
        """Generate a story for the given episode number."""
        try:
            if history:
                self.story_generator.load_story_history(history)

            story = await self.story_generator.generate_story(episode_number)
            return SkillResult.success(story)
        except Exception as e:
            return SkillResult.failed(f"Story generation failed: {e}")


class GetStoryHistorySkill(BaseSkill):
    """Skill to retrieve story history from database."""

    name = "get_story_history"
    description = "Get story history from database"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        limit: int = 5,
        **kwargs: Any,
    ) -> SkillResult[list[StoryHistoryEntry]]:
        """Get the latest stories from history."""
        try:
            repo = StoryRepository(self.db_session)
            db_stories = await repo.get_latest(limit=limit)
            history = [repo.to_model(story) for story in db_stories]
            return SkillResult.success(history)
        except Exception as e:
            return SkillResult.failed(f"Failed to get story history: {e}")


class SaveStorySkill(BaseSkill):
    """Skill to save a story to database."""

    name = "save_story"
    description = "Save a story to the database"

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def execute(
        self,
        story: Story,
        episode: int,
        **kwargs: Any,
    ) -> SkillResult[int]:
        """Save a story and return its ID."""
        try:
            repo = StoryRepository(self.db_session)
            db_story = await repo.create(story, episode)
            await self.db_session.commit()
            return SkillResult.success(db_story.id)
        except Exception as e:
            await self.db_session.rollback()
            return SkillResult.failed(f"Failed to save story: {e}")
