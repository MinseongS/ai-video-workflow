"""Base skill class for AI Video Workflow."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel


class SkillStatus(str, Enum):
    """Skill execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


T = TypeVar("T")


class SkillResult(BaseModel, Generic[T]):
    """Result of a skill execution."""

    status: SkillStatus
    data: T | None = None
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def success(cls, data: T) -> "SkillResult[T]":
        """Create a successful result."""
        return cls(status=SkillStatus.SUCCESS, data=data)

    @classmethod
    def failed(cls, error: str) -> "SkillResult[T]":
        """Create a failed result."""
        return cls(status=SkillStatus.FAILED, error=error)

    @property
    def is_success(self) -> bool:
        """Check if the skill execution was successful."""
        return self.status == SkillStatus.SUCCESS


class BaseSkill(ABC):
    """Base class for all skills."""

    name: str = "base_skill"
    description: str = "Base skill"

    @abstractmethod
    async def execute(self, **kwargs: Any) -> SkillResult:
        """Execute the skill."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
