"""Skills module for AI Video Workflow."""

from src.skills.base import BaseSkill, SkillResult, SkillStatus
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
from src.skills.story_skills import (
    GenerateStorySkill,
    GetStoryHistorySkill,
    SaveStorySkill,
)
from src.skills.video_skills import (
    GenerateVideoSequenceSkill,
    GenerateVideoSkill,
    MergeVideosSkill,
    SaveVideoGenerationSkill,
    UpdateVideoGenerationSkill,
)
from src.skills.youtube_skills import (
    GetVideoInfoSkill,
    SaveYouTubeUploadSkill,
    UploadVideoSkill,
)

__all__ = [
    # Base
    "BaseSkill",
    "SkillResult",
    "SkillStatus",
    # Story skills
    "GenerateStorySkill",
    "GetStoryHistorySkill",
    "SaveStorySkill",
    # Video skills
    "GenerateVideoSkill",
    "GenerateVideoSequenceSkill",
    "MergeVideosSkill",
    "SaveVideoGenerationSkill",
    "UpdateVideoGenerationSkill",
    # YouTube skills
    "UploadVideoSkill",
    "GetVideoInfoSkill",
    "SaveYouTubeUploadSkill",
    # Project management skills
    "CheckProjectStatusSkill",
    "RunWorkflowSkill",
    "ViewHistorySkill",
    "RunDatabaseMigrationSkill",
    "CleanupFilesSkill",
    "InitializeDatabaseSkill",
    "ProjectStatus",
    "WorkflowRunResult",
]
