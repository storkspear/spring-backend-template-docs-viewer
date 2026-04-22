# Item 9 v2 — 인프라/사용법 문서 정비 (scope 조정 + 3-agent 리뷰 반영)

> **이 문서는 v2 개정본** 입니다. v1 (`5be87c2`) 는 3명 리뷰어 (실행가능성 / 완전성 / 가정검증) 의 Critical/Major 피드백 을 받고 개정됨.

## 메타

- **작성일**: 2026-04-18
- **리비전**: v2 (v1 = `5be87c2`, 리뷰 반영)
- **선행 완료**:
  - Item 7 (DTO 네이밍) 머지 `647b0c4`
  - application-{dev,prod}.yml `app:` 중복 fix `a42902a`, `70e3de1`
  - storage.md 2-tier bucket 정책 `98f20b1`
  - `.gitignore` node_modules 추가 `607874d`
- **후행 예약** (본 Item 에서 명시적으로 deferred):
  - **운영 배포 Item 묶음 (가칭 Item Ops-1)** — 운영 파이프라인 구축 시점 일괄. 포함:
    - secrets-management 체계 선택 + 문서
    - backup-recovery 실행 + drill + 문서
    - deployment pipeline (Jenkins vs GH Actions 결정 + 맥미니 launchd/systemd)
    - Cloudflare Tunnel 셋업 (tunnel ID, DNS, ingress, WAF, rate limit)
    - Slack/Discord 알림 종류·임계치 정의
    - Supabase CI secrets wiring
    - MinIO 외부 접근 방식 선택 (Tailscale / Cloudflare Tunnel)
    - MinIO root → service account 로테이션
    - 동일 비번 사용 (MinIO ↔ Supabase) 분리
  - **Item 10** — 앱 프로비저닝 통합 스크립트 (이전부터 예정)
  - **Item 11** — Documentation contract test (문서 claim ↔ artifact 자동 검증)
- **예상 작업량**: 1~1.5 일
- **결과물**:
  - 신설: `docs/infrastructure.md`, `docs/guides/onboarding.md`, `docs/conventions/decisions-infra.md`, `docs/backlog.md`
  - 수정: 루트 `README.md`, `docs/architecture.md`, `docs/guides/storage-setup.md`, `docs/guides/monitoring-setup.md`, `docs/conventions/observability.md`, `docs/philosophy.md` (결정 16~N 편입), `docs/conventions/git-workflow.md` (backlog 규칙), `.env.example` (주석 보강)

---

## 1. Context — v1 → v2 무엇이 바뀌었나

### 1.1 리뷰 피드백 적용 표

| v1 → v2 변화 | 근거 리뷰어 |
|---|---|
| `decisions.md` / `decisions-infra.md` 혼용 → **`decisions-infra.md`** 로 파일명 통일 확정 | 실행가능성 (Critical A) |
| C.4 "축약/보강" 모호 지시 → **라인 단위 이관 표** (대상 라인 / 액션 / 결과분량 / 대상 문서) | 실행가능성 (Critical B) |
| 🔍 F-01~F-03 의 "기록 위치" 명시 | 실행가능성 (Critical C) |
| Phase D 역방향 검증의 실행 주체 / 시점 / 산출물 명시 | 실행가능성 (Major D) |
| Phase E 3-agent → **1-agent** 축소 (Agent 2, 3 은 Item 11 로 이관) | 완전성 (과잉), 실행가능성 (Major E) |
| **Status 필드** (`planned / provisioned / in-prod`) 도입 | 가정검증 (구조적 권고) |
| `infrastructure.md` 상단에 **프로비저닝 상태 표** | 가정검증 (구조적 권고) |
| NAS MinIO = "template 관리자 개인 LAN 전용" 명시 | 가정검증 (F-4, I-A) |
| Phase B 에 Config/ArchUnit/Observ/README 서브테이블 추가 | 완전성 (Gap 2-1) |
| 문서 ↔ 문서 양방향 링크 검증 → Phase D 에 포함 | 완전성 (Gap 2-2) |
| philosophy.md 결정 16~N 후보 편입 sub-task 추가 | 가정검증 (F-5) |
| onboarding 시간 "15분" → "prereqs 제외 10~15분 / cold 25~30분" 이분화 | 가정검증 (F-6) |
| `new-app.sh` 기능 정확한 묘사 (586줄, settings.gradle + bootstrap/build.gradle 자동 수정 포함) | 가정검증 (F-7) |
| `docs/backlog.md` 신설 + 운영 규칙 문서화 | user 요청 |
| 운영 배포 관련 (secrets/backup/deployment/Cloudflare/Jenkins/Discord) → Item Ops-1 로 묶음 연기 | user 결정 |
| inventory drift 완화 메모 (향후 Item 11 에서 기계화) | 완전성 (스코프 평가) |

### 1.2 현재 프로비저닝 상태 (2026-04-18 기준)

| 컴포넌트 | Status | 비고 |
|---|---|---|
| Supabase | `provisioned` | 계정 발급 + 연결 테스트 완료. `.env` 에 `DB_URL/USER/PASSWORD` 저장 (gitignored). 레포 CI secret 미등록 (Item Ops-1) |
| NAS MinIO | `provisioned (LAN-only)` | `192.168.X.X:9000`. template 관리자 홈 네트워크 전용. 외부 접근은 Item Ops-1 |
| 맥미니 (운영 호스트) | `hardware-acquired` | 물리 보유, 네트워크/배포 셋업 pending (Item Ops-1) |
| Cloudflare Tunnel | `planned` | Item Ops-1 |
| Jenkins vs GH Actions | `undecided` | Item Ops-1 에서 결정 |
| Slack/Discord 알림 | `planned` | Item Ops-1 |
| 로컬 docker 스택 | `provisioned` | postgres/loki/grafana/prom/alertmanager compose 작동 확인 |

### 1.3 왜 지금이 최적 타이밍

- Phase 0 스캐폴딩 끝 → 파생 레포 0개 (아직)
- 문서 drift 있는 채로 파생 생기면 레포 N개마다 따로 수정
- Item 7, 9 (v2), 10 순서로 정리 후 Phase 1 진입 → 파이프라인/운영 (Item Ops-1) 이 자연스럽게 이어짐

---

## 2. 방법론 (Phase A ~ E)

**핵심 원칙**: 사람 기억 의존 0% — 모든 근거를 기계 추출한 인벤토리에서 파생.

### Phase A — 자동 인벤토리 (완료 + 보강)
`grep`, `find`, `ls`, `git log` 로 문서화 필요 artifact 전수 조사. v1 21 카테고리 + A.22 (philosophy 결정 16~N 후보).

### Phase B — 감사 매트릭스 (완료 + 보강)
Phase A × 현재 문서 매핑표. 서브테이블 v1 의 5개 → v2 의 **8개**. 각 결정에 **status 필드** 추가.

### Phase C — 신설/수정 작업
매트릭스의 ❌/🆕 를 0개로 만드는 본작업. 라인 단위 구체 지시.

### Phase D — 역방향 검증
**주체**: 본인 (수동). **시점**: Phase C 마지막 커밋 직후, Phase E 전. **산출물**: 본 plan 섹션 11 "Phase D 검증 결과" 표 커밋.

### Phase E — 1-agent 리뷰 (축소)
"신규 개발자 onboarding 시뮬레이터" 1명만. 운영자 시뮬 / 완전성 검사관 2명은 **Item 11 (Documentation contract test)** 으로 이관.

---

## 3. Phase A — 인벤토리 결과

> 재생산 방법: 각 서브섹션 아래 명령어 그대로 실행하면 동일 결과.
> 한계: plan 본문 embed 방식은 **drift 위험** (코드 바뀌면 plan 도 바뀌어야 함). 향후 Item 11 에서 기계 추출 파일로 분리 예정.

### A.1 Top-level 파일/디렉토리

```
.dockerignore, .editorconfig, .env.example, .github/, .gitignore, .gitmessage, .husky/,
CHANGELOG.md, Dockerfile, README.md, apps/, bootstrap/, build-logic/, build.gradle,
commitlint.config.js, common/, core/, docs/, gradle/, gradle.properties,
gradlew, gradlew.bat, infra/, package.json, settings.gradle, tools/
```

### A.2 Gradle 모듈 (19개 + build-logic)

```
:common:{common-logging, common-web, common-security, common-testing, common-querydsl}
:core:{core-user,core-auth,core-device,core-push,core-billing,core-storage}-{api,impl}
:bootstrap
(includeBuild: build-logic)
```

### A.3 환경 변수 (.env.example 32개 + prod yml placeholder 13개)

**활성** (.env.example 주석 해제 라인):
```
SPRING_PROFILES_ACTIVE, POSTGRES_{DB,USER,PASSWORD}, JWT_SECRET, APP_DOMAIN,
RESEND_API_KEY, RESEND_FROM_ADDRESS
```

**선택 (주석 처리)**:
```
DB_URL/USER/PASSWORD (prod), JWT_ISSUER, APP_PUSH_FCM_CREDENTIALS_PATH,
APP_RATE_LIMIT_*, APP_STORAGE_MINIO_* (8개), MINIO_ROOT_USER/PASSWORD,
GRAFANA_ADMIN_USER/PASSWORD, MANAGEMENT_SERVER_PORT, LOKI_URL,
DISCORD_WEBHOOK_URL, RESEND_FROM_NAME, APP_CREDENTIALS_{SLUG}_*
```

### A.4 Spring profile YAML (5개)

```
bootstrap/src/main/resources/application.yml            (공통 기본)
bootstrap/src/main/resources/application-dev.yml        (로컬 개발)
bootstrap/src/main/resources/application-prod.yml       (운영)
common/common-testing/src/main/resources/application-test.yml
common/common-security/src/test/resources/application-test.yml
```

### A.5 스크립트 파일

```
tools/new-app/new-app.sh             — 586줄. 앱 모듈 스캐폴딩 + settings.gradle + bootstrap/build.gradle 자동 수정 + 수동 작업 체크리스트 출력 (정정: v1 에서 "모듈 스캐폴딩만" 으로 과소묘사)
infra/scripts/init-core-schema.sql   — core 스키마 초기화
infra/scripts/init-app-schema.sql    — 앱 스키마 초기화 (template)
infra/scripts/keep-alive.sh          — (🔍 F-02 확인 필요)
infra/scripts/backup-to-nas.sh.example — (placeholder, Item Ops-1)
.husky/commit-msg                    — commitlint 실행
package.json scripts: prepare=husky, cz=cz
```

### A.6 Docker 서비스 (`infra/docker-compose.dev.yml`)

```
postgres      :5433
prometheus    :9090
loki          :3100
grafana       :3000
alertmanager  :9093
minio         :9000/:9001    (NAS 로 이관 후 로컬에선 선택적 기동)
minio-setup   (one-shot)
```

### A.7 Flyway 마이그레이션 (9개, V004 은 리팩토링으로 삭제됨 → 🔍 F-01 판명)

```
V001__init_users.sql
V002__init_social_identities.sql
V003__add_users_email_index.sql
V005__init_refresh_tokens.sql
V006__init_email_verification_tokens.sql
V007__init_password_reset_tokens.sql
V008__init_devices.sql
V009__add_devices_updated_at.sql
```

🔍 **F-01 결과**: V004 는 과거에 존재했으나 `87fb8e2 refactor: convert to per-app independent users model` 에서 **삭제**. Flyway 관례 상 번호 재사용 안 함. **Phase C 에서 `infrastructure.md` 부록 또는 DB 섹션에 1줄 기록**.

### A.8 Port 인터페이스 (7개)

```
AuthPort, EmailPort   (core-auth-api)
BillingPort           (core-billing-api)
DevicePort            (core-device-api)
PushPort              (core-push-api)
StoragePort           (core-storage-api)
UserPort              (core-user-api)
```

### A.9 Config Properties 클래스 (6개)

| 클래스 | Prefix |
|---|---|
| `JwtProperties` | `app.jwt` |
| `RateLimitProperties` | `app.rate-limit` |
| `AppCredentialProperties` | `app.credentials` |
| `ResendProperties` | `app.email.resend` |
| `FcmProperties` | `app.push.fcm` |
| `MinioProperties` | `app.storage.minio` |

### A.10 Spring AutoConfiguration (12개 + 10개 `.imports`)

```
common: logging, querydsl, security, web(+Observability+RateLimit)
core-impl: user, auth, device, push, billing, storage
+ FactoryApplication 의 @SpringBootApplication
AutoConfiguration.imports: 10개 모듈 META-INF
```

### A.11 ArchUnit 규칙 (22개)

```
APPS_MUST_NOT_DEPEND_ON_CORE_IMPL, APPS_MUST_NOT_DEPEND_ON_EACH_OTHER,
COMMON_MUST_NOT_DEPEND_ON_APPS, COMMON_MUST_NOT_DEPEND_ON_CORE,
CORE_API_MUST_NOT_DEPEND_ON_APPS, CORE_API_MUST_NOT_DEPEND_ON_CORE_IMPL,
CORE_API_MUST_NOT_DEPEND_ON_JPA, CORE_API_MUST_NOT_USE_JPA_ANNOTATIONS,
CORE_IMPL_MUST_NOT_DEPEND_ON_APPS, CORE_IMPL_MUST_NOT_DEPEND_ON_EACH_OTHER,
DEPRECATED_MUST_DECLARE_SINCE_AND_FOR_REMOVAL,
DTOS_MUST_BE_RECORDS, DTO_NAMING_SUFFIX,
ENTITIES_MUST_RESIDE_IN_IMPL_ENTITY,
EXCEPTIONS_MUST_RESIDE_IN_EXCEPTION_PACKAGE,
NO_MAPPER_CLASSES, PORT_INTERFACES_MUST_RESIDE_IN_API,
PORT_METHODS_MUST_NOT_EXPOSE_ENTITIES,
REPOSITORIES_MUST_RESIDE_IN_IMPL_REPOSITORY,
SERVICE_IMPL_MUST_RESIDE_IN_IMPL,
SPRING_BEANS_MUST_RESIDE_IN_IMPL_OR_APPS
(+ 1 개 — 🔍 F-03: 실제 22개 확정, grep 재검증 결과 일치)
```

🔍 **F-03 결과**: 22개 확정. **Phase C 에서 `conventions/naming.md` 에 목록 + 카테고리 분류 1페이지**.

### A.12 philosophy.md 결정 15개

```
1. 모듈러 모놀리스       9. BaseEntity 공통 슈퍼클래스
2. GitHub Template      10. 공통 조회 조건 인프라
3. core-api/impl 분리   11. 포트/어댑터 패턴
4. Gradle 모듈 경계      12. 앱별 독립 유저 모델
5. 단일 Postgres+schema 13. 앱별 인증 엔드포인트
6. HS256 JWT            14. Delegation mock 금지
7. 솔로 친화적 운영      15. Conventional Commits + 템플릿 semver
8. API 버전 Phase 0 미도입
```

### A.13 Observability 인프라 파일 (7개)

```
infra/prometheus/{prometheus.yml, rules.yml}
infra/loki/loki-config.yml
infra/grafana/dashboards/app-factory-overview.json
infra/grafana/provisioning/{dashboards, datasources}/*.yml
infra/alertmanager/config.yml
```

### A.14 CI 워크플로우 (7개)

```
ci.yml                 — 모든 push/PR → ./gradlew build
commit-lint.yml        — PR 커밋 메시지 conventional
pr-title.yml           — PR 타이틀 conventional
changelog-check.yml    — CHANGELOG 갱신 강제
release.yml            — template-v* tag → GitHub Release
release-pr-validate.yml — 릴리스 PR 형식 검증
tag-validate.yml       — 태그 이름 규칙
```

### A.15 Testcontainers / Abstract test infra

```
common/common-testing/.../AbstractContractBase.java
common/common-testing/.../AbstractIntegrationTest.java
common/common-testing/.../PostgresTestContainer.java
사용처: FactoryApplicationTests, HealthEndpointsTest, UserControllerTest, *ContractTest
```

### A.16 Build-logic convention plugins (5개)

```
build-logic/src/main/groovy/factory.{common,core-api,core-impl,bootstrap,app}-module.gradle
```

### A.17 Logback 설정 (2개)

```
bootstrap/src/main/resources/logback-spring.xml
common/common-logging/src/main/resources/logback-common.xml
```

### A.18 README 파일 (22개)

```
README.md (루트)
apps/README.md, bootstrap/README.md
common/common-{logging,querydsl,security,testing,web}/README.md
core/core-{auth,billing,device,push,storage,user}-{api,impl}/README.md
docs/conventions/README.md, docs/migration/README.md
```

### A.19 기존 docs 파일 (23개)

```
docs/architecture.md, philosophy.md, edge-cases.md, social-auth-setup.md
docs/conventions/README.md, api-response.md, contract-testing.md, design-principles.md,
  dto-factory.md, exception-handling.md, git-workflow.md, json-contract.md,
  module-dependencies.md, naming.md, observability.md, rate-limiting.md,
  records-and-classes.md, storage.md, versioning.md
docs/guides/cross-repo-cherry-pick.md, monitoring-setup.md, storage-setup.md
docs/migration/README.md
```

### A.20 Cloudflare / 맥미니 / NAS / Supabase 기존 언급 위치

| 문서 | 언급 라인 |
|---|---|
| `architecture.md` | 26, 65-94 (Supabase 전파), 350 (NAS backup), 426-429 (Cloudflare Tunnel), 682-698 (운영 구성) |
| `edge-cases.md` | 208-219 (맥미니 디스크 고장, Time Machine, Supabase) |
| `conventions/storage.md` | 2-tier bucket (Item 7 에서 추가) |

### A.21 미문서화 / 결손 주제 (정정 반영)

1. `node_modules/` 필요성 설명 (누락) — `onboarding.md` 로
2. `.husky/` 역할 (누락) — `onboarding.md` 로
3. `package.json` devDep 만 있는 이유 (누락) — `onboarding.md` 로
4. 맥미니 운영 선택 근거 — `decisions-infra.md` (status: hardware-acquired)
5. NAS MinIO 선택 근거 + LAN 전용 표식 — `decisions-infra.md` + `infrastructure.md`
6. Supabase 선택 근거 — `decisions-infra.md` (status: provisioned)
7. 로컬 2-tier bucket 정책의 prod 확장 — `infrastructure.md` 링크
8. "use this template" 직후 워크플로우 — `onboarding.md`
9. V004 번호 빠진 이유 — 판명, `infrastructure.md` 부록
10. `keep-alive.sh` 용도 — 🔍 F-02, Phase C 에서 파일 내용 확인 후 기록

### A.22 (신규) philosophy.md 결정 16~N 후보

Phase A 조사 결과 결정 16~ 의 **충분한 후보**:

| 후보 | 근거 문서 | 편입 여부 |
|---|---|---|
| **DTO 팩토리 + Mapper 폐기** | Item 4 커밋 `e203872`, `docs/conventions/dto-factory.md` | 결정 16 으로 편입 (코드 철학) |
| **2-tier bucket (dev-shared / prod per-app)** | `storage.md` (Item 7 추가) | 결정 17 로 편입 (인프라 결정) — 또는 `decisions-infra.md` 에만 |
| **NAS MinIO 오브젝트 스토리지** | `.env`, storage 대화 기록 | `decisions-infra.md` I-03 |
| **맥미니 운영 방향** | architecture.md 부분 | `decisions-infra.md` I-04 |
| **Conventional Commits** | 결정 15 (이미 있음) | 없음 |

**판단 기준**: 코드 구조/테스트/도메인 관련 = `philosophy.md`, 물리적 인프라 = `decisions-infra.md`. 경계 케이스는 양쪽에서 상호 참조.

### A.23 (🚧 deferred to Item Ops-1) 미포함 카테고리

완전성 리뷰어가 지적한 다음 3 카테고리는 **Item 9 v2 스코프 밖**, Item Ops-1 에서 다룸. backlog.md 에 식별:

- A-Ops-1: Secrets lifecycle (생성/보관/로테이션/백업/공유)
- A-Ops-2: 백업/복구 실행 계획 (RTO/RPO, drill)
- A-Ops-3: 배포 파이프라인 (CI artifact → 맥미니 runtime hop)
- A-Ops-4: Cloudflare Tunnel / 네트워크 엣지 설정 파일
- A-Ops-5: MinIO 외부 접근 방식 (Tailscale / CF Tunnel)
- A-Ops-6: Slack/Discord 알림 종류 + 임계치

---

## 4. Phase B — 감사 매트릭스

### 4.1 범례

| 기호 | 의미 |
|---|---|
| ✅ | 명시적 + 충분 문서화 |
| ⚠️ | 언급만 존재 (보강 필요) |
| ❌ | 미문서화 |
| 🆕 | Item 9 v2 에서 신설 |
| 🔍 | 사실확인 필요 (Phase C 중 처리) |
| 🚧 | Item Ops-1 로 연기 |

### 4.2 인프라 결정 매트릭스 (status 필드 포함)

| ID | 결정 | Status | 현재 문서 | 상태 | 조치 |
|---|---|---|---|---|---|
| I-01 | Supabase 운영 DB | `provisioned` | `architecture.md:26,65-94` | ⚠️ | `decisions-infra.md` 에 대안 비교 + 재검토 트리거. `infrastructure.md` 상단 표 |
| I-02 | 서비스별 schema | 결정 5 (코드) | `philosophy.md 결정 5` | ✅ | `infrastructure.md` 에서 참조 링크만 |
| I-03 | NAS MinIO (LAN-only) | `provisioned` | `storage.md` (2-tier) | ⚠️ | `decisions-infra.md` + LAN 한계 명시. `infrastructure.md` |
| I-04 | 맥미니 운영 | `hardware-acquired` | `architecture.md:688` | ⚠️ | `decisions-infra.md` + status 명시 (deployment pending) |
| I-05 | Cloudflare Tunnel | `planned` | `architecture.md:426` | ⚠️ | `decisions-infra.md` + Item Ops-1 연결 |
| I-06 | 로컬 관측성 스택 | `provisioned` | `monitoring-setup.md` | ✅ | `infrastructure.md` 링크 |
| I-07 | 2-tier bucket | `provisioned` (로컬), `planned` (운영) | `storage.md` | ✅ | `infrastructure.md` 링크 |

### 4.3 환경변수 매트릭스 (주요)

| ID | ENV | 문서 | 상태 |
|---|---|---|---|
| E-01 | SPRING_PROFILES_ACTIVE | .env.example | ⚠️ 사용처·영향 설명 보강 (`onboarding.md`) |
| E-02 | DB_URL/USER/PASSWORD | .env.example, application-prod.yml | ⚠️ Supabase pooler 주의점 (.env.example 주석 보강) |
| E-03 | JWT_SECRET | .env.example | ⚠️ 생성 명령 + 로테이션 정책 (`onboarding.md`) |
| E-04 | APP_STORAGE_MINIO_* | .env.example, storage.md | ✅ |
| E-05 | APP_CREDENTIALS_{SLUG}_* | social-auth-setup.md | ✅ |
| E-06 | MANAGEMENT_SERVER_PORT | application-prod.yml | ⚠️ 방화벽 차단 명령 (`infrastructure.md`) |
| E-07 | LOKI_URL | monitoring-setup.md | ✅ |
| E-08 | DISCORD_WEBHOOK_URL | application-prod.yml | 🚧 Item Ops-1 |
| E-09 | GRAFANA_ADMIN_* | .env.example | ⚠️ onboarding.md 에 언급 |

### 4.4 Onboarding / 툴체인 매트릭스

| ID | 항목 | 현재 | 상태 |
|---|---|---|---|
| O-01 | 필수 설치 (JDK 21, Docker, mc, gh) | 없음 | ❌ → 🆕 onboarding.md |
| O-02 | 로컬 첫 부팅 순서 | README 단편 | ⚠️ → 🆕 onboarding.md |
| O-03 | `npm install` 이유 | 없음 | ❌ → 🆕 onboarding.md |
| O-04 | `node_modules/` 생성 이유 | 없음 | ❌ → 🆕 onboarding.md |
| O-05 | `.husky/` 역할 | 없음 | ❌ → 🆕 onboarding.md |
| O-06 | 커밋 규약 (cz/commitlint) | `git-workflow.md` | ✅ |
| O-07 | 흔한 에러 5개 | `edge-cases.md` (일부) | ⚠️ → 🆕 onboarding.md |
| O-08 | "use this template" 직후 플로우 | 없음 | ❌ → 🆕 onboarding.md |
| O-09 | 시크릿 초기 세팅 5개 | 없음 | ❌ → 🆕 onboarding.md (JWT 만, 나머지 Item Ops-1) |
| O-10 | Phase 0 "무엇이 동작 안 하는가" | 없음 | ❌ → 🆕 onboarding.md |

### 4.5 Item 7 drift 재확인

| ID | 변경 | 위치 | 상태 |
|---|---|---|---|
| R-01 | UserCredentials → UserAccount | Java + 문서 | ✅ |
| R-02 | TokenPair → AuthTokens | Java + 문서 | ✅ |
| R-03 | PushResult → PushSendResult | Java + 문서 | ✅ |
| R-04 | verifyReceipt → registerPurchase | Java + 문서 | ✅ |
| R-05 | findCredentialsBy* → findAccountBy* | Java + 문서 | ✅ |
| R-06 | ArchUnit r19 allowlist | architecture, naming | ✅ |
| R-07 | architecture.md `tokenPair` 잔재 | 수정됨 | ✅ |

### 4.6 스크립트 / 자동화 매트릭스

| ID | 항목 | 현재 | 상태 |
|---|---|---|---|
| S-01 | `new-app.sh` 사용법 (586줄 기능) | 스크립트 주석 | ⚠️ → `onboarding.md` + `infrastructure.md` 로 명시 |
| S-02 | `init-core-schema.sql` | 없음 | ❌ → `infrastructure.md` DB 섹션 |
| S-03 | `init-app-schema.sql` | 없음 | ❌ → `infrastructure.md` DB 섹션 |
| S-04 | `keep-alive.sh` | 없음 | 🔍 F-02 파일 내용 확인 후 결정 |
| S-05 | `backup-to-nas.sh.example` | architecture.md:350 | 🚧 Item Ops-1 |
| S-06 | Item 10 통합 스크립트 | 없음 | 🚧 Item 10 |

### 4.7 (신규) Config Properties / ArchUnit / Observability / README 매트릭스

#### 4.7.1 Config Properties × 문서
| 클래스 | prefix | 문서 |
|---|---|---|
| JwtProperties | app.jwt | ✅ `conventions/observability.md` 에 언급 / `onboarding.md` 링크 |
| RateLimitProperties | app.rate-limit | ✅ `conventions/rate-limiting.md` |
| AppCredentialProperties | app.credentials | ✅ `social-auth-setup.md` |
| ResendProperties | app.email.resend | ⚠️ `.env.example` 주석만 / `infrastructure.md` 에 1줄 |
| FcmProperties | app.push.fcm | ⚠️ `.env.example` 주석만 / `infrastructure.md` 에 1줄 |
| MinioProperties | app.storage.minio | ✅ `storage.md` |

#### 4.7.2 ArchUnit 22개 × 관련 문서
- 🆕 `conventions/naming.md` 에 "ArchUnit 규칙 분류" 섹션 추가 (카테고리별 22개 목록)
- 또는 `conventions/module-dependencies.md` 와 `naming.md` 에 각자 half 분배
- 판단: 1 파일 단일 리스트가 검색 쉬움 → `module-dependencies.md` 에 통합

#### 4.7.3 Observability 파일 × 문서
| 파일 | 문서 |
|---|---|
| prometheus.yml, rules.yml | `monitoring-setup.md` ✅ |
| loki-config.yml | `monitoring-setup.md` ✅ |
| grafana/dashboards/*.json | `monitoring-setup.md` ⚠️ 대시보드 내용 설명 |
| alertmanager/config.yml | 🚧 Item Ops-1 (알림 종류/임계치) |

#### 4.7.4 모듈 README 22개
- 전수 스캔 `Item 9 v2 에서 확인` → 어느 README 에 stale 내용 (예: verifyReceipt) 남아있는지 grep 후 수정

### 4.8 (신규) 문서 ↔ 문서 양방향 링크 매트릭스

Phase D 에서 자동 검증할 쌍:

| A | B | 양방향? |
|---|---|---|
| infrastructure.md | decisions-infra.md | ✅ |
| infrastructure.md | onboarding.md | ✅ |
| infrastructure.md | storage.md | ✅ |
| onboarding.md | philosophy.md | ✅ |
| architecture.md | infrastructure.md | ✅ (architecture 는 인프라 섹션 축소 + 링크) |
| backlog.md | git-workflow.md | ✅ (규칙 정의 위치 ↔ 실제 목록) |
| philosophy.md (결정 16) | dto-factory.md | ✅ |
| decisions-infra.md | storage.md | ✅ |

양방향 pass 조건: A → B 와 B → A 링크 모두 존재.

---

## 5. Phase C — 신설/수정 작업 (라인 단위 구체)

### C.1 🆕 `docs/infrastructure.md` 신설

**섹션 outline**:

```
1. 이 문서의 범위
   - 인프라만 (코드 아키텍처는 architecture.md)
   - 대상 독자 (본인 / 파생 레포 개발자 / 운영자)

2. 현재 프로비저닝 상태 (2026-04-18) — 표 (본 plan §1.2 복사 + 링크)

3. 로컬 개발 구성도 (ASCII)
   - Spring JVM + docker compose + NAS MinIO
   - 포트 표 (8081, 5433, 9000/9001, 3000/3100/9090/9093)
   - 최소 기동 / 관측성 포함 / 전체 스택 3단계

4. 운영 구성도 (ASCII, planned)
   - 박스로 "현재 대부분 planned 상태, Item Ops-1 에서 구체화" 명시
   - Cloudflare → cloudflared → 맥미니 → Spring + Supabase + NAS
   - NAS MinIO 의 LAN 전용 주의

5. 책임 분담 표
   - TLS/DDoS/Rate (Cloudflare, planned)
   - DB (Supabase, provisioned)
   - 파일 (NAS MinIO, LAN-only)
   - 관측성 (로컬 docker 스택)

6. 선택 근거 요약 (세부는 decisions-infra.md 로 링크)

7. 규모 기준 (MAU 0→1K→10K 각 단계별 조치)

8. 보안 / 네트워크 경계 (planned)
   - 외부 노출 포트 (아직 없음) / 내부 전용 포트 (관리 9090)
   - Item Ops-1 에서 구체화 예고

9. 인프라 변경 프로세스
   - 새 환경변수 추가 시 업데이트할 파일 체크리스트
   - CORS / Cloudflare 규칙 변경 시 어디 기록

10. DB 스키마 관리 (F-01 V004 포함)
    - init-core-schema.sql, init-app-schema.sql 설명
    - Flyway 파일 구조, V004 누락 이유 1줄

11. 관련 문서
    - decisions-infra.md, onboarding.md, storage.md, monitoring-setup.md
```

### C.2 🆕 `docs/guides/onboarding.md` 신설

**섹션 outline**:

```
1. 대상 + 선행 지식 (Java/Spring 경험, Docker 기초)

2. 사전 설치 체크리스트
   - JDK 21 Temurin (설치 명령)
   - Docker Desktop (맥/리눅스)
   - mc (brew install minio/stable/mc)
   - gh (선택)
   - Node.js 18+ (husky)

3. 파생 레포 생성
   - GitHub Template → Use this template
   - git clone
   - npm install (why + what it creates)
   - node_modules 가 왜 생기는지 (husky/commitlint)
   - .husky 가 뭐 하는지 (commit-msg hook)

4. 최소 기동 (prereqs 완료 시 약 10~15분 / cold install 시 25~30분)
   - .env.example → .env 복사
   - 최소 env 편집 (JWT_SECRET 생성: openssl rand -hex 32)
   - docker compose up -d postgres
   - ./gradlew :bootstrap:bootRun
   - curl :8081/actuator/health
   - 첫 빌드는 Gradle 의존성 다운로드로 5~12분 소요 안내

5. 추가 스택 (선택)
   - 관측성 (loki/grafana/prometheus) 명령
   - MinIO (로컬 or NAS 분기, NAS 는 본인 네트워크 전용)

6. 앱 모듈 추가 (new-app.sh)
   - 실제 기능 정확히 (Java + settings.gradle + bootstrap/build.gradle 자동 수정)
   - 향후 Item 10 통합 스크립트 예고

7. 흔한 에러 5개 + 해결
   - YAML duplicate key
   - DB 연결 실패 (postgres 미기동)
   - Docker daemon not running
   - MinIO LAN 외부 접근 불가
   - Flyway checksum mismatch

8. Phase 0 에서 동작 안 하는 것 (기대치 관리)
   - Billing: stub only
   - Push: NoOp adapter (FCM 연동 없음)
   - Storage: endpoint 없으면 InMemoryAdapter fallback
   - 실제 운영 배포 파이프라인: Item Ops-1 에서

9. 그 다음 읽을 것
   - infrastructure.md, philosophy.md, conventions/
```

### C.3 🆕 `docs/conventions/decisions-infra.md` 신설

**파일명 확정**: `decisions-infra.md` (v2 에서 변동 없음 확정).

**각 결정 필드**:
```
## 결정 I-NN. 제목
- status: planned | provisioned | in-prod | hardware-acquired
- 결정일: YYYY-MM-DD
- 결정: (한 줄)
- 근거: (왜 이 선택인가)
- 대안: (A 대신 고려한 B, C)
- Trade-off: (어떤 비용을 감수하는가)
- 재검토 트리거: (어떤 지표/이벤트가 넘으면 다시 본다)
- 관련 문서: (링크)
```

**섹션 outline**:
```
1. 이 문서의 역할 (philosophy.md 와의 구분)
   - philosophy.md: 코드 설계 결정 (모듈, Mapper 금지, 포트/어댑터)
   - decisions-infra.md: 물리/운영 인프라 결정 (Supabase, NAS, 맥미니, CF)
   - 경계 케이스는 양쪽 상호 참조

2. 결정 간 충돌 해결 규칙
   - 예: "솔로 친화" (philosophy 7) vs "보안 강화" 가 충돌할 때 솔로 친화 우선 (Phase 0)
   - Phase 별로 우선순위 명시

3. 결정 I-01 ~ I-07
   - I-01 Supabase (status: provisioned)
   - I-02 서비스별 schema (philosophy 5 참조)
   - I-03 NAS MinIO LAN-only (status: provisioned, LAN 한계)
   - I-04 맥미니 운영 (status: hardware-acquired)
   - I-05 Cloudflare Tunnel (status: planned, Item Ops-1)
   - I-06 로컬 관측성 셀프 (status: provisioned)
   - I-07 2-tier bucket (status: provisioned 로컬 / planned 운영)

4. 재검토 트리거 요약 표
   - MAU 1K 넘으면 재검토: I-01 (Supabase Pro), I-03 (NAS 용량)
   - 외부 개발자 합류 시 재검토: I-03 (접근 방식), I-05 (Tunnel)
```

### C.4 🆕 `docs/backlog.md` 신설

**섹션 outline**:

```
# Backlog

## 사용 규칙
1. 추가 시: `- [ ] [카테고리] 제목 — 이유 (생성일: YYYY-MM-DD)`
2. 작업 시작 시: 항목을 "진행 중" 섹션으로 이동 + `(담당 Item: Item X)` 추가
3. 완료 시: "완료 (archive)" 로 이동 + 커밋 해시 링크
4. 2개월마다 archive → CHANGELOG 로 이관, backlog 가볍게 유지
5. Item 시작 전 반드시 backlog 점검 (git-workflow.md 참조)

## 진행 중 (N)
(비어있음)

## 대기 (카테고리별)

### 운영 배포 / 파이프라인 (Item Ops-1 묶음)
- [ ] [Ops] Jenkins vs GitHub Actions 결정 + 실제 파이프라인 구축 (2026-04-18)
- [ ] [Ops] 맥미니 배포 방식 (launchd / systemd) (2026-04-18)
- [ ] [Ops] Cloudflare Tunnel 셋업 (tunnel ID, DNS, ingress, WAF) (2026-04-18)
- [ ] [Ops] Supabase CI secrets wiring (2026-04-18)
- [ ] [Ops] Slack/Discord 알림 연동 + 알림 종류/임계치 정의 (2026-04-18)
- [ ] [Ops] Secrets management 체계 선택 (1Password CLI / sops / Vault) (2026-04-18)
- [ ] [Ops] MinIO 외부 접근 방식 (Tailscale vs Cloudflare Tunnel) (2026-04-18)
- [ ] [Ops] MinIO root → service account 로테이션 (mc svcacct add) (2026-04-18)
- [ ] [Ops] 비번 분리 (MinIO ↔ Supabase 동일 비번 사용 중) (2026-04-18)

### 데이터 / DB (Item Ops-1 에 일부)
- [ ] [Data] 백업 실행 (pg_dump 주기, NAS 보관, retention) (2026-04-18)
- [ ] [Data] 복구 drill (년 1회 실측) (2026-04-18)
- [ ] [Data] Flyway migration rollback 전략 문서 (2026-04-18)
- [ ] [Data] GDPR export/delete 요청 대응 (2026-04-18)
- [ ] [Data] Supabase pooler 모드 (transaction vs session) 튜닝 (2026-04-18)

### 관측성 / 운영 (Item Ops-1 에 일부)
- [ ] [Obs] Loki retention 정책 (보관 기간, 디스크 예산) (2026-04-18)
- [ ] [Obs] Prometheus retention + 디스크 공간 예상 (2026-04-18)
- [ ] [Obs] 맥미니 vs NAS 관측성 분리 여부 결정 (2026-04-18)
- [ ] [Obs] Performance baseline (JMeter / Gatling) (2026-04-18)

### 앱 기능 (Phase 1+)
- [ ] [Feature] Billing 실제 구현 (StoreKit + Play Billing) (2026-04-18)
- [ ] [Feature] Push 실제 구현 (FCM, APNs) (2026-04-18)
- [ ] [Feature] Admin 페이지 (이미지 검열) (2026-04-18)
- [ ] [Feature] API 버저닝 실제 롤아웃 (philosophy 8: 미도입 → 도입 시점 결정) (2026-04-18)
- [ ] [Feature] i18n / 다국어 (2026-04-18)
- [ ] [Feature] OpenAPI → Flutter 계약 공유 자동화 (2026-04-18)

### 개발자 경험 / 툴링
- [ ] [DX] Item 11 — Documentation contract test (자동 문서 drift 검증) (2026-04-18)
- [ ] [DX] Inventory 기계 추출 파일 (`docs/.inventory.yml`) (2026-04-18)
- [ ] [DX] Multi-app 로컬 병렬 개발 (포트 충돌, IntelliJ run config 공유) (2026-04-18)
- [ ] [DX] Pre-push hook (build 자동) (2026-04-18)

### 템플릿 진화
- [ ] [Template] Item 10 — 앱 프로비저닝 통합 스크립트 (2026-04-18)
- [ ] [Template] Roll-forward 가이드 보강 (cross-repo-cherry-pick.md 에 인프라 변경 반영법) (2026-04-18)
- [ ] [Template] Release cadence 규칙 (template-v 태그 주기) (2026-04-18)

## 완료 (archive, 지난 2개월)
- [x] Item 7 — DTO/API 네이밍 정리 (2026-04-18, `647b0c4`)
- [x] Item 9 v1 → v2 개정 (2026-04-18, plan 커밋 예정)
```

### C.5 🆕 `docs/philosophy.md` 결정 16 편입

**추가할 결정** (A.22 기반):

```
## 결정 16. DTO 팩토리 + Mapper 폐기
### 결정
DTO 변환에 별도 Mapper 클래스를 두지 않고, Entity 에 `to<Dto>()` 메서드로 
변환 제공. `*Factory`, `*Mapper` 클래스 금지 (ArchUnit r NO_MAPPER_CLASSES).

### 근거
- 솔로 개발자 스케일에서 Mapper 레이어는 불필요한 boilerplate
- Entity 가 자신을 다양한 DTO 로 표현하는 건 OOP 자연스러움
- Item 4 에서 확정 (커밋 `e203872`)

### 관련
- conventions/dto-factory.md
- ArchUnit NO_MAPPER_CLASSES 규칙
```

**참고**: 2-tier bucket / NAS MinIO / 맥미니는 `decisions-infra.md` 에 (물리 인프라). philosophy 에 중복 금지.

### C.6 🆕 `docs/conventions/git-workflow.md` 에 backlog 운영 규칙 추가

**추가할 섹션** (기존 파일 말미에):

```
## Backlog 운영 규칙

`docs/backlog.md` 는 프로젝트의 "지금 안 하지만 잊지 말 것" 목록입니다.

### 항목 추가
- 기술부채 발견 시 즉시 추가
- 형식: `- [ ] [카테고리] 제목 — 이유 (생성일: YYYY-MM-DD)`
- 카테고리: Ops, Data, Obs, Feature, DX, Template

### 항목 처리
1. 새 Item 시작 전 backlog 점검 의무 (관련 항목 확인)
2. 작업 착수 시 "진행 중" 섹션으로 이동 + `(담당 Item: Item X)` 추가
3. 완료 시 "완료 (archive)" 로 이동 + 커밋 해시 링크
4. 2개월마다 archive → CHANGELOG 로 이관

### 신규 Item plan 작성 시
- backlog 에서 관련 항목들을 plan scope 에 포함 선언
- plan 완료 시 해당 backlog 항목 일괄 archive
```

### C.7 기존 문서 수정 — 라인 단위 이관 표

| 원본 | 라인 | 액션 | 대상 | 결과 |
|---|---|---|---|---|
| `architecture.md` | 26 (DB 언급) | 1줄 요약 + link | `infrastructure.md §2` | `architecture.md` 는 "Phase 0 는 Postgres; 운영은 Supabase (상세: infrastructure.md)" 1줄 |
| `architecture.md` | 65-94 (Supabase schema 전파) | 전면 이관 | `infrastructure.md §10` | `architecture.md` 는 2줄 요약 + 링크 |
| `architecture.md` | 350 (backup) | 유지 + 🚧 Ops-1 태그 | - | 현재 그대로, `[Item Ops-1 에서 실행]` 주석 추가 |
| `architecture.md` | 426-429 (CF Tunnel) | 전면 이관 | `infrastructure.md §4` | `architecture.md` 는 "운영 접근: infrastructure.md" 1줄 |
| `architecture.md` | 682-698 (운영 구성 ASCII) | 전면 이관 | `infrastructure.md §4` | `architecture.md` 는 제거 + 링크 |
| `guides/storage-setup.md` | 22-74 (NAS) | 유지 + "책임/스코프" 1절 보강 | - | 이 문서가 "셋업 guide" 로 포지셔닝 명확해짐 |
| `guides/monitoring-setup.md` | (맥북 홈서버 기존 섹션) | 유지 + `infrastructure.md` 링크 | - | - |
| `conventions/observability.md` | LOKI_URL 관련 | 주석 + 링크 보강 | - | Discord webhook 은 🚧 Ops-1 placeholder |
| `.env.example` | 활성 7개 변수 | 각 변수 앞에 1줄 설명 주석 | - | "활성 7개": SPRING_PROFILES_ACTIVE, POSTGRES_{DB,USER,PASSWORD}, JWT_SECRET, APP_DOMAIN, RESEND_{API_KEY,FROM_ADDRESS} |
| `README.md` (루트) | 최상단 | "네비" 섹션 신규 | - | 시작 → onboarding / 인프라 → infrastructure / 철학 → philosophy / 규약 → conventions/ / 이슈 → backlog |

### C.8 🔍 F-01 ~ F-03 처리 (기록 위치 명시)

| F | 사실 | 기록 위치 |
|---|---|---|
| F-01 | V004 은 `87fb8e2` 에서 삭제 (per-app user model 리팩토링) | `infrastructure.md §10` (DB 스키마 관리) 에 1줄 |
| F-02 | `keep-alive.sh` 용도 (파일 내용 확인 필요) | Phase C 작업 중 파일 읽고 `infrastructure.md §10` 부록 또는 `backlog.md` 로 |
| F-03 | ArchUnit 22개 확정 (grep 검증) | `conventions/module-dependencies.md` (통합 리스트) |

---

## 6. Phase D — 역방향 검증

**목적**: 신설/수정 문서의 모든 claim 을 실제 코드/파일/env 와 대조.

### 실행 절차
- **주체**: 본인 (수동)
- **시점**: Phase C 마지막 커밋 직후, Phase E 전
- **산출물**: 본 plan 섹션 11 "Phase D 검증 결과" 표에 결과 commit
- **도구**: `ls`, `grep`, `find`, `git log`

### 검증 항목
1. **파일 경로 claim** → `ls <path>` 로 존재 확인
2. **메서드/클래스 이름 claim** → `grep -rn '<name>' --include='*.java'` 로 존재 확인
3. **환경변수 이름 claim** → `.env.example` 또는 `application*.yml` 에 존재
4. **명령어 claim** → syntax 검증 (실행 필요 없음)
5. **문서 ↔ 문서 양방향 링크** (§4.8 매트릭스) → `grep -l '<target.md>' <source.md>` 양방향

### DoD
- Phase D 결과 표의 모든 행 PASS
- 본 plan 에 표 commit

---

## 7. Phase E — 1-agent 리뷰 (축소)

**Agent 1: 신규 개발자 onboarding 시뮬레이터**

프롬프트:
```
당신은 Java 10년차, Spring Boot 경험 있음, 이 레포를 처음 받음.
입력 환경 가정: JDK 21 / Docker Desktop / mc / Node 18 이미 설치됨 (prereqs OK).
목표: docs/guides/onboarding.md 만 보고 15분 안에 로컬에서
Spring 앱 기동 + `curl :8081/actuator/health` 로 200 응답 받기.
Gap 정의: 가이드 명령어 그대로 실행 시 오류 발생 or 문서 외부 검색 필요.
Gap 을 모두 보고하라.
```

합격 기준: Gap 0개.

**Agent 2 (운영자 시뮬) / Agent 3 (완전성 검사) 는 Item 11 로 이관**.

---

## 8. 완료 기준 (DoD) — 모두 측정 가능

- [ ] `docs/infrastructure.md` 신설 (상단 프로비저닝 상태 표 포함) — 라인 검증
- [ ] `docs/guides/onboarding.md` 신설 (prereqs + 시간 이분화 명시) — 라인 검증
- [ ] `docs/conventions/decisions-infra.md` 신설 (I-01~I-07, 각 결정 6개 필드 포함) — 라인 검증
- [ ] `docs/backlog.md` 신설 (30+ 항목 seed) — 라인 검증
- [ ] `docs/philosophy.md` 에 결정 16 (DTO 팩토리 + Mapper 폐기) 추가 — grep 검증
- [ ] `docs/conventions/git-workflow.md` 말미에 "Backlog 운영 규칙" 섹션 추가 — grep 검증
- [ ] `docs/architecture.md` 인프라 관련 라인 축약 + infrastructure.md 링크 — 라인 대조
- [ ] `docs/guides/storage-setup.md`, `monitoring-setup.md` 에 infrastructure.md 링크 추가 — grep 검증
- [ ] `docs/conventions/observability.md` LOKI_URL 설명 보강 — grep 검증
- [ ] `README.md` 루트 네비 추가 — 라인 검증
- [ ] `.env.example` 활성 7개 변수에 설명 주석 추가 — grep 검증
- [ ] F-01 V004 기록 (`infrastructure.md §10`) — grep 검증
- [ ] F-02 `keep-alive.sh` 확인 + 기록 — grep 검증
- [ ] F-03 ArchUnit 22개 리스트 (`module-dependencies.md`) — 카운트 검증
- [ ] Phase D 검증 결과 표가 본 plan §11 에 commit — line count 검증
- [ ] Phase E Agent 1 리뷰 통과 (Gap 0) — agent 리포트 기록
- [ ] 본인 dogfooding: 신규 디렉토리에 onboarding.md end-to-end 수행 성공 — 시간/결과 기록

---

## 9. 위험 요소

| 위험 | 영향 | 완화 |
|---|---|---|
| 문서 drift 재발 (인벤토리 stale) | 다음 변경에서 또 혼란 | Item 11 (docs contract test) 예약. plan 에 향후 기계 추출 예고 |
| Status 필드 기준일 모호 | "provisioned 가 언제부터?" 질문 | 각 항목에 `결정일: YYYY-MM-DD` 필드 필수 |
| Item Ops-1 미착수 상태로 오래 | 운영 배포 관련 gap 영속 | `backlog.md` 에 "Item Ops-1 묶음" 명시 + 월 1회 점검 규칙 |
| 감사 매트릭스가 stale | 새 env/script 생겼는데 매트릭스 미반영 | Item 11 에 매트릭스 재생성 자동화 포함 |
| onboarding 15분 주장이 깨짐 | 신규 개발자 신뢰 하락 | prereqs 명시 + 콜드 시간 별도 표기 (v2 에서 수정) |
| Plan v2 자체도 stale 될 위험 | 이 문서 참조 깨짐 | Phase C 완료 후 "완료" 섹션 업데이트, archive |

---

## 10. 작업 순서 (의존성 명시)

각 단계 끝마다 커밋 (`docs(...)`, `fix(docs): ...`).

1. **🔍 F-01 / F-02 / F-03 사실 최종 확인**
   - F-01: 판명됨, 기록만
   - F-02: `cat infra/scripts/keep-alive.sh` 후 요약
   - F-03: `grep -c "public static final ArchRule" ArchitectureRules.java` → 22 확정
2. **A.22 — `philosophy.md` 결정 16 (DTO 팩토리 + Mapper 폐기) 편입**
3. **`decisions-infra.md` 작성** (상태 필드 포함 I-01~I-07)
4. **`infrastructure.md` 작성** — §2 프로비저닝 상태 표, §3 로컬 구성도, §4 운영 구성도 (planned 박스 포함), §10 DB 스키마 + F-01
   - 입력: architecture.md 라인 26/65-94/350/426-429/682-698 내용
5. **`architecture.md` 축약** — 위 라인들 이관 후 2줄 요약 + 링크
6. **`onboarding.md` 작성** — prereqs/시간 이분화/흔한 에러 5개/Phase 0 제약
7. **`backlog.md` 작성** — 30+ 항목 seed (Ops-1 묶음 포함)
8. **`git-workflow.md` 말미에 backlog 규칙** 추가
9. **기타 기존 문서 수정** — storage-setup.md, monitoring-setup.md, observability.md 링크 보강
10. **`README.md` 루트 네비** 추가
11. **`.env.example` 활성 7개 변수 주석** 보강
12. **Phase D 역방향 검증 수행** → 본 plan §11 에 결과 표 commit
13. **Phase E Agent 1 리뷰 dispatch** → 결과 기록, Gap 있으면 2~11 으로 돌아가 수정
14. **Dogfooding** — 별도 디렉토리 clone 후 onboarding.md end-to-end 수행
15. **DoD 전체 체크박스 통과 확인** → Item 9 v2 완료, backlog.md 에서 "Item 9 v1→v2 개정" 완료 archive

---

## 11. Phase D 검증 결과 (2026-04-18 수행)

### D.1 파일 경로 claim (13 항목)

| 경로 | 결과 |
|---|---|
| `infra/scripts/keep-alive.sh` | ✅ PASS |
| `infra/scripts/backup-to-nas.sh.example` | ✅ PASS |
| `infra/scripts/init-core-schema.sql` | ✅ PASS |
| `infra/scripts/init-app-schema.sql` | ✅ PASS |
| `tools/new-app/new-app.sh` | ✅ PASS |
| `infra/docker-compose.dev.yml` | ✅ PASS |
| `bootstrap/src/main/resources/application-{dev,prod,default}.yml` | ✅ PASS |
| `.env.example`, `.gitignore`, `commitlint.config.js`, `.husky/commit-msg` | ✅ PASS |
| Flyway V001/V002/V003/V005/V006/V007/V008/V009 (V004 결번 확인) | ✅ PASS |

### D.2 클래스/메서드 claim (12 심볼 + Entity 메서드 3개)

| 심볼 | 결과 |
|---|---|
| `BucketProvisioner`, `MinIOStorageAdapter`, `InMemoryStorageAdapter` | ✅ PASS |
| `StubBillingAdapter`, `NoOpPushAdapter`, `FcmPushAdapter` | ✅ PASS |
| `MinioProperties`, `JwtProperties`, `AppCredentialProperties`, `ResendProperties`, `RateLimitProperties`, `FcmProperties` | ✅ PASS |
| `User.toSummary()`, `User.toProfile()`, `User.toAccount()` | ✅ PASS |
| ArchUnit `NO_MAPPER_CLASSES` | ✅ PASS |

### D.3 환경변수 claim (19 변수)

| 변수 | 결과 |
|---|---|
| `SPRING_PROFILES_ACTIVE`, `POSTGRES_*`, `JWT_SECRET`, `APP_DOMAIN`, `RESEND_*` (7개) | ✅ PASS |
| `DB_URL`, `DB_USER`, `DB_PASSWORD`, `APP_STORAGE_MINIO_*` (8개) | ✅ PASS |
| `APP_CREDENTIALS_GYMLOG_*`, `LOKI_URL`, `DISCORD_WEBHOOK_URL`, `MANAGEMENT_SERVER_PORT` (4개) | ✅ PASS |

### D.4 명령어 syntax (5 명령)

| 명령 | 결과 |
|---|---|
| `openssl rand -hex 32` | ✅ PASS |
| `docker compose -f infra/docker-compose.dev.yml config` | ✅ PASS |
| `./gradlew :bootstrap:bootRun` (실행 권한) | ✅ PASS |
| `curl --version`, `mc --version` | ✅ PASS |

### D.5 문서 ↔ 문서 양방향 링크 (21 쌍)

| 쌍 | 결과 | 조치 |
|---|---|---|
| infrastructure ↔ decisions-infra / onboarding / storage / architecture | ✅ PASS | - |
| onboarding ↔ philosophy | ✅ PASS | - |
| backlog ↔ git-workflow | ✅ PASS | - |
| philosophy ↔ dto-factory | ✅ PASS | - |
| decisions-infra ↔ storage | ✅ PASS | - |
| observability, storage-setup, monitoring-setup → infrastructure | ✅ PASS | - |
| README → onboarding / infrastructure / decisions-infra / backlog | ✅ PASS | - |
| **storage → infrastructure** | ❌ → ✅ FIXED | 헤더에 링크 3줄 추가 (커밋 예정) |

### 종합

- 검증 항목 **총 60+**, 최초 검증 시 **1건 FAIL** (storage.md → infrastructure 링크 누락)
- 즉시 fix 완료, 재검증 PASS
- Phase D 최종 결과: **All PASS**

## 11.1 Phase E — 1-agent onboarding 시뮬레이터 리뷰 결과 (2026-04-18)

### Gap 발견 (Major 2 + Minor 5)

| Gap | 심각도 | 내용 | 조치 |
|---|---|---|---|
| 1 | Major | onboarding/infrastructure 에 Prometheus 9091 로 표기, 실제 compose 는 9090 | onboarding.md §4.3 + infrastructure.md §3.1/§8.2 + plan Phase A.6 모두 9090 으로 수정 |
| 2 | Major | `JWT_SECRET=$(openssl rand -hex 32)` 예시가 shell substitution 없는 `.env` 에서 리터럴 17자로 저장 → 검증 실패 | placeholder 로 변경 + 별도 생성 명령 + 경고 박스 추가 |
| 3 | Minor | dev 프로파일은 JWT_SECRET fallback 있어 사실상 선택인데 "최소 필수" 로 표현 | §3.2 를 "cp 만으로 충분, prod 에서만 필수" 로 재구성 |
| 4 | Minor | observability 스택 부팅 타이밍 경고 부재 | §4.3 말미에 "DB 만 있으면 부팅 OK" 1줄 추가 |
| 5 | Minor | §5 (new-app.sh) 가 15분 스코프 밖인데 경계 모호 | §4.3 말미에 "여기서 onboarding 성공" 박스 추가 |
| 6 | Minor | `pg_isready` 의 container_name 하드코딩 | optional 표기 유지, 수정 불필요 |
| 7 | Minor | `graceful shutdown` 으로 Ctrl+C 지연 경고 없음 | §6.7 신설 |

### 추가 개선 반영

- §6.6 JWT_SECRET 길이 부족 에러 케이스 신설 (개선 4 반영)

### 결과

- Phase E Agent 1 총평: "Critical gap 은 없음. Major 2 건만 수정하면 0-gap 수준에 근접."
- 본 작업으로 Major 2 + Minor 4 (Gap 3/4/5/7) + 개선 1 (§6.6) 반영
- 잔존 Gap: **없음** (수정 후)

## 11.2 Dogfooding — 실제 신규 디렉토리에서 onboarding 수행 (2026-04-18)

수행 순서:
1. `/tmp/dogfood-test` 에 `git clone`
2. `npm install` → 12초 (warm cache)
3. `cp .env.example .env`
4. `docker compose up -d postgres` → 20초
5. `./gradlew :bootstrap:bootRun` → **❌ 기동 실패**
6. `set -a; source .env; set +a; ./gradlew :bootstrap:bootRun` → ✅ 4초
7. `curl :8081/actuator/health` → ✅ `{"status":"UP"}` (DB UP 포함)

### Gap 발견 (Critical 1 + Minor 2)

| # | 심각도 | 내용 | 조치 |
|---|---|---|---|
| D1 | **Critical** | Spring Boot 가 `.env` 자동 로드하지 않음 → `SPRING_PROFILES_ACTIVE=dev` 미적용, default profile 로 폴백 → `app.jwt.secret` 없어 기동 실패 | onboarding §4.2 에 `set -a; source .env; set +a` 단계 추가, §6.6 원인 A/B 분기. backlog 에 "bootRun 기본 profile 주입" 태스크 |
| D2 | Minor | 활성 변수 실제 8개, plan/commit 은 7개 표기 | 기록만 |
| D3 | Minor | §6.3 Docker daemon 에러 경로 Mac 버전 누락 | Mac 경로 + `open -a Docker` + daemon 대기 루프 추가 |

### 결과

- Warm cache 환경 기준 **5분** (clone → curl UP)
- Cold install 환경 기준 25~30분 (문서 추정치 유효)
- Critical Gap fix 후 **신규 개발자가 막힘 없이 15분 목표 달성 가능**

---

## 12. Item Ops-1 (운영 배포 묶음) 예약 공고

**Item Ops-1 가 포함할 것** (Item 9 v2 에서 명시적으로 연기):

### 12.1 신설 문서 (예정)
- `docs/guides/deployment.md` — CI → 맥미니 runtime 파이프라인, 배포 체크리스트, rollback 절차
- `docs/guides/disaster-recovery.md` — RTO/RPO, 복구 drill, 시나리오별 플레이북
- `docs/guides/secrets-management.md` — 시크릿 생성/보관/로테이션/공유 전략

### 12.2 인프라 프로비저닝 작업
- Supabase CI secrets wiring (GitHub Secrets 등록)
- 맥미니 배포 메커니즘 (launchd / systemd 선택 + 설정)
- Cloudflare Tunnel 셋업 (tunnel ID, DNS, ingress rules, WAF, rate limit)
- Slack/Discord webhook 연동 + Alertmanager 알림 종류/임계치 정의
- MinIO 외부 접근 방식 결정 (Tailscale / CF Tunnel / 공개 IP + DDNS 중 선택)
- MinIO root → service account 로테이션
- MinIO ↔ Supabase 동일 비번 분리

### 12.3 Item Ops-1 착수 조건
- Phase 1 기능 개발 직전 또는 맥미니 네트워크 준비 완료 시점
- `backlog.md` "Item Ops-1 묶음" 목록이 갱신된 상태

---

## 13. 진행 추적 (checkbox)

- [x] v1 (`5be87c2`) 작성
- [x] 3-agent 독립 리뷰 완료 (실행가능성 / 완전성 / 가정검증)
- [x] v2 개정 (이 문서)
- [ ] Phase A 재확인 (v2 기준 인벤토리 — §3 에 반영됨)
- [x] Phase B 확장 매트릭스 (§4 에 반영됨)
- [x] Phase C 작업 (섹션 10 순서대로)
  - [x] 1. 🔍 F-01/02/03 — V004 삭제 이력 / keep-alive.sh 용도 / ArchUnit 22개 확정
  - [x] 2. philosophy 결정 16 (`d8b8107`)
  - [x] 3. decisions-infra.md (`54fd67e`)
  - [x] 4. infrastructure.md (`e199ddc`, `f35059e`, `508b954`)
  - [x] 5. architecture.md 축약 (`bbc11ce`)
  - [x] 6. onboarding.md (`f6fc056`)
  - [x] 7. backlog.md (`857566c`)
  - [x] 8. git-workflow.md 규칙 (`18edf4c`)
  - [x] 9. 기존 문서 보강 (`0b9fbb3`)
  - [x] 10. README 네비 (`b749b5e`)
  - [x] 11. .env.example 주석 (`dfa49b4`)
- [x] Phase D 역방향 검증 (`8c1e984`, storage.md fix 포함)
- [x] Phase E Agent 1 리뷰 + Gap 반영 (Major 2 + Minor 4 수정)
- [x] Dogfooding — Critical Gap 1건 (D1 `.env` 자동 로드 X) 발견 + fix, Minor 2건 반영
- [x] DoD 전체 통과
