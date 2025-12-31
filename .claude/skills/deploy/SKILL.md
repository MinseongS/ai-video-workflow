---
name: deploy
description: AI Video Workflow 프로젝트의 Docker 빌드, Kubernetes 배포, Skaffold 관리를 담당합니다. 배포, 파드 상태, 로그 확인, 수동 Job 트리거 등 인프라 작업 시 사용합니다.
allowed-tools: Bash(docker:*), Bash(kubectl:*), Bash(skaffold:*), Bash(ls:*), Read, Glob
---

# Deploy Skill - AI Video Workflow 배포 관리

## 개요
이 스킬은 AI Video Workflow 프로젝트의 배포 관련 작업을 처리합니다.

## Docker 명령어

```bash
# 이미지 빌드
docker build -t ai-video-workflow:latest .

# 이미지 태그 및 푸시
docker tag ai-video-workflow:latest ghcr.io/minseongs/ai-video-workflow:latest
docker push ghcr.io/minseongs/ai-video-workflow:latest

# 로컬 테스트 실행
docker run --env-file .env ai-video-workflow:latest
```

## Kubernetes 명령어

모든 리소스는 `ai-video` 네임스페이스에 배포됩니다.

```bash
# 전체 리소스 상태 확인
kubectl get all -n ai-video

# 파드 상태 확인
kubectl get pods -n ai-video

# 파드 로그 확인
kubectl logs -l app=ai-video-workflow -n ai-video --tail=100

# 파드 상세 정보
kubectl describe pod <pod-name> -n ai-video

# CronJob 상태
kubectl get cronjob daily-video-generator -n ai-video

# Job 수동 트리거
kubectl create job manual-$(date +%s) --from=cronjob/daily-video-generator -n ai-video

# Job 로그 확인
kubectl logs -f job/<job-name> -n ai-video

# 시크릿/ConfigMap 확인
kubectl get secrets ai-video-secrets -n ai-video
kubectl get configmap ai-video-config -n ai-video -o yaml

# PV/PVC 확인
kubectl get pv,pvc -n ai-video
```

## Skaffold 프로파일

| 프로파일 | 명령어 | 설명 |
|---------|--------|------|
| default | `skaffold run` | 디버깅용 Deployment |
| dev | `skaffold dev` | 파일 변경 감시, 자동 재배포 |
| prod | `skaffold run -p prod` | **운영 배포** - CronJob (매일 9시 KST) |
| test | `skaffold run -p test` | **E2E 테스트** - 1회 실행 Job |

## 배포 절차

### 운영 배포 (빌드 → 푸시 → 배포)
```bash
skaffold run -p prod
```

### E2E 테스트 (1회 실행)
```bash
skaffold run -p test
```

### 개발 모드 (파일 변경 시 자동 재배포)
```bash
skaffold dev
```

## 문제 진단

```bash
# 1. 전체 리소스 상태 확인
kubectl get all -n ai-video

# 2. 파드 로그 확인
kubectl logs <pod-name> -n ai-video --tail=200

# 3. 이벤트 확인
kubectl describe pod <pod-name> -n ai-video

# 4. PV/PVC 상태 확인
kubectl get pv,pvc -n ai-video
```

## 주요 파일
- `Dockerfile` - Docker 빌드 설정
- `skaffold.yaml` - Skaffold 프로파일
- `k8s/` - Kubernetes 매니페스트 (ai-video 네임스페이스)
  - `namespace.yaml` - ai-video 네임스페이스
  - `storage.yaml` - PV/PVC (외장 SSD)
  - `configmap.yaml` - 환경 설정
  - `secrets.yaml` - API 키 시크릿
  - `postgres.yaml` - PostgreSQL
  - `cronjob.yaml` - 운영 CronJob (매일 9시 KST)
  - `test/job.yaml` - E2E 테스트 Job
  - `test/deployment.yaml` - 디버깅용 Deployment

## 스토리지
영상은 노드의 외장 SSD에 저장됩니다:
- **output**: `/media/minseong/PortableSSD1/ai-video-output`
- **data**: `/media/minseong/PortableSSD1/ai-video-data`

## 주의사항
- 시크릿 배포 전 `uv run python scripts/setup.py`로 설정 확인
- 운영 배포 전 `test` 프로파일로 E2E 테스트 권장
- ghcr.io 로그인 필요: `docker login ghcr.io`
