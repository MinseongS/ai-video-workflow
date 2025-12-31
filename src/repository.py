"""데이터베이스 리포지토리 패턴"""

from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db_models import StoryHistory, VideoGeneration, WorkflowExecution, YouTubeUpload
from src.models import Story, StoryHistoryEntry


class StoryRepository:
    """스토리 히스토리 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, story: Story, episode: int) -> StoryHistory:
        """새 스토리 히스토리 생성"""
        db_story = StoryHistory(
            episode=episode,
            date=datetime.now(),
            title=story.title,
            dish=story.dish,
            summary=story.summary,
            story=story.story,
            cooking_steps=story.cooking_steps,
            video_prompts=story.video_prompts,
            tags=story.tags,
            description=story.description,
        )
        self.session.add(db_story)
        await self.session.flush()
        await self.session.refresh(db_story)
        return db_story

    async def get_by_episode(self, episode: int) -> StoryHistory | None:
        """에피소드 번호로 조회"""
        result = await self.session.execute(
            select(StoryHistory).where(StoryHistory.episode == episode)
        )
        return result.scalar_one_or_none()

    async def get_latest(self, limit: int = 5) -> list[StoryHistory]:
        """최근 스토리 조회"""
        result = await self.session.execute(
            select(StoryHistory).order_by(desc(StoryHistory.episode)).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[StoryHistory]:
        """모든 스토리 조회"""
        result = await self.session.execute(select(StoryHistory).order_by(StoryHistory.episode))
        return list(result.scalars().all())

    async def get_count(self) -> int:
        """전체 스토리 개수"""
        result = await self.session.execute(select(func.count(StoryHistory.id)))
        return result.scalar() or 0

    def to_model(self, db_story: StoryHistory) -> StoryHistoryEntry:
        """데이터베이스 모델을 Pydantic 모델로 변환"""
        return StoryHistoryEntry(
            episode=db_story.episode,
            date=db_story.date.isoformat(),
            title=db_story.title,
            dish=db_story.dish,
            summary=db_story.summary,
            story=db_story.story,
            cooking_steps=db_story.cooking_steps,
            video_prompts=db_story.video_prompts,
            tags=db_story.tags,
            description=db_story.description,
        )


class VideoGenerationRepository:
    """영상 생성 기록 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        story_id: int,
        status: str = "processing",
        video_path: str | None = None,
        segments: list[dict] | None = None,
    ) -> VideoGeneration:
        """새 영상 생성 기록 생성"""
        db_video = VideoGeneration(
            story_id=story_id, status=status, video_path=video_path, segments=segments or []
        )
        self.session.add(db_video)
        await self.session.flush()
        await self.session.refresh(db_video)
        return db_video

    async def update(
        self,
        video_id: int,
        status: str | None = None,
        video_path: str | None = None,
        video_url: str | None = None,
        error_message: str | None = None,
    ) -> VideoGeneration | None:
        """영상 생성 기록 업데이트"""
        result = await self.session.execute(
            select(VideoGeneration).where(VideoGeneration.id == video_id)
        )
        db_video = result.scalar_one_or_none()

        if db_video:
            if status:
                db_video.status = status
            if video_path:
                db_video.video_path = video_path
            if video_url:
                db_video.video_url = video_url
            if error_message:
                db_video.error_message = error_message

            await self.session.flush()
            await self.session.refresh(db_video)

        return db_video


class YouTubeUploadRepository:
    """YouTube 업로드 기록 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        story_id: int,
        video_id: str,
        video_url: str,
        title: str,
        video_generation_id: int | None = None,
        privacy_status: str = "public",
    ) -> YouTubeUpload:
        """새 YouTube 업로드 기록 생성"""
        db_upload = YouTubeUpload(
            story_id=story_id,
            video_generation_id=video_generation_id,
            video_id=video_id,
            video_url=video_url,
            title=title,
            status="completed",
            privacy_status=privacy_status,
        )
        self.session.add(db_upload)
        await self.session.flush()
        await self.session.refresh(db_upload)
        return db_upload

    async def get_by_video_id(self, video_id: str) -> YouTubeUpload | None:
        """YouTube video ID로 조회"""
        result = await self.session.execute(
            select(YouTubeUpload).where(YouTubeUpload.video_id == video_id)
        )
        return result.scalar_one_or_none()


class WorkflowExecutionRepository:
    """워크플로우 실행 기록 리포지토리"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, episode_number: int | None = None, status: str = "running"
    ) -> WorkflowExecution:
        """새 워크플로우 실행 기록 생성"""
        db_execution = WorkflowExecution(episode_number=episode_number, status=status)
        self.session.add(db_execution)
        await self.session.flush()
        await self.session.refresh(db_execution)
        return db_execution

    async def update(
        self,
        execution_id: int,
        status: str | None = None,
        current_step: str | None = None,
        story_id: int | None = None,
        video_generation_id: int | None = None,
        youtube_upload_id: int | None = None,
        error_message: str | None = None,
    ) -> WorkflowExecution | None:
        """워크플로우 실행 기록 업데이트"""
        result = await self.session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        db_execution = result.scalar_one_or_none()

        if db_execution:
            if status:
                db_execution.status = status
            if current_step:
                db_execution.current_step = current_step
            if story_id:
                db_execution.story_id = story_id
            if video_generation_id:
                db_execution.video_generation_id = video_generation_id
            if youtube_upload_id:
                db_execution.youtube_upload_id = youtube_upload_id
            if error_message:
                db_execution.error_message = error_message

            if status in ["completed", "failed"]:
                db_execution.completed_at = datetime.now(timezone.utc)
                if db_execution.started_at:
                    # Handle timezone-aware/naive comparison
                    started = db_execution.started_at
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    duration = (db_execution.completed_at - started).total_seconds()
                    db_execution.duration_seconds = int(duration)

            await self.session.flush()
            await self.session.refresh(db_execution)

        return db_execution
