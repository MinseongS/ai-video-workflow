# AI YouTube Shorts 자동 생성 시스템

라쿤 캐릭터 "넝심이"의 요리 쇼츠 영상을 매일 자동으로 생성하고 YouTube에 업로드하는 LangGraph 기반 자동화 시스템입니다.

## 주요 기능

- **AI 스토리 생성** - Gemini API를 사용한 일관된 캐릭터 스토리
- **AI 영상 생성** - Google Veo3를 사용한 요리 영상 생성
- **자동 업로드** - YouTube API를 통한 쇼츠 자동 업로드
- **LangGraph 워크플로우** - 상태 기반 에이전트 자동화
- **Kubernetes 배포** - Skaffold를 통한 간편한 배포

## 기술 스택

Python 3.11+ | LangGraph | Gemini API | Veo3 API | YouTube API v3 | PostgreSQL | SQLAlchemy (async) | Docker | Kubernetes | Skaffold

---

## 빠른 시작

### 1. 의존성 설치

```bash
uv sync --dev
```

### 2. API 키 설정

```bash
uv run python scripts/setup.py
```

대화형 마법사가 실행되며 `.env` 파일과 `k8s/secrets.yaml`이 자동 생성됩니다.

### 3. 데이터베이스 초기화

```bash
uv run python scripts/init_db.py
```

### 4. 워크플로우 실행

```bash
uv run python main.py              # 자동 에피소드 번호
uv run python main.py 5            # 특정 에피소드
uv run python main.py --private    # 비공개로 업로드
```

---

## CLI 명령어

```bash
uv run python cli.py status        # 프로젝트 상태 확인
uv run python cli.py generate      # 새 에피소드 생성
uv run python cli.py history       # 에피소드 히스토리 조회
uv run python cli.py cleanup       # 오래된 파일 정리 (dry-run)
uv run python cli.py init          # 데이터베이스 초기화
```

---

## 배포

### Docker (로컬 테스트)

```bash
docker build -t ai-video-workflow:latest .
docker run --env-file .env ai-video-workflow:latest
```

### Kubernetes (Skaffold)

#### 사전 요구사항

- Kubernetes 클러스터 (v1.20+)
- kubectl 설정 완료
- Skaffold 설치
- ghcr.io 로그인 (`docker login ghcr.io`)

#### 운영 배포

```bash
# 1. API 키 설정 (k8s/secrets.yaml 자동 생성)
uv run python scripts/setup.py

# 2. 운영 배포 (빌드 → 푸시 → 배포)
skaffold run -p prod
```

매일 오전 9시(KST)에 자동으로 파이프라인이 실행됩니다.

#### E2E 테스트 (1회 실행)

```bash
skaffold run -p test
```

전체 파이프라인을 한 번 실행하여 영상 생성 및 업로드를 테스트합니다.

#### Skaffold 프로필

| 프로필 | 설명 | 사용 시점 |
|--------|------|----------|
| `(기본)` | Deployment | 디버깅 |
| `dev` | 파일 변경 시 자동 리빌드 | 개발 |
| `prod` | CronJob (매일 9시 KST) | **운영** |
| `test` | 일회성 Job | **E2E 테스트** |

```bash
skaffold run -p prod              # 운영 배포
skaffold run -p test              # E2E 테스트 (1회 실행)
skaffold dev                      # 개발 모드 (파일 감시)
```

#### 네임스페이스

모든 리소스는 `ai-video` 네임스페이스에 배포됩니다.

```bash
kubectl get all -n ai-video       # 리소스 확인
kubectl logs -f job/<job-name> -n ai-video  # 로그 확인
```

#### 수동 실행 (운영 환경에서)

```bash
kubectl create job manual-$(date +%s) --from=cronjob/daily-video-generator -n ai-video
```

#### 스토리지

영상은 노드의 외장 SSD에 저장됩니다:
- **output**: `/media/minseong/PortableSSD1/ai-video-output`
- **data**: `/media/minseong/PortableSSD1/ai-video-data`

---

## 아키텍처

### 워크플로우

```
load_history → generate_story → generate_videos → upload_to_youtube → save_history
                    ↓                 ↓                  ↓
                handle_error ←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

### Agents

| Agent | 역할 |
|-------|------|
| `StoryAgent` | Gemini API로 스토리 생성 |
| `VideoAgent` | Veo3 API로 영상 생성 |
| `YouTubeAgent` | YouTube 업로드 |
| `ProjectManagerAgent` | 프로젝트 관리 |

### Skills

Agents가 조합하여 사용하는 원자적 작업:

- **Story**: `GenerateStorySkill`, `GetStoryHistorySkill`, `SaveStorySkill`
- **Video**: `GenerateVideoSkill`, `MergeVideosSkill`, `SaveVideoGenerationSkill`
- **YouTube**: `UploadVideoSkill`, `GetVideoInfoSkill`, `SaveYouTubeUploadSkill`
- **Project**: `CheckProjectStatusSkill`, `RunWorkflowSkill`, `CleanupFilesSkill`

### 데이터베이스 스키마

| 테이블 | 용도 |
|--------|------|
| `story_history` | 생성된 스토리, 프롬프트, 태그 |
| `video_generations` | 영상 생성 상태 및 경로 |
| `youtube_uploads` | YouTube 비디오 ID, URL |
| `workflow_executions` | 워크플로우 실행 기록 |

---

## 프로젝트 구조

```
├── main.py                    # 엔트리 포인트
├── cli.py                     # CLI 도구
├── pyproject.toml             # 의존성 및 설정
├── Dockerfile                 # 멀티스테이지 빌드
├── skaffold.yaml              # Skaffold 설정
│
├── k8s/                       # Kubernetes 매니페스트 (운영)
│   ├── namespace.yaml         # ai-video 네임스페이스
│   ├── configmap.yaml         # 설정값
│   ├── secrets.yaml           # 시크릿 (setup.py로 생성)
│   ├── storage.yaml           # PV/PVC (외장 SSD)
│   ├── postgres.yaml          # PostgreSQL
│   ├── cronjob.yaml           # 운영 CronJob (매일 9시)
│   └── test/                  # 테스트/디버깅용
│       ├── job.yaml           # E2E 테스트 (1회 실행)
│       └── deployment.yaml    # 디버깅용 Deployment
│
├── scripts/
│   ├── setup.py               # API 키 설정 마법사
│   └── init_db.py             # DB 초기화
│
└── src/
    ├── agents/                # Agent 구현
    ├── skills/                # Skill 구현
    ├── workflow.py            # LangGraph 워크플로우
    ├── config.py              # 설정 (Pydantic)
    ├── models.py              # Pydantic 모델
    ├── db_models.py           # SQLAlchemy 모델
    └── repository.py          # 데이터 접근 계층
```

---

## 환경 변수

```bash
# Google API (Gemini + Veo3)
GOOGLE_API_KEY=your_google_api_key

# YouTube API
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token

# PostgreSQL
DB_PASSWORD=your_db_password
```

`scripts/setup.py` 실행 시 대화형으로 설정 가능합니다.

---

## 개발

### 코드 스타일

```bash
uv run ruff check --fix .      # 린팅
uv run ruff format .           # 포맷팅
```

### 테스트

```bash
uv run pytest
```

### 데이터베이스 마이그레이션

```bash
uv run alembic revision --autogenerate -m "설명"
uv run alembic upgrade head
```

---

## 주의사항

- **Veo3 API**: 공개 API가 아닐 수 있음 (mock fallback 포함)
- **ffmpeg**: 영상 병합에 필요 (Docker 이미지에 포함)
- **API 비용**: Gemini/Veo3 API 사용량 모니터링 필요
- **YouTube 할당량**: 일일 업로드 제한 확인

---

## 라이선스

MIT
