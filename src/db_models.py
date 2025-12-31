"""데이터베이스 모델 정의"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.database import Base


class StoryHistory(Base):
    """스토리 히스토리 테이블"""

    __tablename__ = "story_history"

    id = Column(Integer, primary_key=True, index=True)
    episode = Column(Integer, nullable=False, unique=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 스토리 정보
    title = Column(String(500), nullable=False)
    dish = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    story = Column(Text, nullable=False)
    cooking_steps = Column(JSON, nullable=False)  # 리스트로 저장
    video_prompts = Column(JSON, nullable=False)  # 리스트로 저장
    tags = Column(JSON, nullable=False)  # 리스트로 저장
    description = Column(Text, nullable=False)

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class VideoGeneration(Base):
    """영상 생성 기록 테이블"""

    __tablename__ = "video_generations"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, nullable=False, index=True)  # story_history.id 참조

    # 영상 정보
    video_path = Column(String(1000), nullable=True)
    video_url = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False)  # 'processing', 'completed', 'failed'

    # 세그먼트 정보
    segments = Column(JSON, nullable=True)  # 세그먼트 정보 리스트

    # 에러 정보
    error_message = Column(Text, nullable=True)

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class YouTubeUpload(Base):
    """YouTube 업로드 기록 테이블"""

    __tablename__ = "youtube_uploads"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, nullable=False, index=True)  # story_history.id 참조
    video_generation_id = Column(Integer, nullable=True, index=True)  # video_generations.id 참조

    # YouTube 정보
    video_id = Column(String(100), nullable=False, unique=True, index=True)
    video_url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)

    # 업로드 상태
    status = Column(String(50), nullable=False)  # 'uploading', 'completed', 'failed'
    privacy_status = Column(String(50), nullable=False, default="public")

    # 에러 정보
    error_message = Column(Text, nullable=True)

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkflowExecution(Base):
    """워크플로우 실행 기록 테이블"""

    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    episode_number = Column(Integer, nullable=True, index=True)

    # 실행 상태
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    current_step = Column(String(100), nullable=True)

    # 결과 참조
    story_id = Column(Integer, nullable=True, index=True)
    video_generation_id = Column(Integer, nullable=True, index=True)
    youtube_upload_id = Column(Integer, nullable=True, index=True)

    # 에러 정보
    error_message = Column(Text, nullable=True)

    # 실행 시간
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
