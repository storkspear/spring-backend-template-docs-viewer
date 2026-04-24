# Backlog

프로젝트 진행 중 "지금은 안 하지만 잊지 말 것" 목록. Item 단위 작업이 없어도 주기적으로 점검.

## 사용 규칙

1. **항목 추가 시** — 카테고리별 "대기" 섹션에 추가:
   ```
   - [ ] [카테고리] 제목 — 이유 (생성일: YYYY-MM-DD)
   ```

2. **카테고리 표기**: `Ops` / `Data` / `Obs` / `Security` / `Feature` / `DX` / `Template`

3. **작업 시작 시** — "대기" → "진행 중" 으로 이동 + `(담당 Item: Item X)` 추가:
   ```
   - [x] [Ops] Cloudflare Tunnel 셋업 — 외부 접근 (생성일: 2026-04-18, 담당 Item: Item Ops-1)
   ```

4. **완료 시** — "완료 (archive)" 로 이동 + 커밋 해시 연결:
   ```
   - [x] [Ops] ... — 이유 (완료일: YYYY-MM-DD, commit: abcdef0)
   ```

5. **2개월마다 archive → CHANGELOG 이관**, 이 파일은 가볍게 유지.

6. **새 Item plan 작성 시**: backlog 에서 관련 항목을 plan scope 에 포함 선언. plan 완료 시 해당 backlog 항목 일괄 archive. 규칙 상세: [`Git 워크플로우 (Git Workflow)`](../convention/git-workflow.md).

---

## 진행 중 (1)

- [ ] **Item Ops-1** — 홈서버 MVP (feature 브랜치 `feature/ops-1-home-server-mvp`). Template 쪽 Stage A 완료 (아래 완료 섹션 참조). 파생레포 생성 + Mac mini 최초 배포 (Stage B~F) 는 파생레포 측에서 진행.

---

## 대기

### 운영 배포 / 파이프라인 (Item Ops-1 — 파생레포/호스트 작업)

- [ ] [Ops] 무지개 스택 cutover — 기존 moojigae vite/webhook/nginx/duckdns cron 종료, 기존 cloudflared tunnel 제거 (2026-04-19)
- [ ] [Ops] Secrets management 체계 선택 (1Password CLI / sops / Vault / AWS Parameter Store) — `.env` 수기 관리 탈피 (2026-04-18)
- [ ] [Ops] MinIO root credential → service account 로테이션 (`mc admin user svcacct add`) — root 남용 위험 제거 (2026-04-18)
- [ ] [Ops] MinIO ↔ Supabase 동일 비번 사용 분리 — 하나 유출 시 연쇄 위험 (2026-04-18)

### 보안 / 자격증명

- [ ] [Security] TLS/HTTPS 내부 구간 검토 — CF 가 edge 처리 OK, 맥미니 ↔ NAS 내부 통신은? (2026-04-18)

### 데이터 / DB

- [ ] [Data] 백업 실행 (pg_dump 주기, NAS 보관, retention) — `backup-to-nas.sh.example` 은 placeholder (2026-04-18)
- [ ] [Data] 복구 drill — "edge-cases 3-1: 1~2 시간 내 복구" 주장 실측 (2026-04-18)
- [ ] [Data] GDPR / 개인정보 export/delete 요청 대응 절차 — 법적 대비 (2026-04-18)
- [ ] [Data] Supabase pooler 모드 (transaction vs session) 튜닝 가이드 — 성능 이슈 예방 (2026-04-18)
- [ ] [Data] Supabase Free → Pro 전환 기준 + 절차 — MAU 1K 도달 대비 (2026-04-18)

### 관측성 / 운영

- [ ] [Obs] Performance baseline (JMeter / Gatling) — 릴리스 전 기준 RPS / p95 (2026-04-18)
- [ ] [Obs] On-call 알림 피로 방지 규칙 (솔로 운영 기준) — 중요도별 알림 채널 분리 (2026-04-18)

### 앱 기능 (Phase 1+)

- [ ] [Feature] Billing 실제 구현 (Apple StoreKit + Google Play Billing) — 현재 Stub (2026-04-18)
- [ ] [Feature] 이미지 검열용 Admin 페이지 (유저 업로드 모더레이션) — Cyberduck/콘솔 대체 (2026-04-18)
- [ ] [Feature] i18n / 다국어 지원 전략 — 모바일 클라이언트와 계약 (2026-04-18)

### 개발자 경험 / 툴링 (DX)

- [ ] [DX] Inventory 기계 추출 파일 `docs/.inventory.yml` — Item 9 plan 의 embed 인벤토리 drift 방지 (2026-04-18)
- [ ] [DX] Multi-app 로컬 병렬 개발 가이드 (포트 충돌, IntelliJ run config 공유) — 여러 앱 동시 기동 (2026-04-18)
- [ ] [DX] Pre-push hook (build 자동 실행) — CI 실패 전 로컬 차단 (2026-04-18)

### 템플릿 진화

- [ ] [Template] Roll-forward 가이드 보강 (`cross-repo-cherry-pick.md` 에 인프라 변경 반영법) — 파생 레포가 template 업데이트 가져가는 법 (2026-04-18)
- [ ] [Template] Release cadence 규칙 (`template-v` 태그 찍는 주기) — 의도적 cadence 정의 (2026-04-18)
- [ ] [Template] 파생 레포 "inventory 자동 업데이트" 가이드 — 본인 파생 레포가 새 env/service 추가 시 문서 동기화 (2026-04-18)

---

## 완료 (archive, 지난 2개월)

- [x] Item 7 — DTO/API 네이밍 정리 (완료일: 2026-04-18, commit: `647b0c4`)
- [x] Item 9 v1 → v2 plan 개정 (완료일: 2026-04-18, commit: `ef9b912`)
- [x] Item 10 — 앱 프로비저닝 통합 스크립트 (완료일: 2026-04-19, merge: `ff4bcbb`)
- [x] Item 10b — Multi-DataSource wiring (완료일: 2026-04-19, merge: `69ca16d`)
- [x] Item 11 — Documentation contract test (완료일: 2026-04-19, merge: `03112a6`)
- [x] [Ops] Jenkins vs GitHub Actions 결정 + 파이프라인 구축 → GHA + Kamal 선택. Item Ops-1 Stage A (template-ready). 완료일: 2026-04-19, feature/ops-1-home-server-mvp 의 `6f08db4`
- [x] [Ops] 맥미니 배포 메커니즘 선택 → Docker + Kamal + kamal-proxy (launchd 는 cloudflared 에만). 완료일: 2026-04-19, `0254e09` + `99aaa79`
- [x] [Ops] Graceful shutdown / health check / 자동 재시작 룰 → Spring `server.shutdown=graceful` + `timeout-per-shutdown-phase=30s` + Kamal healthcheck `/actuator/health/liveness` + Docker `restart: unless-stopped`. 완료일: 2026-04-19, `8d9263a`
- [x] [Ops] Cloudflare Tunnel 셋업 (template-ready) → `guides/deployment.md §2.3` 에 tunnel create / DNS / ingress / Access 절차. 실제 tunnel 생성은 파생레포 onboarding 시. 완료일: 2026-04-19, `7f9acae`
- [x] [Obs] 로컬 관측성 범위 재조정 → 운영 전용으로 한정 (infra/docker-compose.observability.yml 분리). 완료일: 2026-04-19, `895ef84` + `47eeced`
- [x] [Obs] Prometheus retention 정책 → 운영 compose 에서 7일 확정. 완료일: 2026-04-19, `47eeced`
- [x] [DX] `bootstrap/build.gradle` bootRun 기본 프로파일 dev 주입 → convention plugin 에서 처리. 완료일: 2026-04-19, `d781b34`
- [x] [Security] JWT_SECRET prod 전용 생성 + 로테이션 주기 규약 → [`key-rotation.md §5 JWT_SECRET`](../production/setup/key-rotation.md) 에 6개월 주기 + 즉시 폐기 절차 문서화. JwtProperties 가 32자 미만 거부. 완료일: 2026-04-24
- [x] [Obs] Loki retention 정책 확정 → `infra/loki/loki-config.yml` 에 `retention_period: 336h` (14일) 확정. 완료일: 2026-04-24
- [x] [Feature] API 버저닝 롤아웃 결정 → [`ADR-008 (API 버전 관리 미도입)`](../philosophy/adr-008-no-api-versioning.md) 으로 의도적 미도입 확정. 도입 경로 (Cloudflare rewrite / ApiEndpoints prefix) 사전 기록. 완료일: 2026-04-24
- [x] [Feature] Push 실제 구현 → `FcmPushAdapter` 에 Firebase Admin SDK 호출 + MulticastMessage + 토픽 푸시 + 무효 토큰 추적 완료. APNs 는 iOS 고급 기능 필요 시점에 별도. 완료일: 2026-04-24
- [x] [Feature] OpenAPI → Flutter 클라이언트 계약 export → springdoc-openapi 2.6.0 로 `/v3/api-docs` + Swagger UI 제공. Flutter 측 자동 생성은 `openapi-generator-cli` 사용 (백엔드 쪽 준비 완료). 완료일: 2026-04-24

> 2개월 경과 후 CHANGELOG 로 이관.

---

## 관련 문서

- [`Git 워크플로우 (Git Workflow)`](../convention/git-workflow.md) — backlog 운영 규칙 상세
- [`CHANGELOG.md`](../../CHANGELOG.md) — archive 된 완료 항목의 최종 기록처
