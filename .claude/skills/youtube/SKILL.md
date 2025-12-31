---
name: youtube
description: YouTube 업로드 및 관리를 담당합니다. 영상 업로드, 업로드 히스토리 조회, 영상 정보 확인, API 설정 등 YouTube 관련 작업 시 사용합니다.
allowed-tools: Bash(uv:*), Bash(python:*), Read, Glob, Grep
---

# YouTube Skill - YouTube 영상 관리

## 개요
AI Video Workflow에서 생성된 영상의 YouTube 업로드 및 관리를 담당합니다.

## 핵심 명령어

### 업로드 히스토리 조회
```bash
# 최근 업로드 10개 조회
uv run python cli.py history

# 최근 20개 조회
uv run python cli.py history 20
```

### 프로젝트 상태 (업로드 통계 포함)
```bash
uv run python cli.py status
```

### API 설정 확인
```bash
uv run python scripts/setup.py --check
```

## YouTube API 설정

### 필요한 환경 변수
| 변수 | 설명 |
|------|------|
| YOUTUBE_CLIENT_ID | OAuth 클라이언트 ID |
| YOUTUBE_CLIENT_SECRET | OAuth 클라이언트 시크릿 |
| YOUTUBE_REFRESH_TOKEN | OAuth 리프레시 토큰 |

### 설정 방법
```bash
# 대화형 설정 위자드
uv run python scripts/setup.py
```

## 업로드 옵션

### Privacy Status
| 값 | 설명 |
|-----|------|
| public | 공개 (기본값) |
| private | 비공개 (테스트용) |
| unlisted | 미등록 |

### YouTube Shorts 요구사항
- 세로 영상 (9:16 비율)
- 60초 이하
- #Shorts 태그 자동 포함

## 데이터베이스 조회

업로드 기록은 `youtube_uploads` 테이블에 저장:

| 컬럼 | 설명 |
|------|------|
| video_id | YouTube 비디오 ID |
| video_url | 영상 URL |
| title | 영상 제목 |
| privacy_status | 공개 상태 |
| uploaded_at | 업로드 시간 |

## 주요 파일
- `src/youtube_uploader.py` - YouTube API 클라이언트
- `src/skills/youtube_skills.py` - YouTube 스킬 구현
- `src/agents/youtube_agent.py` - YouTube 에이전트

## 트러블슈팅

### OAuth 토큰 만료
```bash
uv run python scripts/setup.py
```

### 업로드 실패 시
1. API 키 확인: `uv run python scripts/setup.py --check`
2. 네트워크 연결 확인
3. 영상 파일 확인: `ls -la data/output/videos/`
4. 로그 확인: `cat data/logs/*.log`

### Quota 초과
YouTube API 일일 quota: 업로드당 약 1600 quota 소모
- 일일 할당량 초과 시 다음 날 재시도
- `quota exceeded` 에러 발생 시 24시간 대기
