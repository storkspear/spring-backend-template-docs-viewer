# Legacy — 재작성 대기 중인 기존 결정들

> **이 파일의 위상**  
> 이 문서의 결정들은 **아직 ADR 카드 형식으로 재작성되지 않은 원본 콘텐츠** 입니다. 차후 세션에서 테마별로 하나씩 독립 파일 (예: `adr-005-db-schema-isolation.md`) 로 재작성되며, 여기서는 해당 항목이 제거됩니다.
>
> 즉 이 파일은 **점점 줄어드는 임시 공간** 이에요. 모든 재작성이 끝나면 이 파일 자체가 사라집니다.
>
> **재작성 진행 상황**:
> - ✅ 테마 1 (레포 구조): ADR-001, 002, 003, 004 — 완료
> - ✅ 테마 2 (모듈 내부 설계): ADR-009, 010, 011, 016 — 완료
> - ⏳ 테마 3 (데이터 & 테넌시): ADR-005, 012 — 예정
> - ⏳ 테마 4 (인증 & 보안): ADR-006, 013 — 예정
> - ⏳ 테마 5 (운영 & 개발 방법론): ADR-007, 008, 014, 015 — 예정
>
> **현재 이 파일에 남아있는 결정**: 5, 6, 7, 8, 12, 13, 14, 15

> **독자 유의사항**  
> 아래 콘텐츠는 **프롤로그 톤/깊이에 미달** 합니다. Options Considered 대안 검토가 얕고, Lessons Learned 가 누락되었으며, Code References 도 부실해요. ADR 카드로 재작성된 테마 1 의 [ADR-001~004](./README.md) 수준의 품질을 여기서 기대하지 마세요. 재작성이 끝나면 동일 깊이가 될 것입니다.

---

## 결정 5. 단일 Postgres database + 앱당 schema

> **이 섹션은 기존 '통합 계정' 모델에서 '앱별 독립 유저' 모델로 변경된 내용을 반영합니다.**
> users 테이블은 이제 `core` schema 가 아니라 각 앱 schema (`sumtally`, `rny` 등) 에 있습니다.

### 결정

모든 앱이 **하나의 Postgres database (`postgres`)** 를 공유하며, 각 앱은 자기 schema (`sumtally`, `rny`, `gymlog` 등) 를 가집니다.

각 앱 schema 는 **유저/인증 테이블과 도메인 테이블을 모두 포함**합니다. `core` schema 는 최소화되거나 비워질 수 있습니다.

```
postgres (database)
├── sumtally schema
│   ├── users                        ← sumtally 유저 (독립)
│   ├── social_identities
│   ├── refresh_tokens
│   ├── email_verification_tokens
│   ├── password_reset_tokens
│   ├── devices
│   ├── budget_groups                ← sumtally 도메인
│   ├── expenses
│   └── ...
├── rny schema
│   ├── users                        ← rny 유저 (독립, sumtally 와 별개)
│   ├── social_identities
│   ├── refresh_tokens
│   ├── ...
│   ├── asset_groups                 ← rny 도메인
│   └── ...
└── public schema                    ← 건드리지 않음 (Supabase 기본)
```

### 이유

**Supabase 의 구조적 제약입니다.** Supabase 는 `postgres` database 중심으로 설계되어 있으며, 부가 기능들(Auth, Storage, Realtime) 이 모두 이 database 의 schema 로 구현되어 있습니다. 추가 database 를 만드는 것은 제한되거나 대시보드가 제대로 인식하지 못합니다.

**schema 분리만으로도 충분한 격리가 가능합니다.** 다음 5중 방어선을 적용합니다.

1. **DB role 분리** — 각 앱 모듈은 자기 schema 에만 접근 권한을 가진 전용 role 로 접속 (`sumtally_app`, `gymlog_app` 등). 크로스 schema 접근은 DB 수준에서 permission denied.
2. **Spring DataSource 분리** — 앱별로 별도 HikariCP 커넥션 풀. 한 앱의 커넥션 고갈이 다른 앱에 영향 없음.
3. **Flyway 마이그레이션 분리** — 앱별 마이그레이션 히스토리 테이블 독립.
4. **포트 인터페이스 의존** — 앱 모듈은 자기 schema 의 엔티티만 소유.
5. **ArchUnit 규칙** — 크로스 모듈 엔티티 참조 금지.

### `new-app.sh` 가 자동 생성하는 마이그레이션

새 앱 추가 시 `./tools/new-app.sh <slug>` 를 실행하면 해당 앱 schema 아래에 V001~V006 마이그레이션이 자동 생성됩니다.

```
apps/app-<slug>/src/main/resources/db/migration/<slug>/
    V001__init_users.sql
    V002__init_social_identities.sql
    V003__init_refresh_tokens.sql
    V004__init_email_verification_tokens.sql
    V005__init_password_reset_tokens.sql
    V006__init_devices.sql
```

### 트레이드오프

단일 database 는 "한 Postgres 인스턴스의 장애가 모든 앱을 다운시킴" 을 의미합니다. 그러나 우리는 Supabase (관리형) 를 사용하므로 인스턴스 운영 자체가 Supabase 책임이며, 실제 장애율은 낮습니다. 필요한 시점(특정 앱이 진짜 독립 운영이 필요할 때) 에는 pg_dump 로 해당 schema 만 떼어 내 별도 Postgres 인스턴스로 이전할 수 있습니다.

---

## 결정 6. HS256 JWT (대칭키)

### 결정

JWT 서명 알고리즘으로 HS256 (대칭키) 를 사용합니다.

### 이유

우리는 단일 모놀리스 JVM 안에서 토큰 발급과 검증이 모두 일어납니다. 발급자와 검증자가 같은 프로세스이므로 같은 비밀 키를 공유하는 것이 자연스럽습니다.

### 대안 검토

**RS256 (비대칭키)**
- 장점: 개인키로 서명, 공개키로 검증. 공개키를 여러 서비스에 배포해서 독립 검증 가능.
- 사용 맥락: 마이크로서비스에서 여러 서비스가 JWT 를 독립 검증해야 할 때.
- 우리에겐 과잉: 우리는 단일 JVM 이므로 공개키 배포의 이점이 없습니다.

HS256 이 더 단순하고 빠릅니다. 운영할 것은 비밀 키 하나뿐입니다.

### 트레이드오프

HS256 의 단점은 비밀 키가 유출되면 누구든 토큰을 위조할 수 있다는 것입니다. 이것은 시크릿 관리로 대응합니다 (`~/.factory/secrets.env`, GitHub Actions Secrets, 평문 커밋 금지).

---

## 결정 7. 솔로 친화적 운영

### 결정

모든 운영 결정은 **솔로 한 사람이 감당 가능한가** 를 기준으로 판단합니다.

### 구체 적용 예시

**단일 배포 단위** — bootstrap JAR 한 개만 배포합니다. 여러 서비스를 동시에 배포하지 않습니다.

**관리형 서비스 선호** — Postgres 는 Supabase, 이메일은 Resend, 푸시는 FCM, 스토리지는 Cloudflare R2. 직접 운영하는 것은 Spring Boot 프로세스와 몇 개의 bash 스크립트뿐입니다.

**로컬 개발 우선** — 개발은 로컬 Docker Postgres 에서 하며, 프로덕션에서 실험하지 않습니다. `application-dev.yml` 과 `application-prod.yml` 을 명확히 분리합니다.

**코드가 문서** — 새 앱 추가는 `./tools/new-app.sh <slug>` 한 줄. README 를 길게 쓰기보다 스크립트를 완성해두는 것을 우선합니다.

**CI 는 빨간불 아니면 초록불** — 회색 지대(경고 무시, 일부 테스트 스킵) 를 만들지 않습니다. 빨간불이면 머지 금지.

### 비목표

이 제약의 뒷면은 다음이 **우리 목표가 아니다** 라는 것입니다.

- **고가용성 99.99% SLA** — 인디 스케일에서는 99% 면 충분합니다.
- **전 세계 멀티 리전** — 국내 유저 대상이므로 Seoul 리전 하나면 충분합니다.
- **무중단 배포** — 짧은 재시작 다운타임 (30초) 은 수용합니다.
- **마이크로서비스 분산 추적** — 단일 프로세스라 필요 없습니다.

이것들은 "중요하지 않다" 가 아니라 **"우리 단계에서는 필요하지 않다"** 입니다. 필요해지는 시점이 오면 그때 추가합니다.

---

## 결정 8. API 버전 관리는 Phase 0 에서 미도입

### 결정

API 엔드포인트에 `/v1/` 같은 버전 접두사를 붙이지 않습니다. 현재 경로는 `/api/core/users/me`, `/api/apps/<slug>/...` 형태입니다.

### 이유

API 버전 관리가 필요한 상황은 **"클라이언트를 서버 측에서 통제할 수 없을 때"** 입니다. 공개 API (카카오맵, Twitter API 등) 는 외부 개발자가 어느 버전을 쓰는지 모르니까 v1/v2 를 공존시켜야 합니다.

우리 상황은 서버와 클라이언트(Flutter 앱) 를 **같은 사람이 운영**합니다. API 가 바뀌면 서버 + 앱을 같이 배포하면 끝입니다. 서로 다른 API 버전이 공존할 필요가 없습니다.

### 미래 대응

버전 관리가 필요해지는 시점이 오면 (외부 소비자 등장, 멀티 버전 앱 공존 등):
- Cloudflare 리버스 프록시에서 경로 재작성 (`/api/v1/*` → `/api/*`)
- 또는 `@RequestMapping` prefix 를 `api/v1` 로 변경 (한 줄)

---

## 결정 12. 앱별 독립 유저 모델 (통합 계정 폐기)

### 결정

각 앱은 **자기 schema 에 독립된 users 테이블을 가집니다.** 같은 이메일이 `sumtally.users` 와 `rny.users` 에 별개의 레코드로 존재할 수 있습니다. 통합 계정(`core.users` + `core.user_app_access`) 은 폐기합니다.

### 이유

**UX 관점** — 유저는 각 앱을 독립된 서비스로 인식합니다. 가계부 앱에 가입했다고 해서 자동으로 다른 앱에도 계정이 생기는 것은 어색합니다. "sumtally 에서 쓰던 계정으로 rny 에 로그인" 이라는 플로우는 설명이 필요하고, 설명이 필요한 UX 는 나쁜 UX 입니다.

**프라이버시 관점** — 통합 계정은 앱 간 데이터가 같은 user_id 로 연결됨을 의미합니다. GDPR/개인정보 관점에서 "이 앱에서 탈퇴하면 모든 앱에서 사라지는가" 같은 복잡한 질문이 생깁니다. 독립 유저 모델에서는 각 앱 탈퇴가 그 앱 데이터만 삭제합니다.

**운영 단순성** — `user_app_access` 테이블 관리, JWT `apps` claim 생성/검증, 멀티테넌트 DataSource 라우팅 등 통합 계정이 만들어내는 복잡성이 제거됩니다.

**GDPR 단순성** — 앱별 독립 데이터이므로 "데이터 삭제 요청" 이 앱 단위로 처리됩니다. 교차 앱 데이터 연결을 추적할 필요가 없습니다.

### 폐기된 개념들

| 폐기 | 대체 |
|---|---|
| `core.users` (공유 유저 테이블) | `<slug>.users` (앱별 독립 테이블) |
| `core.user_app_access` | 없음 (앱에 유저가 있으면 접근 권한 있음) |
| JWT `apps` claim (배열) | JWT `appSlug` claim (단일 문자열) |
| `/api/core/auth/*` 전역 엔드포인트 | `/api/apps/<slug>/auth/*` 앱별 엔드포인트 |
| 멀티테넌트 DataSource 라우팅 | 앱 모듈이 자기 DataSource 직접 사용 |

### 크로스 앱 통합의 미래 대응

"미래에 Marvel universe 처럼 앱들이 연동되면?" 이라는 질문이 있을 수 있습니다. 그 시점이 오면:

1. 각 앱에 `linked_account_id` 컬럼 추가 (optional)
2. 별도 `core.linked_accounts` 테이블로 크로스 앱 매핑 관리
3. 유저가 **명시적으로** 계정 연동을 선택

지금 당장 이 복잡성을 도입할 이유가 없습니다. YAGNI.

### `AppSlugVerificationFilter`

JWT 의 `appSlug` claim 과 URL path 의 `{slug}` 가 다를 경우 즉시 403 을 반환하는 필터입니다. 예를 들어 sumtally 에서 발급된 JWT 로 `/api/apps/rny/...` 를 호출하면 차단됩니다. 이것은 앱 간 JWT 오용을 방지하는 마지막 방어선입니다.

---

## 결정 13. 앱별 인증 엔드포인트 (core-auth 는 라이브러리 역할)

### 결정

인증 엔드포인트는 `/api/apps/<slug>/auth/*` 패턴을 사용합니다. 각 앱 모듈이 자신의 `AuthController` 를 가지며, 실제 인증 로직은 `core-auth-impl` 서비스에 위임합니다.

### 기존 방식과의 비교

| 항목 | 기존 방식 | 새 방식 |
|---|---|---|
| 엔드포인트 | `/api/core/auth/email/signup` | `/api/apps/<slug>/auth/email/signup` |
| 런타임 Controller 위치 | `core-auth-impl/controller/AuthController` (활성) | `apps/app-<slug>/auth/<Slug>AuthController` (활성) — core-auth-impl 의 동일 파일은 스캐폴딩 소스로만 잔존 (런타임 bean 아님) |
| DataSource 결정 | ThreadLocal 라우팅 (AbstractRoutingDataSource) | 앱 모듈 자체 DataSource 직접 주입 |
| 앱 식별 | 요청 파라미터 또는 헤더 | URL path (`<slug>`) |

### 멀티테넌트 라우팅 제거

기존 통합 계정 모델에서는 `POST /api/core/auth/email/signup` 으로 들어오는 요청이 "어느 앱의 가입인지" 를 런타임에 구분해야 했습니다. 이를 위해 `AbstractRoutingDataSource` + `ThreadLocal` 조합을 사용하거나, 요청 body/header 에 `appSlug` 를 별도 포함시켜야 했습니다.

이 방식의 문제:
- `ThreadLocal` 은 비동기 처리(`@Async`, `CompletableFuture`, Virtual Thread) 에서 컨텍스트가 누출되거나 소실됩니다.
- Spring Security 필터 체인 + `ThreadLocal` 상태 관리가 복잡해집니다.
- 코드에 "어느 DataSource 를 써야 하나" 를 주입해야 하는 복잡성이 모든 Repository 에 전파됩니다.

새 모델에서는 URL path 의 `{slug}` 가 곧 "어느 앱의 요청인지" 를 결정하며, 해당 앱 모듈의 Controller 가 자기 DataSource 를 직접 사용합니다. Spring 의 DI 만으로 해결되며 `ThreadLocal` 이 필요 없습니다.

### `new-app.sh` 자동 생성

`./tools/new-app/new-app.sh <slug>` 실행 시 해당 앱의 `<Slug>AuthController` 가 `apps/app-<slug>/auth/` 에 자동으로 스캐폴드됩니다. 인증 엔드포인트를 손으로 작성할 필요가 없습니다. 생성 시의 "템플릿 소스" 는 `core-auth-impl/controller/AuthController.java` 의 구조를 참조하지만, 그 파일 자체는 **런타임 bean 으로 등록되지 않습니다** (`AuthAutoConfiguration` 이 더 이상 `@Import` 하지 않음). 따라서 template 상태 (앱 0개) 에선 인증 엔드포인트가 노출되지 않고, 앱이 추가될 때마다 해당 slug 의 엔드포인트만 활성화됩니다.

---

## 결정 14. Delegation mock 테스트를 쓰지 않는다

### 결정
테스트는 Port 의 **외부 관측 가능한 행위** 를 검증합니다. 내부 서비스 간 delegation 을 mock 으로 검증하지 않습니다.

### 이유
"A 가 B.foo() 를 호출하는가" 를 mock 으로 검증하는 테스트는 **구현 내부(how)** 에 결합됩니다. B 를 인라인화하거나 이름을 바꾸면 행위 불변이어도 테스트가 깨집니다. Port 계약 테스트가 같은 행위를 더 강하게 검증합니다 (B 가 실제로 작동하는지 간접 확인).

Port 패턴의 원래 목적인 "계약으로 격리" 와 정렬됩니다.

### 트레이드오프
내부 엣지 케이스 (특정 서비스 호출 여부) 를 직접 단언 불가 — Port 관점 행위로 재표현 필요. 일부 케이스는 표현이 길어지나, 테스트의 탄력성(내부 구조 변경에 안 깨짐)이 더 중요.

**유지되는 단위 테스트**: Port 계약으로 환원되지 않는 고유 알고리즘 (RefreshToken 회전, Apple JWKS 검증, JWT 서명 등) 은 계속 단위 테스트로 검증. 자세한 구분은 [`testing/contract-testing.md`](../testing/contract-testing.md).

---

## 결정 15. Conventional Commits + 템플릿 전체 semver

### 결정
- 모든 커밋에 Conventional Commits 포맷 강제 (commitlint + CI).
- Git 태그는 `template-v<major>.<minor>.<patch>` — **템플릿 레포 전체** 단위.
- CHANGELOG 는 Keep a Changelog 포맷. 모든 PR 이 `[Unreleased]` 섹션 업데이트.
- Breaking change 는 Deprecation 프로세스 경유 (최소 1 minor 주기 유예).

### 이유
**파생 레포 전파의 실효성 확보**. 파생 레포는 Use this template 모델로 git 히스토리가 분리됨. cherry-pick 이 유일한 전파 수단. Conventional Commits 는 "어느 커밋이 공통 코드 개선인지" 를 기계가 읽게 해줌 (`git log template-v0.3.0..v0.4.0 --grep="^feat\\|^fix"`).

**모듈별 버전이 아닌 템플릿 전체 버전** 인 이유: 모듈 간 의존 그래프가 연관되어 있음 (auth ↔ user), 솔로 운영에서 5개 버전 동기화 추적 부담 초과. 파생 레포는 "template-v0.3.0 기반" 한 줄로 단순 추적.

**Deprecation 경유 breaking**: 파생 레포가 따라올 시간 확보. 갑작스러운 major bump 는 "나중에 업그레이드 포기" 로 귀결.

### 트레이드오프
- 초기 도구 설정 (commitlint, husky, workflows) 필요 — 1회성.
- 학습 곡선: 개발자가 `feat:`, `fix:` 등에 익숙해져야 함. `.gitmessage` + Commitizen 으로 완화.
- 모듈별 세밀 버전의 손실 — "이 모듈만 업그레이드" 불가. 하지만 이 프로젝트 스케일에선 불필요.

---

