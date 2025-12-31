# Kubernetes 배포 가이드

## 사전 요구사항

- Kubernetes 클러스터 (v1.20 이상)
- kubectl 설치 및 클러스터 접근 권한
- Skaffold 설치 (https://skaffold.dev/docs/install/)
- Docker

## 빠른 시작 (Skaffold)

### 1. 설정 파일 생성

설정 마법사를 사용하여 .env와 secrets.yaml 생성:

```bash
uv run python scripts/setup.py
```

또는 수동으로:

```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml
# k8s/secrets.yaml 파일을 실제 값으로 수정
```

### 2. Skaffold로 배포

```bash
# 개발 모드 (자동 리빌드 + 로그 스트리밍)
skaffold dev

# 프로덕션 배포 (CronJob)
skaffold run -p prod

# 한 번만 실행 (테스트용)
skaffold run -p run-once
```

### 3. 상태 확인

```bash
kubectl get pods -l app=ai-video-workflow
kubectl get cronjobs
```

## Skaffold 프로필

| 프로필 | 용도 |
|--------|------|
| (기본) | Deployment로 배포 (디버깅용) |
| `dev` | 개발 모드 - 파일 변경 시 자동 리빌드 |
| `prod` | CronJob으로 배포 (매일 자동 실행) |
| `run-once` | Job으로 한 번 실행 (테스트용) |

## 수동 배포 (Skaffold 없이)

### 1. 이미지 빌드

```bash
docker build -t ai-video-workflow:latest .
```

### 2. 시크릿 생성

```bash
kubectl apply -f k8s/secrets.yaml
```

### 3. ConfigMap 생성

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. 스토리지 생성

```bash
kubectl apply -f k8s/storage.yaml
```

### 5. PostgreSQL 배포

```bash
kubectl apply -f k8s/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

### 6. 데이터베이스 초기화

```bash
kubectl run db-init --rm -it --image=ai-video-workflow:latest \
  --env-from=configmap/ai-video-config \
  --env-from=secret/ai-video-secrets \
  -- python scripts/init_db.py
```

### 7. 애플리케이션 배포

```bash
# CronJob (프로덕션)
kubectl apply -f k8s/cronjob.yaml

# 또는 Deployment (디버깅)
kubectl apply -f k8s/deployment.yaml
```

## 수동 실행

```bash
# CronJob에서 수동으로 Job 생성
kubectl create job manual-run-$(date +%s) --from=cronjob/daily-video-generator

# 또는 직접 Job 실행
kubectl apply -f k8s/job.yaml
```

## 모니터링

### CronJob 상태 확인

```bash
kubectl get cronjobs
kubectl get jobs
kubectl get pods -l app=ai-video-workflow
```

### 로그 확인

```bash
# 최근 Pod 로그
kubectl logs -l app=ai-video-workflow --tail=100

# 특정 Pod 로그
kubectl logs <pod-name>
```

### 데이터베이스 확인

```bash
# PostgreSQL Pod에 접속
kubectl exec -it $(kubectl get pod -l app=postgres -o name) -- \
  psql -U postgres -d ai_video_workflow

# 스토리 히스토리 조회
SELECT episode, title, created_at FROM story_history ORDER BY episode DESC LIMIT 5;
```

## 트러블슈팅

### Pod가 시작되지 않는 경우

```bash
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'
```

### 데이터베이스 연결 오류

- PostgreSQL 서비스 확인: `kubectl get svc postgres`
- 비밀번호 확인: `kubectl get secret ai-video-secrets -o yaml`
- 네트워크 정책 확인

### 영상 생성 실패

- Veo3 API 키 확인
- API 할당량 확인
- Pod 리소스 제한 확인

## 업데이트

### Skaffold 사용

```bash
# 이미지만 업데이트
skaffold build

# 전체 재배포
skaffold run -p prod
```

### 수동 업데이트

```bash
# 이미지 빌드 및 푸시
docker build -t <registry>/ai-video-workflow:latest .
docker push <registry>/ai-video-workflow:latest

# CronJob 이미지 업데이트
kubectl set image cronjob/daily-video-generator \
  ai-video-workflow=<registry>/ai-video-workflow:latest
```

## 백업

### 데이터베이스 백업

```bash
kubectl exec $(kubectl get pod -l app=postgres -o name) -- \
  pg_dump -U postgres ai_video_workflow > backup.sql
```

### 복원

```bash
kubectl exec -i $(kubectl get pod -l app=postgres -o name) -- \
  psql -U postgres ai_video_workflow < backup.sql
```
