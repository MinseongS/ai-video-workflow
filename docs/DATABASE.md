# 데이터베이스 필요 여부

## 현재 구조

이 프로젝트는 **데이터베이스 없이** JSON 파일을 사용하여 데이터를 저장합니다.

### 사용하는 파일 기반 저장소

1. **스토리 히스토리**: `data/story-history.json`
   - 생성된 모든 스토리 정보 저장
   - 에피소드 번호, 제목, 요약, 태그 등
   - 다음 에피소드 생성 시 참조하여 캐릭터 일관성 유지

2. **n8n 워크플로우 데이터**: n8n 자체 저장소
   - n8n은 내부적으로 SQLite 또는 PostgreSQL 사용
   - 워크플로우 정의, 실행 히스토리 등 저장
   - 별도 설정 불필요

## 데이터베이스가 필요한 경우

### 현재 구조로 충분한 경우 (권장)

✅ **파일 기반 저장소로 충분한 경우:**
- 일일 1개 영상 생성
- 스토리 히스토리만 저장
- 단일 서버에서 실행
- 간단한 데이터 구조

### 데이터베이스가 유용한 경우

❌ **데이터베이스가 유용한 경우:**
- 여러 채널 동시 운영
- 대량의 메타데이터 저장 (조회수, 좋아요, 댓글 등)
- 복잡한 쿼리 및 분석 필요
- 여러 서버에서 분산 실행
- 실시간 모니터링 및 대시보드

## 권장 구조

### 현재 (파일 기반) - 권장

```
data/
└── story-history.json  # 스토리 히스토리
```

**장점:**
- 설정 간단
- 추가 의존성 없음
- 백업 쉬움 (파일 복사)
- 충분한 성능 (일일 1개 영상)

**단점:**
- 동시 접근 제한
- 복잡한 쿼리 불가
- 대용량 데이터 처리 어려움

### 데이터베이스 사용 시

#### 옵션 1: SQLite (가장 간단)

```javascript
// package.json에 추가
"better-sqlite3": "^9.0.0"

// 사용 예시
const Database = require('better-sqlite3');
const db = new Database('data/stories.db');

db.exec(`
  CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode INTEGER UNIQUE,
    title TEXT,
    dish TEXT,
    summary TEXT,
    story TEXT,
    tags TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);
```

**장점:**
- 파일 기반 (설정 간단)
- SQL 쿼리 가능
- 추가 서버 불필요

**단점:**
- 동시 쓰기 제한
- 대용량 데이터 처리 제한

#### 옵션 2: PostgreSQL (프로덕션 권장)

```javascript
// package.json에 추가
"pg": "^8.11.0"

// 사용 예시
const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});
```

**장점:**
- 강력한 쿼리 기능
- 동시 접근 지원
- 확장성 좋음
- 복잡한 분석 가능

**단점:**
- 별도 서버 필요
- 설정 복잡
- 오버헤드 (현재 용도에는 과함)

#### 옵션 3: MongoDB (NoSQL)

```javascript
// package.json에 추가
"mongodb": "^6.0.0"

// 사용 예시
const { MongoClient } = require('mongodb');
const client = new MongoClient(process.env.MONGODB_URI);
```

**장점:**
- 유연한 스키마
- JSON과 유사한 구조
- 확장성 좋음

**단점:**
- 별도 서버 필요
- 메모리 사용량 높음

## 권장 사항

### 현재 단계: 파일 기반 유지 ✅

**이유:**
1. 일일 1개 영상만 생성
2. 데이터 구조가 단순함
3. 추가 인프라 불필요
4. 유지보수 간단

### 향후 확장 시: SQLite 고려

**전환 시점:**
- 여러 채널 운영 시작
- 메타데이터 분석 필요
- 복잡한 쿼리 필요
- 성능 문제 발생

## 마이그레이션 가이드

### JSON → SQLite 마이그레이션

필요 시 다음 스크립트를 사용할 수 있습니다:

```javascript
// scripts/migrate-to-database.js
const Database = require('better-sqlite3');
const fs = require('fs');

const db = new Database('data/stories.db');
const history = JSON.parse(fs.readFileSync('data/story-history.json', 'utf-8'));

db.exec(`
  CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode INTEGER UNIQUE,
    title TEXT,
    dish TEXT,
    summary TEXT,
    story TEXT,
    tags TEXT,
    video_id TEXT,
    video_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

const insert = db.prepare(`
  INSERT INTO stories (episode, title, dish, summary, story, tags, video_id, video_url)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

history.forEach(story => {
  insert.run(
    story.episode,
    story.title,
    story.dish,
    story.summary,
    story.story,
    JSON.stringify(story.tags),
    story.videoId,
    story.videoUrl
  );
});

console.log('✅ 마이그레이션 완료');
```

## 결론

**현재는 데이터베이스가 필요하지 않습니다.** 

파일 기반 저장소(`data/story-history.json`)로 충분하며, 향후 확장이 필요할 때 SQLite로 전환하는 것을 권장합니다.

