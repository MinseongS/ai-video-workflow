# n8n 워크플로우 설정 가이드

## 방법 1: 자동 설정 (API 키 사용)

### 1. n8n API 키 생성

1. n8n 웹 인터페이스 접속 (http://localhost:5678)
2. Settings (설정) > API 메뉴로 이동
3. "Create API Key" 클릭
4. 생성된 API 키를 복사

### 2. 환경 변수 설정

`.env` 파일에 다음 추가:

```bash
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_api_key_here
PROJECT_PATH=/Users/minseong/project/ai-youtube
```

### 3. 워크플로우 설정 실행

기존 워크플로우 업데이트:
```bash
npm run setup:n8n vZ39nBavp03uxjeL
```

또는 새 워크플로우 생성:
```bash
npm run setup:n8n
```

## 방법 2: 수동 설정 (웹 인터페이스 사용)

### 1. 워크플로우 가져오기

1. n8n 웹 인터페이스 접속 (http://localhost:5678)
2. 왼쪽 메뉴에서 "Workflows" 클릭
3. "Import from File" 버튼 클릭
4. `workflows/daily-youtube-shorts-simple.json` 파일 선택

### 2. 워크플로우 편집

1. 가져온 워크플로우를 열기
2. "영상 생성 및 업로드 실행" 노드 클릭
3. Arguments 필드에서 프로젝트 경로 확인:
   ```
   /Users/minseong/project/ai-youtube/scripts/daily-video-generator.js
   ```
4. 필요시 경로 수정

### 3. 환경 변수 설정

n8n에서 환경 변수를 설정합니다:

1. Settings > Environment Variables로 이동
2. 다음 변수들 추가:
   - `PROJECT_PATH`: `/Users/minseong/project/ai-youtube`
   - `GEMINI_API_KEY`: (Gemini API 키)
   - `VEO3_API_KEY`: (Veo3 API 키)
   - `VEO3_PROJECT_ID`: (Google Cloud 프로젝트 ID)
   - `YOUTUBE_CLIENT_ID`: (YouTube 클라이언트 ID)
   - `YOUTUBE_CLIENT_SECRET`: (YouTube 클라이언트 시크릿)
   - `YOUTUBE_REFRESH_TOKEN`: (YouTube 리프레시 토큰)
   - `YOUTUBE_CHANNEL_ID`: (YouTube 채널 ID)

또는 `.env` 파일을 n8n이 읽을 수 있도록 설정:

```bash
# n8n Docker 실행 시
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -v /Users/minseong/project/ai-youtube/.env:/home/node/.env \
  n8nio/n8n
```

### 4. 워크플로우 활성화

1. 워크플로우 편집 화면에서 오른쪽 상단의 "Active" 토글을 켜기
2. 또는 워크플로우 목록에서 활성화

### 5. 스케줄 설정

1. "매일 오전 9시 실행" 노드 클릭
2. Cron Expression 확인: `0 9 * * *`
3. 필요시 시간 변경:
   - 매일 오전 10시: `0 10 * * *`
   - 매일 오후 2시: `0 14 * * *`
   - 매일 자정: `0 0 * * *`

## 테스트

### 수동 실행 테스트

1. 워크플로우 편집 화면에서 "Execute Workflow" 버튼 클릭
2. 실행 결과 확인
3. 오류가 있으면 각 노드를 클릭하여 상세 정보 확인

### 로그 확인

1. 워크플로우 실행 후 "Executions" 탭 클릭
2. 실행 히스토리 확인
3. 실패한 실행 클릭하여 오류 상세 확인

## 문제 해결

### "command not found" 오류

- Node.js가 PATH에 있는지 확인
- n8n이 실행되는 환경에서 Node.js 접근 가능한지 확인
- 절대 경로 사용: `/usr/local/bin/node`

### 환경 변수 인식 안 됨

- n8n 환경 변수 설정 확인
- 스크립트에서 `process.env`로 접근 가능한지 확인
- `.env` 파일이 올바른 위치에 있는지 확인

### 권한 오류

- 스크립트 실행 권한 확인: `chmod +x scripts/daily-video-generator.js`
- 파일 읽기/쓰기 권한 확인
- `data/` 및 `output/` 디렉토리 권한 확인

## 데이터베이스 필요 여부

**답: 현재는 데이터베이스가 필요하지 않습니다.**

이 프로젝트는 파일 기반 저장소를 사용합니다:
- 스토리 히스토리: `data/story-history.json`
- n8n 자체는 내부적으로 SQLite 사용 (별도 설정 불필요)

자세한 내용은 `docs/DATABASE.md`를 참고하세요.

## 다음 단계

1. ✅ 워크플로우 설정 완료
2. ✅ 환경 변수 설정 완료
3. ✅ 워크플로우 활성화 완료
4. 🔄 첫 번째 테스트 실행
5. 🔄 스케줄 확인 및 모니터링

