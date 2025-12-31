"""Base agent class for AI Video Workflow."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.skills.base import BaseSkill


class AgentState(BaseModel):
    """Base state for agents."""

    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """Base class for all agents."""

    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self, db_session: AsyncSession | None = None):
        self.db_session = db_session
        self._skills: dict[str, BaseSkill] = {}

    def register_skill(self, skill: BaseSkill) -> None:
        """Register a skill to this agent."""
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> BaseSkill | None:
        """Get a registered skill by name."""
        return self._skills.get(name)

    @property
    def skills(self) -> list[str]:
        """List of registered skill names."""
        return list(self._skills.keys())

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Run the agent's main task."""
        pass

    async def execute_skill(self, skill_name: str, **kwargs: Any) -> Any:
        """Execute a registered skill."""
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")
        return await skill.execute(**kwargs)
