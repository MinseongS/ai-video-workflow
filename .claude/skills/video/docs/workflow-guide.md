# AI Video Workflow 상세 가이드

## 캐릭터 소개

**넝심이 (Neung-sim-i)**: 요리를 좋아하는 너구리 캐릭터
- 매일 새로운 요리에 도전
- 실수도 하지만 항상 긍정적
- 귀여운 외모와 성격

## 스토리 생성 구조

Gemini API를 통해 생성되는 스토리:

```json
{
  "episode": 1,
  "date": "2025-01-01",
  "title": "넝심이의 첫 번째 요리 도전: 떡볶이",
  "dish": "떡볶이",
  "summary": "넝심이가 떡볶이에 도전합니다",
  "story": "상세 스토리 내용...",
  "cooking_steps": ["단계 1", "단계 2", ...],
  "video_prompts": [
    "A cute raccoon character named 넝심이 enters a colorful kitchen...",
    "넝심이 carefully prepares ingredients...",
    "넝심이 starts cooking with enthusiasm...",
    "넝심이 tastes the dish with a surprised expression...",
    "넝심이 presents the final dish proudly..."
  ],
  "tags": ["#넝심이", "#요리", "#떡볶이", "#Shorts"],
  "description": "YouTube 설명문..."
}
```

## 비디오 생성 사양

| 항목 | 값 |
|------|-----|
| 해상도 | 1080x1920 (9:16) |
| 모델 | Veo 3.1 Fast |
| 장면 수 | 5개 |
| 장면당 길이 | 5초 |
| 총 길이 | 25초 |
| 형식 | MP4 (H.264) |
| 오디오 | 효과음만 (음성 없음) |

## 워크플로우 상세

### 1. load_history
- 데이터베이스에서 최근 5개 에피소드 로드
- 중복 요리 방지를 위해 사용

### 2. generate_story (Gemini API)
- 이전 히스토리 기반으로 새로운 요리 선택
- 5개의 video_prompts 생성
- YouTube 메타데이터 (title, description, tags) 생성

### 3. generate_videos (Veo3 API)
- 각 video_prompt로 5초 영상 생성
- ffmpeg로 5개 영상 병합
- 최종 MP4 파일 생성

### 4. upload_to_youtube
- YouTube Shorts로 업로드
- 제목, 설명, 태그 자동 설정
- #Shorts 태그 자동 추가

### 5. save_history
- 스토리, 비디오, 업로드 정보 저장
- workflow_executions 테이블에 실행 이력 기록

## 에러 처리

### 복구 방법
1. 에러 로그 확인: `uv run python cli.py status`
2. 특정 에피소드 재시도: `uv run python main.py <episode>`
3. 데이터베이스 확인: `workflow_executions` 테이블

### 일반적인 에러

| 에러 | 원인 | 해결 |
|------|------|------|
| API key not set | 환경변수 미설정 | `scripts/setup.py` 실행 |
| Veo3 timeout | API 응답 지연 | 재시도 또는 mock 모드 |
| ffmpeg not found | ffmpeg 미설치 | `brew install ffmpeg` |
| YouTube quota exceeded | 일일 할당량 초과 | 다음 날 재시도 |

## 파일 구조

```
data/
├── output/
│   └── videos/           # 생성된 비디오 파일
├── logs/                 # 로그 파일
└── temp/                 # 임시 파일
```

## 데이터베이스 스키마

### story_history
- episode, date, title, dish
- story, cooking_steps
- video_prompts (JSON array)
- tags (JSON array)

### video_generations
- story_id (FK)
- status (processing/completed/failed)
- video_path
- segments (JSON)

### youtube_uploads
- story_id (FK)
- video_id (YouTube ID)
- video_url
- title, privacy_status

### workflow_executions
- episode
- status
- started_at, completed_at
- error_message
