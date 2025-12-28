# 설정 가이드

이 문서는 AI YouTube 쇼츠 자동 생성 시스템을 설정하는 상세한 가이드를 제공합니다.

## 1. 사전 준비사항

### 필요한 계정 및 API 키

1. **Google Cloud Platform 계정**
   - Gemini API 키
   - Veo3 API 키 (사용 가능 시)
   - YouTube Data API v3 활성화

2. **YouTube 채널**
   - 업로드할 YouTube 채널

3. **n8n 설치** (선택사항, 자동화를 위해 권장)

## 2. 프로젝트 설정

### 2.1 의존성 설치

```bash
npm install
```

### 2.2 환경 변수 설정

`env.example` 파일을 복사하여 `.env` 파일을 생성합니다:

```bash
cp env.example .env
```

`.env` 파일을 열어 필요한 값들을 입력합니다.

## 3. API 키 설정

### 3.1 Gemini API 키

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. 생성된 API 키를 `.env` 파일의 `GEMINI_API_KEY`에 입력

### 3.2 Veo3 API 키

Veo3 API가 공개되면:
1. Google Cloud Console에서 Veo3 API 활성화
2. 서비스 계정 키 생성 또는 API 키 생성
3. `.env` 파일에 설정

**참고**: Veo3 API가 아직 공개되지 않았을 수 있습니다. 실제 API 스펙에 맞게 코드를 수정해야 할 수 있습니다.

### 3.3 YouTube API 설정

#### 3.3.1 OAuth 2.0 클라이언트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. "API 및 서비스" > "사용자 인증 정보" 이동
4. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
5. 애플리케이션 유형: "웹 애플리케이션" 선택
6. 승인된 리디렉션 URI 추가: `http://localhost:3000/oauth2callback`
7. 클라이언트 ID와 클라이언트 시크릿을 `.env` 파일에 입력

#### 3.3.2 YouTube Data API v3 활성화

1. Google Cloud Console에서 "API 및 서비스" > "라이브러리" 이동
2. "YouTube Data API v3" 검색 및 활성화

#### 3.3.3 인증 토큰 획득

터미널에서 다음 명령어를 실행:

```bash
npm run auth:youtube
```

또는:

```bash
node scripts/youtube-auth-helper.js
```

화면에 표시된 URL을 브라우저에서 열고 인증을 완료한 후, 리디렉트된 URL에서 인증 코드를 복사하여 입력합니다.

생성된 `refresh_token`을 `.env` 파일의 `YOUTUBE_REFRESH_TOKEN`에 입력합니다.

## 4. n8n 설정

### 4.1 n8n 설치

#### Docker를 사용한 설치 (권장)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your_password \
  n8nio/n8n
```

#### npm을 사용한 설치

```bash
npm install -g n8n
n8n start
```

### 4.2 워크플로우 가져오기

1. n8n 웹 인터페이스 접속 (http://localhost:5678)
2. 왼쪽 메뉴에서 "Workflows" 클릭
3. "Import from File" 클릭
4. `workflows/daily-youtube-shorts-simple.json` 파일 선택 (간단한 버전 권장)
   또는 `workflows/daily-youtube-shorts.json` (전체 기능 버전)

### 4.3 환경 변수 설정

n8n에서 환경 변수를 설정합니다:

1. n8n 설정에서 환경 변수 추가
2. 또는 각 노드에서 직접 환경 변수 참조

필요한 환경 변수:
- `PROJECT_PATH`: 프로젝트 절대 경로 (예: `/Users/minseong/project/ai-youtube`)
- `GEMINI_API_KEY`
- `VEO3_API_KEY`
- `VEO3_PROJECT_ID`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_CHANNEL_ID`

### 4.4 크리덴셜 설정 (전체 기능 버전 사용 시)

**Gemini API 크리덴셜:**
1. n8n에서 "Credentials" 메뉴 이동
2. "Add Credential" 클릭
3. "Google Gemini API" 선택
4. API Key 입력

**YouTube OAuth2 API 크리덴셜:**
1. "Credentials" 메뉴에서 "Add Credential" 클릭
2. "YouTube OAuth2 API" 선택
3. Client ID, Client Secret, Refresh Token 입력

## 5. 테스트

### 5.1 API 연결 테스트

```bash
npm test
```

또는:

```bash
node scripts/test-apis.js
```

모든 API가 정상적으로 연결되는지 확인합니다.

### 5.2 수동 실행 테스트

```bash
npm start
```

또는:

```bash
node scripts/daily-video-generator.js
```

전체 프로세스가 정상적으로 작동하는지 확인합니다.

## 6. 스케줄 설정

### 6.1 n8n 스케줄러 사용 (권장)

n8n 워크플로우의 스케줄 트리거 노드에서 실행 시간을 설정합니다:
- 기본값: 매일 오전 9시
- 변경하려면 cron 표현식 수정

### 6.2 시스템 크론 사용

n8n을 사용하지 않는 경우, 시스템 크론을 설정할 수 있습니다:

```bash
crontab -e
```

다음 줄 추가:

```
0 9 * * * cd /Users/minseong/project/ai-youtube && node scripts/daily-video-generator.js >> logs/cron.log 2>&1
```

## 7. 문제 해결

### 7.1 YouTube 인증 오류

- `refresh_token`이 만료되었을 수 있습니다. `npm run auth:youtube`를 다시 실행하세요.
- OAuth 클라이언트의 리디렉션 URI가 정확한지 확인하세요.

### 7.2 Veo3 API 오류

- Veo3 API가 아직 공개되지 않았을 수 있습니다. API가 사용 가능해지면 코드를 업데이트해야 합니다.
- API 키와 프로젝트 ID가 올바른지 확인하세요.

### 7.3 영상 생성 실패

- ffmpeg가 설치되어 있는지 확인하세요: `ffmpeg -version`
- 출력 디렉토리에 쓰기 권한이 있는지 확인하세요.

### 7.4 스토리 일관성 문제

- `data/story-history.json` 파일을 확인하세요.
- 히스토리 파일이 손상된 경우 백업에서 복원하거나 삭제하여 처음부터 시작할 수 있습니다.

## 8. 모니터링

### 8.1 로그 확인

스크립트 실행 시 콘솔에 로그가 출력됩니다. n8n을 사용하는 경우 n8n의 실행 로그를 확인하세요.

### 8.2 히스토리 확인

생성된 스토리 히스토리는 `data/story-history.json` 파일에서 확인할 수 있습니다.

## 9. 다음 단계

- 알림 설정 (Telegram, Slack 등)
- 에러 처리 개선
- 영상 품질 최적화
- 스토리 다양성 향상

