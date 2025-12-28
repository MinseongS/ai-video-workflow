# AI YouTube 쇼츠 자동 생성 시스템

라쿤 캐릭터 "넝심이"의 요리 쇼츠 영상을 매일 자동으로 생성하고 YouTube에 업로드하는 n8n 워크플로우 시스템입니다.

## 주요 기능

- 🤖 **AI 스토리 생성**: Gemini API를 사용하여 일관된 캐릭터와 스토리로 요리 영상 스토리 생성
- 🎬 **AI 영상 생성**: Google Veo3를 사용하여 요리 영상 생성
- 📺 **자동 업로드**: YouTube API를 통해 쇼츠 영상 자동 업로드
- 📅 **일일 자동화**: n8n 스케줄러를 통해 매일 자동 실행
- 🎭 **캐릭터 일관성**: 주인공과 조연 캐릭터의 일관된 유지

## 프로젝트 구조

```
ai-youtube/
├── scripts/
│   ├── gemini-story-generator.js    # Gemini API 스토리 생성
│   ├── veo3-video-generator.js      # Veo3 영상 생성
│   ├── youtube-uploader.js          # YouTube 업로드
│   ├── daily-video-generator.js     # 전체 프로세스 통합
│   └── merge-videos.js              # 영상 세그먼트 합치기
├── workflows/
│   └── daily-youtube-shorts.json    # n8n 워크플로우
├── data/
│   └── story-history.json           # 스토리 히스토리 (자동 생성)
├── output/
│   └── videos/                       # 생성된 영상 파일
├── package.json
├── env.example
└── README.md
```

## 설치 및 설정

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 API 키를 설정하세요:

```bash
cp env.example .env
```

필수 환경 변수:
- `GEMINI_API_KEY`: Google Gemini API 키
- `VEO3_API_KEY`: Google Veo3 API 키
- `VEO3_PROJECT_ID`: Google Cloud 프로젝트 ID
- `YOUTUBE_CLIENT_ID`: YouTube API 클라이언트 ID
- `YOUTUBE_CLIENT_SECRET`: YouTube API 클라이언트 시크릿
- `YOUTUBE_REFRESH_TOKEN`: YouTube API 리프레시 토큰
- `YOUTUBE_CHANNEL_ID`: YouTube 채널 ID

### 3. YouTube API 인증 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. 인증 URL 생성 및 토큰 획득:

```javascript
const YouTubeUploader = require('./scripts/youtube-uploader');
const uploader = new YouTubeUploader();

// 인증 URL 출력
console.log(uploader.getAuthUrl());

// 브라우저에서 URL 접속 후 인증 코드를 받아서:
// uploader.getTokensFromCode('인증코드').then(tokens => console.log(tokens));
```

### 4. n8n 설정

#### n8n 설치 (Docker 권장)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

#### 워크플로우 가져오기

1. n8n 웹 인터페이스 접속 (http://localhost:5678)
2. 워크플로우 메뉴에서 "Import from File" 선택
3. `workflows/daily-youtube-shorts.json` 파일 업로드
4. 필요한 크리덴셜 설정:
   - Gemini API 크리덴셜
   - YouTube OAuth2 API 크리덴셜
   - Veo3 API 키 (환경 변수로 설정)

#### 크리덴셜 설정

**Gemini API:**
- Credential Type: Google Gemini API
- API Key: `GEMINI_API_KEY` 값 입력

**YouTube API:**
- Credential Type: YouTube OAuth2 API
- Client ID, Client Secret, Refresh Token 입력

## 사용 방법

### 방법 1: n8n 워크플로우 사용 (권장)

1. n8n에서 워크플로우 활성화
2. 스케줄러가 매일 오전 9시에 자동 실행
3. 수동 실행도 가능 (워크플로우에서 "Execute Workflow" 클릭)

### 방법 2: 스크립트 직접 실행

```bash
node scripts/daily-video-generator.js
```

## 워크플로우 프로세스

1. **스토리 히스토리 로드**: 이전 에피소드 정보 로드
2. **스토리 생성**: Gemini API로 새로운 스토리 생성
3. **영상 생성**: Veo3 API로 여러 세그먼트 영상 생성
4. **영상 합치기**: 생성된 세그먼트들을 하나로 합치기
5. **YouTube 업로드**: 완성된 영상을 YouTube에 업로드
6. **히스토리 저장**: 스토리 정보를 히스토리에 저장

## 캐릭터 설정

캐릭터 정보는 환경 변수로 설정할 수 있습니다:

- `MAIN_CHARACTER_NAME`: 주인공 이름 (기본값: "넝심이")
- `MAIN_CHARACTER_DESCRIPTION`: 주인공 설명
- `SUPPORTING_CHARACTER_NAME`: 조연 이름
- `SUPPORTING_CHARACTER_DESCRIPTION`: 조연 설명

## 스토리 히스토리

생성된 스토리는 `data/story-history.json`에 저장되어 다음 에피소드 생성 시 참조됩니다. 이를 통해 캐릭터의 일관성과 스토리의 연속성을 유지합니다.

## 주의사항

1. **Veo3 API**: Veo3 API가 아직 공개되지 않았을 수 있습니다. 실제 API 스펙에 맞게 코드를 수정해야 할 수 있습니다.

2. **ffmpeg**: 영상 합치기를 위해 ffmpeg가 설치되어 있어야 합니다:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

3. **API 비용**: Gemini API와 Veo3 API 사용 시 비용이 발생할 수 있습니다. 사용량을 모니터링하세요.

4. **YouTube 할당량**: YouTube API는 일일 할당량이 있습니다. 여러 영상을 업로드할 경우 할당량을 확인하세요.

## 문제 해결

### 영상 생성 실패
- Veo3 API 키와 프로젝트 ID가 올바른지 확인
- API 할당량 확인

### YouTube 업로드 실패
- OAuth 토큰이 만료되지 않았는지 확인
- YouTube API 할당량 확인
- 영상 파일 크기 및 형식 확인 (최대 128GB, 지원 형식: MP4, MOV, AVI 등)

### 스토리 일관성 문제
- `data/story-history.json` 파일 확인
- 히스토리가 제대로 로드되고 있는지 확인

## 라이선스

MIT

