"""Story generation agent for AI Video Workflow."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import BaseAgent
from src.models import Story, StoryHistoryEntry
from src.skills.story_skills import (
    GenerateStorySkill,
    GetStoryHistorySkill,
    SaveStorySkill,
)
from src.story_generator import GeminiStoryGenerator


class StoryAgentResult(BaseModel):
    """Result of story agent execution."""

    story: Story | None = None
    story_id: int | None = None
    episode: int
    success: bool = False
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True


class StoryAgent(BaseAgent):
    """Agent responsible for story generation and management."""

    name = "story_agent"
    description = "Generates and manages cooking stories using Gemini API"

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        story_generator: GeminiStoryGenerator | None = None,
    ):
        super().__init__(db_session)
        self.story_generator = story_generator or GeminiStoryGenerator()
        self._setup_skills()

    def _setup_skills(self) -> None:
        """Register skills for this agent."""
        self.register_skill(GenerateStorySkill(self.story_generator))
        if self.db_session:
            self.register_skill(GetStoryHistorySkill(self.db_session))
            self.register_skill(SaveStorySkill(self.db_session))

    async def get_history(self, limit: int = 50) -> list[StoryHistoryEntry]:
        """Get story history from database."""
        if not self.db_session:
            return []

        result = await self.execute_skill("get_story_history", limit=limit)
        return result.data if result.is_success else []

    async def generate_story(
        self,
        episode: int,
        history: list[StoryHistoryEntry] | None = None,
    ) -> Story | None:
        """Generate a new story for the given episode."""
        result = await self.execute_skill(
            "generate_story",
            episode_number=episode,
            history=history,
        )
        return result.data if result.is_success else None

    async def save_story(self, story: Story, episode: int) -> int | None:
        """Save a story to the database."""
        if not self.db_session:
            return None

        result = await self.execute_skill("save_story", story=story, episode=episode)
        return result.data if result.is_success else None

    async def run(
        self,
        episode: int | None = None,
        save_to_db: bool = True,
        **kwargs: Any,
    ) -> StoryAgentResult:
        """
        Run the story agent to generate a new story.

        Args:
            episode: Episode number. If None, auto-increments from history.
            save_to_db: Whether to save the story to database.

        Returns:
            StoryAgentResult with the generated story.
        """
        try:
            # Get history for context
            history = await self.get_history()

            # Determine episode number
            if episode is None:
                episode = len(history) + 1

            print(f"[StoryAgent] Generating story for episode {episode}...")

            # Generate story
            story = await self.generate_story(episode, history)
            if not story:
                return StoryAgentResult(
                    episode=episode,
                    success=False,
                    error="Failed to generate story",
                )

            print(f"[StoryAgent] Generated: {story.title}")

            # Save to database
            story_id = None
            if save_to_db and self.db_session:
                story_id = await self.save_story(story, episode)
                if story_id:
                    print(f"[StoryAgent] Saved to database with ID: {story_id}")

            return StoryAgentResult(
                story=story,
                story_id=story_id,
                episode=episode,
                success=True,
            )

        except Exception as e:
            return StoryAgentResult(
                episode=episode or 0,
                success=False,
                error=str(e),
            )
