# Repository Philosophy

이 문서는 `spring-backend-template` 이 왜 현재의 구조를 가지게 되었는지 설명합니다.

각 결정은 추상적인 이론이 아니라 **솔로 인디 개발자가 여러 앱을 빠른 주기로 출시할 때 마주치는 구체적인 고통**에 대한 답변으로 만들어졌습니다.

---

## 맥락: 앱 공장 전략

이 레포지토리는 **"한 사람이 여러 앱을 고 cadence 로 찍어내는"** 작업 방식을 전제로 합니다. 이 작업 방식이 전제가 되면 다음 제약이 자동으로 따라옵니다.

**운영 가능성이 최우선 제약입니다.** 한 사람이 10개 앱을 동시에 운영한다면, 앱 1개당 운영 부담이 조금만 커져도 전체가 무너집니다. 그래서 "기술적으로 멋있는가" 보다 "솔로가 감당 가능한가" 가 설계 기준입니다.

**시간이 가장 희소한 자원입니다.** 돈은 0에 가깝게 만들 수 있지만 (Supabase Free + 맥미니 + Cloudflare Tunnel + NAS 등), 개발자 1명의 시간은 복제 불가능합니다. 그래서 매번 재구현되는 공통 작업(인증, 유저 관리, 푸시, 결제) 을 반드시 한 번만 잘 만들고 재사용해야 합니다.

**앱 1개의 성공 확률은 낮지만 비용이 0이면 많이 시도할 수 있습니다.** 복권 사기 모델입니다. 이 때문에 새 앱 출시 비용을 극단적으로 낮추는 것이 본 템플릿의 존재 이유입니다.

---

## 결정 1. 모듈러 모놀리스 (Modular Monolith)

### 결정

하나의 Spring Boot JAR 안에 여러 앱 모듈을 공존시키되, Gradle 모듈 경계로 격리합니다.

### 이유

솔로 개발자가 앱 10개를 운영할 때, 각 앱이 독립된 백엔드 서버라면 10개의 프로세스, 10개의 배포 파이프라인, 10개의 모니터링 대시보드가 필요합니다. 이것은 솔로 운영 불가능한 수준의 부담입니다.

모놀리스는 배포 1벌, 모니터링 1벌, 프로세스 1개로 끝납니다. 대신 내부적으로는 모듈 경계를 강제해서 "폴더만 나눠서 섞여버리는" 문제를 피합니다.

### 대안 검토

**마이크로서비스 (앱당 독립 백엔드)**
- 장점: 진짜 프로세스 격리, 독립 스케일링
- 탈락 이유: 10개 서버 운영은 솔로 불가능

**단일 Spring Boot, 폴더만 분리 (비모듈화)**
- 장점: 가장 단순
- 탈락 이유: 실수로 앱 코드끼리 얽히기 시작하면 분리가 사실상 불가능. 나중에 한 앱만 떼어내고 싶어질 때 길이 막힙니다.

**공통 코드를 JAR 라이브러리로 분리 + 앱당 독립 백엔드**
- 장점: 공통 코드 재사용
- 탈락 이유: 유저/결제 같은 "상태를 가진 공통 기능" 을 해결하지 못합니다. 각 앱이 자기 users 테이블을 복제하게 됩니다.

### 트레이드오프

모듈러 모놀리스의 단점은 "한 앱의 버그가 전체 JVM 을 죽일 수 있다" 는 것입니다. 이것은 실제 제약이지만, 인디 스케일에서는 충분한 모니터링과 서킷 브레이커로 완화 가능한 수준입니다. 진짜 프로세스 격리가 필요한 시점이 오면 (특정 앱이 MAU 100만 이상) 그때 해당 앱 모듈만 독립 서비스로 추출하면 됩니다. 그 추출을 가능하게 하는 장치가 결정 3(포트 인터페이스 분리) 입니다.

---

## 결정 2. GitHub Template Repository 패턴

### 결정

이 레포는 **직접 개발되지 않는 공통 뼈대 템플릿**입니다. 실제 개발 작업은 `Use this template` 으로 만든 파생 레포에서 진행합니다.

### 이유

**이유 A. 비즈니스 로직은 도메인 종속적입니다.** 가계부 앱의 로직을 운동 앱에 재사용할 수 없습니다. 한 레포에 여러 도메인을 섞으면 나중에 어느 하나도 다른 도메인에 재사용할 수 없어집니다.

**이유 B. 팀 경계에서 백엔드가 분리되어야 합니다.** 외부 팀과 협업할 때 같은 백엔드 서버를 공유할 수 없습니다. 팀 A 의 배포가 팀 B 를 중단시키면 안 됩니다.

**이유 C. 규모 경계에서 분리가 필요할 수 있습니다.** 한 앱이 성공해서 독립 운영이 필요해지면, 그 앱만 별도 백엔드로 빼야 합니다.

**이유 D. 템플릿이 순수해야 어느 도메인으로든 시작할 수 있습니다.** 템플릿에 특정 앱/팀/회사의 흔적이 박히면 다른 맥락에서 쓸 때 불편합니다.

### GitHub Fork 와의 차이

GitHub 에는 두 가지 다른 기능이 있습니다. 이 템플릿은 **후자** 를 사용합니다.

- **Fork** — 원본과 git 수준에서 연결됨. 원본에 PR 을 보낼 수 있음. 한 계정당 1개만 가능. 오픈소스 기여 모델.
- **Use this template** — 파일만 복제됨. 원본과 git 수준의 연결 없음. 무제한 생성 가능. 시작점 복제 모델.

우리는 공통 코드를 "시작점" 으로 제공하되, 이후엔 각 파생 레포가 독립적으로 진화하기를 원하므로 Template 패턴이 맞습니다.

### 공통 코드 전파 방식

템플릿에 개선이 생겼을 때 기존 파생 레포들에 전파하는 방법은 **수동 cherry-pick** 입니다. git remote 로 파생 레포끼리 연결한 후 `git cherry-pick <commit>` 으로 원하는 커밋만 가져옵니다. 자동 전파는 없습니다. 이것은 의도된 설계입니다. 각 파생 레포가 자기 속도로 이행하며, 원치 않는 변경이 강제되지 않습니다.

### 커밋 위생의 중요성

cherry-pick 이 깔끔하게 작동하려면 **"공통 코드 수정" 과 "도메인 코드 수정" 이 같은 커밋에 섞이지 않아야** 합니다. 한 커밋은 한 논리적 변경만 포함해야 합니다. 이 규칙을 어기면 backport 시 불필요한 도메인 코드가 템플릿에 딸려갑니다.

---

## 결정 3. `core/` 모듈을 `-api` / `-impl` 로 분리

### 결정

`core-auth`, `core-user`, `core-push` 같은 플랫폼 모듈을 두 개의 Gradle 모듈로 나눕니다.

- `core-auth-api` — 인터페이스와 DTO 만
- `core-auth-impl` — 실제 구현 (Spring 빈, JPA 엔티티, 비즈니스 로직)

앱 모듈은 `-api` 만 의존하고, `-impl` 에는 접근할 수 없습니다.

### 이유

**미래의 자유도를 위한 보험입니다.** 지금은 모든 것이 단일 JAR 안에서 메서드 호출로 통신합니다. 그러나 언젠가 한 앱이 대박 나서 독립 서비스로 추출해야 할 때가 옵니다.

만약 앱 모듈이 `core-auth-impl` (실제 구현 클래스) 를 직접 의존했다면, 추출 시점에 두 가지 선택만 남습니다.

- (a) `core-auth` 코드를 통째로 복사해서 새 레포에 가져가기 → 두 곳에서 같은 코드를 유지해야 하는 지옥
- (b) 모든 `core-auth` 호출 지점을 찾아서 HTTP REST 클라이언트로 교체 → 수십~수백 곳 리팩토링

대신 앱 모듈이 `core-auth-api` (인터페이스) 만 의존한다면, 추출 시점에 다음으로 끝납니다.

- Spring 이 주입하던 `AuthServiceImpl` (같은 JVM) 을 `AuthHttpClient implements AuthPort` (HTTP 호출) 로 교체
- 앱 코드는 한 줄도 바뀌지 않음

이 패턴은 "포트/어댑터 패턴" 의 적용이며, 미래의 자유도를 위해 지금 약간의 추가 파일(인터페이스 모듈) 을 받아들이는 거래입니다.

### 트레이드오프

`-api` / `-impl` 분리는 초기 설정이 약간 복잡합니다. 모듈 수가 2배가 되고, 인터페이스와 구현체를 별도로 관리해야 합니다. 그러나 이 비용은 "나중에 추출하기 쉽다" 는 보험 가치에 비해 무시할 수 있는 수준입니다.

---

## 결정 4. Gradle 모듈 경계로 의존 강제

### 결정

단순한 폴더 분리가 아니라 **Gradle 모듈** 로 앱과 코어를 분리합니다. 이 경계는 빌드 시스템 수준에서 강제됩니다.

### 이유

폴더만 분리하면 개발자가 실수로 경계를 넘을 수 있습니다.

```
// apps/app-sumtally 에서 실수로
import com.factory.apps.rny.SomeUtility;  // 폴더만 분리라면 가능
```

이렇게 한 번 허용되면 두 앱의 코드가 서로 얽혀서 나중에 어느 하나도 분리할 수 없게 됩니다.

Gradle 모듈은 `build.gradle` 에 선언된 의존성만 import 할 수 있습니다. `app-sumtally/build.gradle` 에 `app-rny` 가 의존성으로 없으면, 해당 패키지를 import 하는 순간 컴파일 에러가 납니다.

### ArchUnit 으로 추가 강제

Gradle 의존성만으로 막기 어려운 규칙은 ArchUnit 테스트로 CI 에서 강제합니다.

- `apps/*` 는 `core-*-impl` 에 접근 금지 (오직 `-api` 만)
- `apps/*` 끼리 참조 금지
- 엔티티는 자기 모듈 외부로 노출되지 않음

이 테스트는 CI 단계에서 실행되며, 위반 시 빌드 실패합니다. 사람 의지가 아니라 기계가 막아줍니다.

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

## 결정 9. BaseEntity 공통 슈퍼클래스 도입

### 결정

모든 JPA 엔티티가 공유하는 필드(`id`, `createdAt`, `updatedAt`) 와 감사 로직(`@PrePersist`, `@PreUpdate`, `equals`/`hashCode`) 을 `@MappedSuperclass BaseEntity` 로 집중화합니다.

### 이유

Phase D, E 를 구현하면서 User, RefreshToken, EmailVerificationToken, PasswordResetToken 등 모든 엔티티가 같은 6 개 필드 + 2 개 콜백 + equals/hashCode 를 각자 따로 선언하고 있었습니다. 엔티티 수가 늘어나면 복사 실수가 필연적이고, 감사 로직 변경 시 N 곳을 수정해야 합니다. BaseEntity 로 한 번 잡으면 이후 모든 엔티티가 자동 상속합니다.

### 위치

`common-persistence` 모듈에 위치합니다. JPA 어노테이션에 의존하므로 `common-web` 에는 넣을 수 없습니다.

---

## 결정 10. 공통 조회 조건 인프라 (SearchCondition + QueryDslPredicateBuilder)

### 결정

목록 조회 API 에서 프론트엔드가 보내는 검색 조건을 **Map<String, Object> 기반**으로 표준화합니다. 백엔드는 이 Map 을 `QueryDslPredicateBuilder` 로 자동 변환하여 동적 WHERE 절을 생성합니다.

### 이유

모든 목록 조회 API 가 반복하는 패턴 (필드별 if 조건 → 쿼리 추가) 을 한 번에 해결합니다. 프론트엔드는 `{field}_{operator}: value` 형식의 Map 을 보내면 되고, 백엔드는 `QueryDslPredicateBuilder.buildConditions(conditions, QEntity.entity)` 한 줄로 WHERE 절을 완성합니다. 각 앱 모듈이 동일한 패턴으로 조회 API 를 구현하므로 프론트엔드의 payload 일관성이 보장됩니다.

### 구조

순수 Java DTO 와 QueryDsl 변환을 분리합니다:
- `common-web/search/` — `SearchCondition`, `SortSpec`, `SearchRequest` (QueryDsl 비의존, 순수 Java)
- `common-persistence/` — `QueryDslPredicateBuilder`, `QueryDslSortBuilder` (QueryDsl 의존)

이렇게 분리하면 web 계층의 DTO 는 QueryDsl 을 몰라도 되고, QueryDsl 변환 로직은 JPA 모듈만 사용합니다.

### Map 기반 조건 규칙

| 키 형식 | 의미 | 예시 |
|---|---|---|
| `field_eq` | 일치 | `"categoryId_eq": 5` |
| `field_gte` / `field_lte` | 이상 / 이하 | `"amount_gte": 10000` |
| `field_gt` / `field_lt` | 초과 / 미만 | `"age_gt": 18` |
| `field_like` | 부분 매칭 (대소문자 무시) | `"title_like": "커피"` |
| `field_isNull` / `field_isNotNull` | null 여부 | `"deletedAt_isNull": true` |

현재 `QueryDslPredicateBuilder` 가 지원하는 연산자는 위 8가지입니다.

### 대안 검토

**타입 세이프 Condition DTO** (`ExpenseSearchCondition(Long categoryId, Integer amountMin, ...)`)
- 장점: 컴파일 타임 검증
- 탈락 이유: 조건 추가할 때마다 DTO 수정 필요. 앱마다 조건이 다른 공장 패턴에서 확장성 떨어짐.

**하이브리드** (기본은 Map, 복잡한 쿼리는 커스텀)
- 실제 운영에서는 이 방식이 될 것이지만, 인프라 수준에서는 Map 기반이 기본이고, 복잡한 쿼리는 각 앱 모듈의 커스텀 Repository 에서 수행합니다.

---

## 결정 11. 모듈 안 레이어드 아키텍처 + 포트/어댑터 패턴

> **이 섹션은 기존 '통합 계정' 모델에서 '앱별 독립 유저' 모델로 변경된 내용을 반영합니다.**
> 런타임에 활성화되는 AuthController 는 각 앱 모듈(`apps/app-<slug>`) 에 위치합니다.
> `core-auth-impl` 은 서비스 로직 라이브러리 + `new-app.sh` 가 참조할 스캐폴딩 소스만 제공하며,
> 그 내부의 `AuthController.java` 파일은 **런타임에 Spring bean 으로 등록되지 않습니다**
> (과거엔 `@Import` 로 등록됐으나 drift 해소를 위해 2026-04-20 제거).

### 구조

각 `core-*-impl` 모듈 내부는 레이어드 아키텍처를 따릅니다:

```
core-auth-impl/               ← 인증 로직 라이브러리 (런타임 Controller 없음)
├── service/        ← 비즈니스 계층 (EmailAuthService, AppleSignInService 등)
├── entity/         ← JPA 엔티티 (RefreshToken 등, 앱 schema 에 매핑)
├── repository/     ← 데이터 접근 계층
├── email/          ← 이메일 어댑터
├── config/         ← Spring 설정 (AuthAutoConfiguration — Controller 등록 안함)
└── controller/
    └── AuthController.java   ← ⚠️ 스캐폴딩 소스 only. AuthAutoConfiguration 이 @Import
                                  하지 않으므로 런타임 빈 아님. `new-app.sh` 가 이 패턴을
                                  참고해 앱 모듈의 <Slug>AuthController 를 생성.

apps/app-<slug>/              ← 앱별 모듈 (런타임 AuthController 여기)
├── controller/                ← (health 같은 앱 전용)
├── auth/
│   └── <Slug>AuthController.java   ← /api/apps/<slug>/auth/* 실제 엔드포인트
├── service/        ← 앱별 도메인 서비스
├── entity/         ← 앱별 도메인 엔티티
└── ...
```

모듈 경계가 도메인 경계와 일치하고, 모듈 안에서는 전통적 레이어로 나뉩니다. 이것은 Spring Boot 멀티모듈 프로젝트의 가장 일반적인 Best Practice 입니다.

> **Template 상태 (앱 0개)**: 인증 엔드포인트가 런타임에 노출되지 않습니다 (AuthController 등록 안됨). `new-app.sh <slug>` 실행해 첫 앱 모듈 추가하는 순간부터 해당 slug 의 엔드포인트가 활성화됩니다.

### AuthController 를 앱 모듈에 두는 이유

기존에는 `core-auth-impl` 안에 `AuthController` 가 있었고, `/api/core/auth/*` 경로로 모든 앱이 공유했습니다. 이 방식은 "어느 앱의 인증 요청인지" 를 런타임에 구분해야 하므로 멀티테넌트 DataSource 라우팅(`AbstractRoutingDataSource`, `ThreadLocal` 등)이 필요했습니다.

새 모델에서는 각 앱 모듈이 자신의 `AuthController` 를 가지고 자기 DataSource 를 직접 사용합니다. 라우팅 복잡성이 제거됩니다.

```
[앱 AuthController]  →  [core-auth-api: AuthPort]  →  [core-auth-impl: EmailAuthService]
       │                                                          │
       │ (앱 schema DataSource 직접 사용)                         │
       └──────────────────────────────────────────────────────────┘
```

### 포트/어댑터 패턴의 적용

- **Port** = `core-*-api` 의 인터페이스 (`UserPort`, `AuthPort`, `EmailPort` 등)
- **Primary Adapter** (Inbound) = `*ServiceImpl` — Port 를 구현하고 비즈니스 로직을 담는 구현체. Spring 관용에 따라 `Adapter` 대신 `ServiceImpl` 이라 명명합니다.
- **Secondary Adapter** (Outbound) = `*Adapter` — 외부 시스템에 연결하는 구현체 (`ResendEmailAdapter`, `FcmPushAdapter` 등). 아직 구현되지 않은 것들은 Phase H, J 에서 추가됩니다.

```
[앱 AuthController] → [AuthPort 인터페이스] → [AuthServiceImpl]    ← Primary Adapter
                                                └→ [Repository]      ← Spring Data JPA (앱 DataSource)
                                                └→ [EmailPort] → [ResendEmailAdapter]  ← Secondary Adapter
```

### 대안 검토

**레이어별 모듈 분리** (module-controller, module-service, module-repository)
- 탈락 이유: 기능 하나 수정에 3 개 모듈을 건드려야 함. 도메인 코드가 흩어져서 전체 파악이 어려움.

**DDD Aggregate 패턴** (feature 단위 패키지)
- Phase 0 에서 YAGNI: 각 모듈이 5~10 클래스 수준이라 feature 분리 이득 없음. 모듈 하나가 20+ 클래스로 커지면 그때 재고.

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

## 이 문서의 용도

이 문서는 **나중에 "왜 이렇게 했지?" 라는 의문이 생길 때 돌아와서 보는 곳** 입니다.

- 설계를 후회하고 바꾸려 할 때: 이 문서의 근거가 여전히 유효한지 확인합니다.
- 새로운 구성원 (혹은 미래의 나) 이 코드를 이해하려 할 때: 구조의 의도를 설명합니다.
- 새 결정을 내릴 때: 기존 결정과 일관성을 유지하는지 비교 기준이 됩니다.

결정은 영원하지 않습니다. 상황이 변하면 재평가해야 합니다. 그러나 **"왜 그 결정을 했는가"** 를 잊지 않으면, 재평가는 빠르고 정확할 수 있습니다.

---

## 결정 14. Delegation mock 테스트를 쓰지 않는다

### 결정
테스트는 Port 의 **외부 관측 가능한 행위** 를 검증합니다. 내부 서비스 간 delegation 을 mock 으로 검증하지 않습니다.

### 이유
"A 가 B.foo() 를 호출하는가" 를 mock 으로 검증하는 테스트는 **구현 내부(how)** 에 결합됩니다. B 를 인라인화하거나 이름을 바꾸면 행위 불변이어도 테스트가 깨집니다. Port 계약 테스트가 같은 행위를 더 강하게 검증합니다 (B 가 실제로 작동하는지 간접 확인).

Port 패턴의 원래 목적인 "계약으로 격리" 와 정렬됩니다.

### 트레이드오프
내부 엣지 케이스 (특정 서비스 호출 여부) 를 직접 단언 불가 — Port 관점 행위로 재표현 필요. 일부 케이스는 표현이 길어지나, 테스트의 탄력성(내부 구조 변경에 안 깨짐)이 더 중요.

**유지되는 단위 테스트**: Port 계약으로 환원되지 않는 고유 알고리즘 (RefreshToken 회전, Apple JWKS 검증, JWT 서명 등) 은 계속 단위 테스트로 검증. 자세한 구분은 [`conventions/contract-testing.md`](../conventions/contract-testing.md).

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

## 결정 16. DTO 변환은 Mapper 클래스 없이 Entity 메서드로

### 결정
- DTO ↔ Entity 변환은 **Entity 의 `to<Dto>()` 메서드** 로 제공.
- 별도 `*Mapper`, `*Factory` 클래스 **금지** (ArchUnit `NO_MAPPER_CLASSES` 로 강제).
- `api` 모듈에 DTO 정적 팩토리 허용 조건: 정규화/검증이 포함된 경우만 (단순 생성자 대체 금지).

### 이유
**Mapper 레이어의 비용 > 가치** — 솔로 개발자 스케일에서:
- 매핑 대부분이 1:1 필드 복사. Mapper 클래스가 제공하는 "격리" 가 실체 없음.
- 의존 하나 추가, 호출 사이트 가독성 ↓ (`mapper.toSummary(entity)` vs `entity.toSummary()`).
- Mapper 를 관리할 팀/규모 자체가 없음.

**Entity 메서드가 자연스러운 이유**:
- Entity 가 자기 표현 방법을 직접 제공 — OOP 원칙에 부합.
- `impl → api` 방향 참조만 발생 (ArchUnit 규칙 부합).
- 포트 추출 시 영향도: Port 는 DTO 만 노출하므로 Entity 교체 시 `to<Dto>()` 메서드 재작성으로 대응.

Item 4 에서 `UserMapper` / `UserMapperTest` 전체 삭제 + Entity 메서드 패턴으로 전환 (커밋 `e203872`).

### 트레이드오프
- Entity 가 DTO 5+ 종류 표현하면 `to<Dto>()` 메서드가 뚱뚱해짐.
  → 현재 max: `User` → 3개 (Summary, Profile, Account). 감당 가능.
  → 5+ 초과 시 "Mapper 부활" 아니라 **DTO 구조 재평가** 시그널.
- 복잡한 매핑 (여러 Entity 조합) 은 Service 에서 조립 (Mapper 없이).

### 관련 문서
- [`conventions/dto-factory.md`](../conventions/dto-factory.md) — 정적 팩토리 허용 규칙, Entity 메서드 패턴 상세
- [`conventions/module-dependencies.md`](../conventions/module-dependencies.md) — `NO_MAPPER_CLASSES` ArchUnit 규칙

---

## 템플릿 유지 규칙 (절대 금지)

이 템플릿 레포에 커밋할 때 **반드시** 지킨다. 파생 레포에는 적용되지 않는다 — 거기에선 오히려 도메인 로직을 적극적으로 쓴다.

- **특정 앱/도메인/팀/회사 이름** 을 코드나 문서에 박지 않는다. 템플릿이 중립적이어야 어느 도메인으로든 가지를 뻗을 수 있다.
- **특정 인프라 자격증명, 계정 식별자, 프로젝트 ID** 를 커밋하지 않는다. Supabase project-ref, Google Client ID, Firebase 키 등은 파생 레포의 `.env` 에서만 존재해야 한다.
- **실제 비즈니스 로직** 을 이 레포에 쓰지 않는다 — 그건 파생 레포의 역할이다. 여기에는 뼈대, 포트 인터페이스, 공통 인프라만 둔다.
- **구체적인 스펙 문서** (특정 앱이 언급되는 요구사항/API 문서 등) 를 여기 두지 않는다 — 각 파생 레포가 `docs/specs/` 에 자기 스펙을 가진다.
- **운영 환경 변수 파일 (`.env.prod`, `.env.production` 등) 을 커밋하지 않는다.** 운영용 값은 **GHA Repository Secrets** 만 사용 (`tools/dogfooding/setup.sh` 가 `.env.dogfood` source 로 등록). 로컬 hotfix 시 노트북의 gitignored `.env.prod` 에 직접 채워서 `kamal deploy` 수동 실행은 가능하나 그 파일은 절대 commit 금지. `.env.example` / `.env.dogfood.example` 만 placeholder + 주석으로 commit.

이유의 배경은 위 **결정 1 — 파생 레포로 사용** 참조.

---

## 관련 문서

- [`architecture.md`](./architecture.md) — 실제 구조의 상세 레퍼런스
- [`conventions/`](../conventions) — 코딩 규약

---

## 📖 책 목차 — Journey 1단계

[`docs/README.md`](./README.md) 의 **1단계 — 이 레포가 뭐야?** 입니다.

| 방향 | 문서 | 한 줄 |
|---|---|---|
| ← 이전 | (없음, 첫 단계) | README 의 30분 QuickStart 가 선행 |
| → 다음 | [`architecture.md`](./architecture.md) | 같은 1단계, 모듈 구조 한눈 요약 |

**막혔을 때**: [도그푸딩 함정](../reference/dogfood-pitfalls.md) / [FAQ](./dogfood-faq.md)
**왜 이렇게?**: 이 문서가 "왜" 의 본진입니다. 더 깊은 인프라 결정은 [`conventions/decisions-infra.md`](../infra/decisions-infra.md).
