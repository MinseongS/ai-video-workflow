"""데이터 모델 정의"""

from pydantic import BaseModel, Field


class Story(BaseModel):
    """스토리 데이터 모델"""

    title: str
    dish: str
    summary: str
    story: str
    cooking_steps: list[str]
    video_prompts: list[str]
    tags: list[str]
    description: str
    episode: int | None = None
    date: str | None = None


class StoryHistoryEntry(BaseModel):
    """스토리 히스토리 엔트리"""

    episode: int
    date: str
    title: str
    dish: str
    summary: str
    story: str
    cooking_steps: list[str]
    video_prompts: list[str]
    tags: list[str]
    description: str


class VideoGenerationResult(BaseModel):
    """영상 생성 결과"""

    video_url: str | None = None
    operation_id: str | None = None
    status: str  # 'processing', 'completed', 'failed'
    file_path: str | None = None
    mock: bool = False


class YouTubeUploadResult(BaseModel):
    """YouTube 업로드 결과"""

    video_id: str
    url: str
    title: str


class WorkflowState(BaseModel):
    """LangGraph 워크플로우 상태"""

    # 입력
    episode_number: int | None = None
    privacy_status: str = "public"  # public, private, unlisted

    # 스토리 생성 단계
    story: Story | None = None
    story_history: list[StoryHistoryEntry] = Field(default_factory=list)
    story_id: int | None = None  # 데이터베이스 ID

    # 영상 생성 단계
    video_segments: list[VideoGenerationResult] = Field(default_factory=list)
    final_video_path: str | None = None
    video_generation_id: int | None = None  # 데이터베이스 ID

    # YouTube 업로드 단계
    upload_result: YouTubeUploadResult | None = None
    youtube_upload_id: int | None = None  # 데이터베이스 ID

    # 에러 처리
    error: str | None = None
    current_step: str = "start"

    # 메타데이터
    timestamp: str | None = None
    execution_id: int | None = None  # 워크플로우 실행 ID
