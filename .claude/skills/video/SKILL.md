---
name: video
description: AI 요리 영상 생성 워크플로우를 관리합니다. 에피소드 생성 (스토리->비디오->업로드), 스토리만 생성, 비디오만 생성, 상태 확인을 지원합니다. 넝심이 캐릭터 영상 관련 작업 시 사용합니다.
allowed-tools: Bash(uv:*), Bash(python:*), Read, Glob, Grep
---

# Video Skill - AI 요리 영상 생성

## 개요
너구리 캐릭터 "넝심이"의 요리 영상을 자동으로 생성하는 워크플로우를 관리합니다.

## 핵심 명령어

### 전체 에피소드 생성 (스토리 -> 비디오 -> YouTube)
```bash
# 자동 에피소드 번호 (다음 에피소드)
uv run python main.py

# 특정 에피소드 번호 지정
uv run python main.py 5

# 비공개로 업로드 (테스트용)
uv run python main.py --private
```

### CLI 명령어
```bash
# 새 에피소드 생성
uv run python cli.py generate

# 특정 에피소드 번호로 생성
uv run python cli.py generate 10

# 프로젝트 상태 확인
uv run python cli.py status

# 에피소드 히스토리 조회
uv run python cli.py history
uv run python cli.py history 20  # 최근 20개
```

## 워크플로우 단계

```
load_history -> generate_story -> generate_videos -> upload_to_youtube -> save_history
                     |                  |                   |
                     +------------------+-------------------+-> handle_error
```

| 단계 | API | 설명 |
|------|-----|------|
| generate_story | Gemini | 요리 스토리 + 5개 video_prompts 생성 |
| generate_videos | Veo3 | 각 prompt로 5초 영상 생성 후 병합 |
| upload_to_youtube | YouTube API | Shorts로 업로드 |

## 비디오 사양
- **해상도**: 1080x1920 (세로, 9:16)
- **모델**: Veo 3.1 Fast
- **각 장면**: 5초 x 5장면 = 25초
- **오디오**: 효과음만 (음성 없음)

## 상세 가이드
워크플로우 상세 내용은 [workflow-guide.md](docs/workflow-guide.md) 참조

## 주요 파일
- `main.py` - 메인 진입점
- `cli.py` - CLI 도구
- `src/workflow.py` - LangGraph 워크플로우
- `src/story_generator.py` - Gemini 스토리 생성
- `src/video_generator.py` - Veo3 비디오 생성

## 데이터베이스 테이블
| 테이블 | 설명 |
|--------|------|
| story_history | 생성된 스토리, video_prompts, tags |
| video_generations | 비디오 생성 상태 및 경로 |
| youtube_uploads | YouTube 업로드 기록 |
| workflow_executions | 워크플로우 실행 이력 |

## 설정 확인
```bash
# API 키 설정 확인
uv run python scripts/setup.py --check

# 데이터베이스 초기화
uv run python scripts/init_db.py
```

## 파일 정리
```bash
# 드라이런 (삭제하지 않고 목록만)
uv run python cli.py cleanup

# 7일 이상 된 파일 실제 삭제
uv run python cli.py cleanup --execute
```
