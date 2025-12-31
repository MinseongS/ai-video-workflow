"""환경 변수 및 설정 관리"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google API (Gemini + Veo3)
    google_api_key: str = ""

    # YouTube API
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""

    # 캐릭터 설정
    main_character_name: str = "넝심이"
    main_character_description: str = "살짝 너구리 같은 귀여운 라쿤 캐릭터, 요리를 좋아함"
    supporting_character_name: str = "친구"
    supporting_character_description: str = "넝심이의 친구"

    # Video Generation
    skip_video_generation: bool = False  # Veo3 영상 생성 스킵 (테스트용)
    test_video_path: str = ""  # 테스트용 영상 파일 경로

    # PostgreSQL
    db_user: str = "postgres"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ai_video_workflow"
    db_echo: bool = False

    # 경로 설정 (환경변수로 설정하지 않음)
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def character_dir(self) -> Path:
        return self.project_root / "character"

    @property
    def character_image_path(self) -> Path | None:
        """캐릭터 참조 이미지 경로 (character/ 디렉토리의 첫 번째 이미지)"""
        if not self.character_dir.exists():
            return None
        for ext in ["png", "jpg", "jpeg", "webp"]:
            images = list(self.character_dir.glob(f"*.{ext}"))
            if images:
                return images[0]
        return None

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "output" / "videos"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# 전역 설정 인스턴스
settings = Settings()

# 디렉토리 생성
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)
