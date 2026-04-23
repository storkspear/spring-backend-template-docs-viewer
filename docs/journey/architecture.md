# Architecture Reference

이 문서는 `spring-backend-template` 의 **실제 구조** 를 설명합니다.

무엇이 어디에 있고, 각 부분이 무슨 역할을 하며, 어떻게 연결되어 있는지가 목적입니다. 결정의 이유(왜 이렇게 설계했는지) 는 [`philosophy.md`](./philosophy.md) 에 있습니다.

---

## 전체 구성 요약

이 템플릿은 **모듈러 모놀리스 구조의 Spring Boot 백엔드** 입니다. 단일 JAR 로 빌드되며, Gradle 멀티모듈로 내부 구조가 나뉘어 있습니다.

모듈은 세 종류입니다.

- **`common/*`** — 상태가 없는 뼈대 유틸리티 (웹/보안/로깅/테스트)
- **`core/*`** — 상태가 있는 플랫폼 기능 (인증/유저/디바이스/푸시/결제)
- **`apps/*`** — 앱별 도메인 로직 (템플릿에는 비어 있음. `Use this template` 으로 파생 레포를 만든 후 추가)

그리고 이들을 모두 합쳐 단일 Spring Boot 앱으로 빌드하는 `bootstrap` 모듈이 있습니다.

### 주요 기술 스택

- **언어/런타임:** Java 21, Spring Boot 3.3.x (LTS)
- **빌드:** Gradle 8.x 멀티모듈
- **데이터 액세스:** Spring Data JPA / Hibernate (엔티티, 기본 CRUD) + **QueryDsl 5.1.0 (Jakarta)** (타입 세이프 동적 쿼리, Q-클래스 자동 생성)
- **DB:** PostgreSQL 16 (로컬 Docker / 운영 Supabase Seoul — 상세: [`infrastructure.md`](../infra/infrastructure.md))
- **인증:** JJWT (HS256) + Spring Security (stateless) + BCrypt
- **외부 서비스:** Resend (이메일), Firebase Admin SDK (FCM)
- **문서화:** springdoc-openapi
- **테스트:** JUnit 5, AssertJ, Mockito, Testcontainers, ArchUnit

### core-* vs apps/* 역할 분리

> **이 섹션은 기존 '통합 계정' 모델에서 '앱별 독립 유저' 모델로 변경된 내용을 반영합니다.**
> 유저/인증 DATA 는 이제 각 앱 schema 에 있습니다. `core-auth` 는 인증 로직(서비스)만 제공하며, AuthController 는 각 앱 모듈에 있습니다.

**`core-*` = 모든 앱이 공유하는 플랫폼 로직 (라이브러리 역할)**

인증, 디바이스, 푸시, 결제 등 **도메인에 무관하게 모든 앱이 필요한 로직**입니다. 가계부 앱이든 운동 앱이든 "이메일 가입 로직" 은 동일합니다. 이 코드는 **템플릿에 포함**되며, 파생 레포 생성 시 그대로 가져갑니다.

단, 유저/인증 **데이터(테이블)** 는 `core` schema 가 아니라 각 앱 schema 에 위치합니다. `core-auth-impl` 은 컨트롤러 없는 순수 서비스 라이브러리입니다.

**`apps/app-<slug>` = 각 앱의 고유 비즈니스 로직 + 인증 엔드포인트**

가계부의 "예산 그룹", 운동 앱의 "세트/reps", 포트폴리오의 "리밸런싱 임계값" 같은 **도메인 특화 코드**와 함께, **해당 앱의 AuthController** 가 위치합니다. **파생 레포에서만** 작성되며, 템플릿에는 존재하지 않습니다.

**개발 흐름:**
1. 템플릿 → `Use this template` → 새 작업 레포(파생 레포) 생성
2. `core-*` 는 이미 들어있음 (인증 로직/푸시 즉시 사용 가능)
3. `./tools/new-app.sh <slug>` → `apps/app-<slug>/` 모듈 자동 스캐폴드 (AuthController 포함, V001~V006 마이그레이션 포함)
4. `apps/` 안에 도메인 코드 작성 (controller, service, entity, repository, Flyway)
5. `core-*` 는 건드리지 않음

**apps/ 모듈이 core-* 를 사용하는 방식:**
- `core-auth-api` 의 Port 인터페이스(`AuthPort`) 에 의존하여 인증 로직 위임
- `core-*-impl` 에는 직접 접근 불가 (ArchUnit 강제)
- `common-*` 의 유틸리티(`ApiResponse`, `@CurrentUser`, `QueryDslPredicateBuilder`) 사용
- 각 앱 모듈은 자기 schema DataSource 를 직접 주입받아 사용

### DB 전략: 동일 소스코드, 독립 데이터베이스

같은 파생 레포 안에서는 하나의 Postgres 에 **앱별 schema** 로 격리 ([`philosophy.md 결정 5`](./philosophy.md)). 서로 다른 파생 레포 간에는 완전히 별도의 DB 인스턴스를 사용.

| 요소 | 같은 파생 레포 내 | 다른 파생 레포 간 |
|---|---|---|
| core-* 소스코드 | 동일 | 동일 (같은 템플릿) |
| apps/* 소스코드 | 파생 레포 내 고유 | 파생 레포별 고유 |
| DB 인스턴스 | 공유 (하나) | 별도 |
| 유저/인증 Schema | 앱별 독립 | 전부 별도 |

schema 실제 구조, 마이그레이션 파일, Supabase 연결 상세: [`infrastructure.md §10`](../infra/infrastructure.md).

---

## 파일 트리 (주석 포함)

```
spring-backend-template/
│
├── .editorconfig                      # 에디터 공통 설정 (들여쓰기, 줄바꿈)
├── .env.example                       # 환경변수 키 목록 (값은 플레이스홀더)
├── .gitignore                         # 빌드 산출물, IDE 파일, .env 등 제외
├── README.md                          # 템플릿 소개 + 사용법
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI 파이프라인 (빌드+테스트+ArchUnit)
│
├── build.gradle                       # 루트 빌드 설정 (공통 plugin, Java 버전, 공통 의존성)
├── settings.gradle                    # Gradle 멀티모듈 선언 (모든 모듈 include)
├── gradle.properties                  # Gradle 실행 설정 (JVM 옵션, 병렬 빌드 등)
├── gradlew, gradlew.bat               # Gradle wrapper 실행 스크립트
├── gradle/wrapper/                    # Gradle wrapper JAR + 설정
│
├── docs/                              # 영구 보관용 레퍼런스 문서
│   ├── philosophy.md                  # 설계 결정의 이유
│   ├── architecture.md                # 본 문서 (구조 레퍼런스)
│   ├── edge-cases.md                  # 예외 상황 · 운영 중 이슈 대응
│   ├── social-auth-setup.md           # Google/Apple 소셜 인증 발급 가이드
│   ├── conventions/                   # 코딩 규약 (11개 문서)
│   ├── guides/                        # 운영 가이드 (cross-repo-cherry-pick 등)
│   └── migration/                     # 버전별 Migration Guide
│
├── common/                            # 상태 없는 뼈대 유틸리티 모듈들
│   │
│   ├── common-logging/                # 로깅 표준 (MDC, logback 포맷)
│   │   ├── build.gradle
│   │   └── src/
│   │       ├── main/
│   │       │   ├── java/com/factory/common/logging/
│   │       │   │   ├── MdcFilter.java              # 요청당 requestId 를 MDC 에 주입
│   │       │   │   └── LoggingAutoConfiguration.java # Spring Boot 자동 설정
│   │       │   └── resources/
│   │       │       ├── logback-spring.xml          # dev: 컬러 콘솔, prod: JSON
│   │       │       └── META-INF/spring/...         # autoconfiguration 등록 파일
│   │       └── test/
│   │
│   ├── common-web/                    # 웹 계층 공통 (응답 포맷, 예외 처리, 검색/페이지네이션, 레이트 리밋)
│   │   └── src/main/java/com/factory/common/web/
│   │       ├── response/
│   │       │   ├── ApiResponse.java                 # { data, error } 표준 응답 래퍼
│   │       │   └── ApiError.java                    # { code, message, details }
│   │       ├── exception/
│   │       │   ├── ErrorInfo.java                   # 모든 도메인 에러 enum 이 구현하는 인터페이스
│   │       │   ├── BaseException.java               # 모든 비즈니스 예외의 부모 (abstract)
│   │       │   ├── CommonException.java             # 공통 예외 (NOT_FOUND, FORBIDDEN 등)
│   │       │   ├── CommonError.java                 # 공통 에러 enum (CMN_001~008, CMN_429)
│   │       │   └── GlobalExceptionHandler.java      # BaseException → ApiError 통합 변환
│   │       ├── pagination/
│   │       │   ├── PageRequest.java                 # 페이지 요청 DTO
│   │       │   └── PageResponse.java                # 페이지 응답 DTO
│   │       ├── search/                              # POST /search 요청 DTO (QueryDsl 비의존)
│   │       │   ├── PageListRequest.java             # conditions + page + sort
│   │       │   ├── PageListQuery.java
│   │       │   ├── PageListResult.java
│   │       │   ├── PageListResponse.java
│   │       │   ├── SortOrder.java
│   │       │   └── SortFieldMapper.java             # 허용 정렬 필드 인터페이스
│   │       ├── ratelimit/                           # Bucket4j 기반 레이트 리미터
│   │       │   ├── RateLimitFilter.java
│   │       │   ├── RateLimitProperties.java
│   │       │   ├── BucketRegistry.java
│   │       │   └── RateLimitAutoConfiguration.java
│   │       ├── metrics/                             # Micrometer observation (appSlug 태깅)
│   │       ├── ApiEndpoints.java                    # 엔드포인트 경로 상수
│   │       ├── AppSlugExtractor.java                # URL path 에서 {appSlug} 추출
│   │       └── WebAutoConfiguration.java
│   │
│   ├── common-security/               # 인증/인가 공통 (JWT, SecurityConfig)
│   │   └── src/main/java/com/factory/common/security/
│   │       ├── jwt/
│   │       │   ├── JwtService.java                  # HS256 서명/검증
│   │       │   ├── JwtProperties.java               # @ConfigurationProperties("app.jwt")
│   │       │   └── JwtAuthFilter.java               # OncePerRequestFilter
│   │       ├── CurrentUser.java                     # @CurrentUser 어노테이션
│   │       ├── CurrentUserArgumentResolver.java     # MVC 인자 리졸버
│   │       ├── AuthenticatedUser.java               # 인증된 유저 값 객체
│   │       ├── PasswordHasher.java                  # BCrypt 래퍼
│   │       ├── SecurityConfig.java                  # stateless + permit/authenticate 규칙
│   │       └── SecurityAutoConfiguration.java
│   │
│   └── common-testing/                # 통합 테스트 + ArchUnit 베이스
│       └── src/
│           ├── main/java/com/factory/common/testing/
│           │   ├── AbstractIntegrationTest.java     # Testcontainers Postgres + @SpringBootTest
│           │   ├── TestUserFactory.java             # 테스트 유저 생성 헬퍼
│           │   └── PostgresTestContainer.java       # Testcontainers 초기화
│           └── test/java/com/factory/common/testing/
│               └── architecture/
│                   └── ArchitectureTest.java       # ArchUnit 경계 강제 테스트
│
├── core/                              # 상태 있는 플랫폼 기능 모듈들 (api/impl 분리)
│   │
│   ├── core-user-api/                 # 유저 포트 (인터페이스 + DTO)
│   │   └── src/main/java/com/factory/core/user/api/
│   │       ├── UserPort.java                         # 외부 노출 인터페이스
│   │       ├── dto/
│   │       │   ├── UserSummary.java                  # 최소 유저 정보
│   │       │   ├── UserProfile.java                  # 전체 프로필
│   │       │   ├── UserAccount.java                  # 계정 정보
│   │       │   └── UpdateProfileRequest.java
│   │       └── exception/
│   │           ├── UserException.java                # BaseException 하위
│   │           └── UserError.java                    # USR_001~002 enum
│   │
│   ├── core-user-impl/                # 유저 도메인 구현
│   │   # User 엔티티는 이 모듈에 정의되며, Flyway 는 `.schemas(slug)` 로 각 앱 schema 에 적용합니다.
│   │   └── src/
│   │       ├── main/
│   │       │   ├── java/com/factory/core/user/impl/
│   │       │   │   ├── UserServiceImpl.java         # UserPort 구현 + Entity.to*() 메서드로 DTO 변환
│   │       │   │   ├── entity/
│   │       │   │   │   ├── User.java                # @Entity — toSummary/toProfile/toAccount 메서드 제공
│   │       │   │   │   ├── SocialIdentity.java      # @Entity
│   │       │   │   │   └── SocialIdentityId.java    # 복합키 EmbeddedId
│   │       │   │   ├── repository/
│   │       │   │   │   ├── UserRepository.java
│   │       │   │   │   └── SocialIdentityRepository.java
│   │       │   │   ├── controller/
│   │       │   │   │   └── UserController.java      # 스캐폴딩 레퍼런스 (런타임 미등록)
│   │       │   │   └── UserAutoConfiguration.java
│   │       │   └── resources/db/migration/core/
│   │       │       ├── V001__init_users.sql
│   │       │       ├── V002__init_social_identities.sql
│   │       │       └── V003__add_users_email_index.sql
│   │       │       # Mapper 디렉토리 없음 — ArchUnit r22 로 *Mapper 금지,
│   │       │       # Entity 의 to<Dto>() 메서드로 대체
│   │       └── test/
│   │
│   ├── core-auth-api/                 # 인증 포트 (인터페이스만)
│   │   └── src/main/java/com/factory/core/auth/api/
│   │       ├── AuthPort.java                         # 인증 외부 노출 인터페이스
│   │       ├── EmailPort.java                        # 이메일 발송 추상 (Resend 등)
│   │       ├── dto/
│   │       │   ├── SignUpRequest.java
│   │       │   ├── SignInRequest.java
│   │       │   ├── AuthResponse.java                 # { user, tokens }
│   │       │   ├── AuthTokens.java                   # { accessToken, refreshToken }
│   │       │   ├── RefreshRequest.java
│   │       │   ├── AppleSignInRequest.java
│   │       │   ├── GoogleSignInRequest.java
│   │       │   ├── PasswordResetRequest.java
│   │       │   ├── PasswordResetConfirmRequest.java
│   │       │   ├── ChangePasswordRequest.java
│   │       │   ├── VerifyEmailRequest.java
│   │       │   └── WithdrawRequest.java
│   │       └── exception/
│   │           ├── InvalidCredentialsException.java
│   │           ├── EmailAlreadyExistsException.java
│   │           ├── EmailNotVerifiedException.java
│   │           ├── TokenExpiredException.java
│   │           ├── InvalidTokenException.java
│   │           └── SocialAuthException.java
│   │
│   ├── core-auth-impl/                # 인증 로직 라이브러리 (Controller 없음)
│   │   # AuthController 는 각 앱 모듈에 위치합니다. 이 모듈은 서비스 로직만 제공합니다.
│   │   └── src/
│   │       ├── main/java/com/factory/core/auth/impl/
│   │       │   ├── AuthServiceImpl.java             # AuthPort 구현 (오케스트레이션)
│   │       │   ├── service/
│   │       │   │   ├── EmailAuthService.java        # 이메일 signup/signin
│   │       │   │   ├── AppleSignInService.java      # Apple identity token 검증
│   │       │   │   ├── AppleJwksClient.java         # Apple JWKS 조회 + 캐시
│   │       │   │   ├── GoogleSignInService.java     # Google id token 검증
│   │       │   │   ├── RefreshTokenService.java     # 회전 + 탈취 감지
│   │       │   │   ├── EmailVerificationService.java # 인증 메일 발송/확인
│   │       │   │   ├── PasswordResetService.java    # 재설정 메일 발송/확인
│   │       │   │   └── WithdrawService.java         # 탈퇴 soft delete
│   │       │   ├── entity/
│   │       │   │   ├── RefreshToken.java            # @Entity <slug>.refresh_tokens (앱별 schema)
│   │       │   │   ├── EmailVerificationToken.java
│   │       │   │   └── PasswordResetToken.java
│   │       │   ├── repository/
│   │       │   ├── email/
│   │       │   │   ├── ResendEmailAdapter.java      # EmailPort 구현 (Resend API)
│   │       │   │   ├── ResendProperties.java
│   │       │   │   └── EmailTemplates.java          # 인증/재설정 이메일 HTML 템플릿
│   │       │   └── filter/
│   │       │       └── AppSlugVerificationFilter.java  # JWT appSlug vs URL path slug 검증 → 불일치 시 403
│   │       │   # controller/ 없음 — AuthController 는 각 앱 모듈에 있음
│   │       ├── resources/db/migration/
│   │       │   # core schema 마이그레이션 없음 — 인증 테이블은 앱 schema 에 있음
│   │       │   # new-app.sh 가 각 앱 schema 에 V003~V005 (refresh_tokens 등) 생성
│   │       └── test/
│   │
│   ├── core-device-api/               # 디바이스 포트 (푸시 토큰 등록)
│   │   └── src/main/java/com/factory/core/device/api/
│   │       ├── DevicePort.java
│   │       └── dto/
│   │           ├── RegisterDeviceRequest.java
│   │           └── DeviceDto.java
│   │
│   ├── core-device-impl/              # 디바이스 실제 구현
│   │   └── src/
│   │       ├── main/java/com/factory/core/device/impl/
│   │       │   ├── DeviceServiceImpl.java
│   │       │   ├── entity/Device.java               # @Entity core.devices
│   │       │   ├── repository/DeviceRepository.java
│   │       │   └── controller/DeviceController.java # POST/DELETE /api/core/devices
│   │       └── resources/db/migration/core/
│   │           └── V007__init_devices.sql
│   │
│   ├── core-push-api/                 # 푸시 포트
│   │   └── src/main/java/com/factory/core/push/api/
│   │       ├── PushPort.java                         # sendToUser, sendToDevices, sendToTopic
│   │       └── dto/
│   │           ├── PushMessage.java                  # title, body, data, imageUrl
│   │           └── PushSendResult.java               # successCount, invalidTokens
│   │
│   ├── core-push-impl/                # FCM 실제 구현
│   │   └── src/main/java/com/factory/core/push/impl/
│   │       ├── FcmPushAdapter.java                   # Firebase Admin SDK 래퍼
│   │       ├── FcmProperties.java                    # service account JSON 경로 등
│   │       ├── PushService.java                      # Device 조회 → FCM 전송 조율
│   │       └── PushAutoConfiguration.java
│   │
│   ├── core-billing-api/              # 결제 포트 (인터페이스만, Phase 0)
│   │   └── src/main/java/com/factory/core/billing/api/
│   │       ├── BillingPort.java
│   │       ├── dto/
│   │       │   ├── IapReceiptRequest.java
│   │       │   ├── SubscriptionStatus.java
│   │       │   └── PurchaseVerificationResult.java
│   │       └── exception/BillingException.java
│   │
│   └── core-billing-impl/             # 결제 스텁 (Phase 0: 미구현)
│       └── src/main/java/com/factory/core/billing/impl/
│           ├── StubBillingAdapter.java              # UnsupportedOperationException throws
│           └── BillingAutoConfiguration.java        # Phase 1 에 실제 구현으로 교체
│
├── apps/                              # 앱별 도메인 모듈 (템플릿에는 비어 있음)
│   ├── .gitkeep
│   └── README.md                      # "./tools/new-app/new-app.sh 로 추가하세요"
│
├── bootstrap/                         # 단일 Spring Boot JAR 진입점
│   └── src/
│       ├── main/
│       │   ├── java/com/factory/bootstrap/
│       │   │   ├── FactoryApplication.java         # @SpringBootApplication
│       │   │   ├── controller/
│       │   │   │   ├── HealthController.java       # GET /health (무인증)
│       │   │   │   └── VersionController.java      # GET /version (무인증)
│       │   │   └── config/
│       │   │       ├── OpenApiConfig.java          # Swagger UI 설정
│       │   │       └── JpaConfig.java              # JPA 스캔 범위 설정
│       │   └── resources/
│       │       ├── application.yml                 # 공통 설정 + 플레이스홀더
│       │       ├── application-dev.yml             # 로컬 Postgres
│       │       ├── application-prod.yml            # Supabase 플레이스홀더
│       │       └── application-test.yml            # Testcontainers
│       └── test/                                    # Full context load test 포함
│
├── tools/
│   └── new-app/
│       └── new-app.sh                             # 새 앱 모듈 스캐폴드 생성 스크립트
│
└── infra/
    ├── docker-compose.dev.yml                     # 로컬 Postgres 16 컨테이너
    └── scripts/
        ├── keep-alive.sh                          # Supabase Free 활성 유지용
        └── backup-to-nas.sh.example               # pg_dump 예시 (플레이스홀더)
```

---

## 모듈 의존 그래프

### 개요

의존 관계는 **아래로만** 흐릅니다. 상위 모듈이 하위 모듈을 의존하며, 역방향 의존은 금지됩니다.

```
bootstrap                              # 최상위 (모든 것을 조립)
   │
   ├──→ common-logging                 # 가장 하위 레이어
   ├──→ common-web                     # (상태 없음)
   ├──→ common-security
   │
   ├──→ core-user-impl                 # core 레이어: 각 모듈이 api + impl 쌍
   │       ├──→ common-web             #   impl 은 common-* 를 의존
   │       ├──→ common-security
   │       └──→ core-user-api          #   impl 은 자기 api 를 의존
   │
   ├──→ core-auth-impl                 # 서비스 라이브러리만 (Controller 없음)
   │       ├──→ common-web
   │       ├──→ common-security
   │       ├──→ core-auth-api          #   자기 api
   │       └──→ core-user-api          #   다른 core 는 api 만 의존 (impl 아님!)
   │
   ├──→ core-device-impl
   │       ├──→ common-web
   │       ├──→ common-security
   │       ├──→ core-device-api
   │       └──→ core-user-api
   │
   ├──→ core-push-impl
   │       ├──→ core-push-api
   │       └──→ core-device-api
   │
   ├──→ core-billing-impl              # Phase 0: 스텁만
   │       └──→ core-billing-api
   │
   └──→ apps/app-<slug>               # 앱별 모듈 (파생 레포에서 추가)
           ├──→ common-web             #   공통 응답/예외
           ├──→ common-security        #   JWT, @CurrentUser
           ├──→ core-auth-api          #   인증 서비스 인터페이스 (AuthPort)
           └──→ core-user-api          #   유저 서비스 인터페이스 (UserPort)
           # core-*-impl 접근 금지 (Gradle + ArchUnit 강제)
```

### 의존 규칙 (강제됨)

다음 규칙은 **Gradle 빌드 시스템과 ArchUnit CI 테스트로 강제** 됩니다. 위반 시 빌드 실패합니다.

**규칙 1. `bootstrap` 만 `core-*-impl` 을 의존합니다.** Spring 이 빈을 조립할 수 있도록 모든 impl 을 한 곳에서 모읍니다.

**규칙 2. `core-*-impl` 은 다른 `core-*-api` 만 의존합니다.** 예를 들어 `core-auth-impl` 은 `core-user-api` 를 의존할 수 있지만 `core-user-impl` 은 의존할 수 없습니다.

**규칙 3. `apps/*` 는 `core-*-api` 와 `common-*` 만 의존합니다.** `core-*-impl` 에 접근할 수 없습니다. (템플릿에는 apps 가 없지만, 파생 레포에서 새 앱 모듈에 적용되는 규칙)

**규칙 4. `apps/*` 끼리 참조 금지.** `app-sumtally` 가 `app-gymlog` 를 import 할 수 없습니다.

**규칙 5. `common-*` 은 `core-*` 나 `apps/*` 를 의존하지 않습니다.** common 은 가장 아래 레이어입니다.

---

## 요청 플로우

### 일반 인증 요청 예시

유저가 `GET /api/apps/sumtally/users/me` 를 호출할 때의 처리 흐름입니다.

```
클라이언트 (Flutter 앱)
      │ HTTPS
      ▼
Cloudflare 엣지 (TLS 종료, DDoS 방어)
      │
      ▼
Cloudflare Tunnel → 맥미니
      │
      ▼
Spring Boot (bootstrap JAR, localhost:8080)
      │
      ▼
[MdcFilter]                             (common-logging)
      │ requestId 를 MDC 에 주입
      ▼
[JwtAuthFilter]                         (common-security)
      │ Authorization: Bearer xxx 파싱
      │ JwtService 로 검증 (appSlug claim 포함)
      │ SecurityContext 에 AuthenticatedUser 주입
      ▼
[AppSlugVerificationFilter]             (core-auth-impl)
      │ JWT appSlug claim == URL path slug 검증
      │ 불일치 → 403 FORBIDDEN
      ▼
[UserController.getMyProfile(@CurrentUser AuthenticatedUser user)]   (apps/app-sumtally)
      │ CurrentUserArgumentResolver 가 AuthenticatedUser 주입
      ▼
UserServiceImpl.findProfileById(user.userId())
      │
      ▼
UserRepository.findById(...)            (Spring Data JPA, sumtally DataSource)
      │
      ▼
HikariCP (sumtally 전용 풀) → Postgres (Supabase, sumtally schema)
      │
      ▼ (응답 경로)
User 엔티티 → User.toProfile() → UserProfile DTO
      │
      ▼
UserController → ApiResponse.ok(profile) → JSON 응답
      │
      ▼
[GlobalExceptionHandler]                (common-web, 예외 시에만)
      │ 예외 발생 시 ApiError 로 변환
      ▼
클라이언트
```

### 예외 처리 흐름

어떤 레이어에서든 예외가 발생하면 `GlobalExceptionHandler` 가 가로채서 `ApiResponse.error(ApiError)` 형태로 변환합니다. 클라이언트는 항상 같은 구조의 응답을 받습니다.

```
throw new UserException(UserError.USER_NOT_FOUND, Map.of("id", String.valueOf(userId)))
      │
      ▼
GlobalExceptionHandler.handleBaseException(BaseException)
      │ ErrorInfo → ApiError 로 변환
      ▼
ApiResponse.error(new ApiError("USR_001", "유저를 찾을 수 없습니다", {id: userId}))
      │
      ▼
HTTP 404 + JSON 응답
```

---

## 인증 플로우

### 이메일 가입

> **이 섹션은 기존 '통합 계정' 모델에서 '앱별 독립 유저' 모델로 변경된 내용을 반영합니다.**
> AuthController 는 각 앱 모듈에 있으며, 엔드포인트는 `/api/apps/<slug>/auth/email/signup` 입니다.

```
POST /api/apps/sumtally/auth/email/signup
     { email, password, displayName }
      │
      ▼
[AppSlugVerificationFilter]             # URL slug 검증 (인증 전이므로 JWT 없을 수 있음 → 패스)
      │
      ▼
AuthController (apps/app-sumtally) → AuthServiceImpl.signUpWithEmail(appSlug, request)
      │
      ├─→ EmailAuthService: 이메일 중복 체크 (sumtally schema 에서), 비밀번호 해싱, User 생성
      │   ├─→ UserRepository.save(User{ email_verified: false })  # sumtally.users 에 저장
      │   └─→ EmailVerificationService.sendVerificationEmail(user)
      │       └─→ ResendEmailAdapter.send(...)
      │
      ├─→ RefreshTokenService.issue(userId) → RefreshToken  # sumtally.refresh_tokens 에 저장
      ├─→ JwtService.issueAccessToken(userId, email, appSlug: "sumtally") → accessToken
      │
      └─→ AuthResponse { user, tokens }
```

### Apple Sign In

```
POST /api/apps/sumtally/auth/apple
     { identityToken }
      │
      ▼
AuthController (apps/app-sumtally) → AuthServiceImpl.signInWithApple(appSlug, request)
      │
      ├─→ AppleSignInService.verify(identityToken)
      │   ├─→ AppleJwksClient.getKeys() → Apple 공개키 목록
      │   ├─→ JWT 서명 검증 (kid → 해당 키로 검증)
      │   ├─→ iss/aud/exp 검증
      │   └─→ sub (Apple user ID) 추출
      │
      ├─→ SocialIdentityRepository.findByProviderAndProviderId("apple", sub)  # sumtally schema
      │   ├─→ 있으면: 기존 sumtally User 로 로그인
      │   └─→ 없으면: 새 sumtally User + SocialIdentity 생성 (이메일은 첫 로그인 시에만 제공됨)
      │
      ├─→ RefreshTokenService.issue(userId)
      ├─→ JwtService.issueAccessToken(...)
      │
      └─→ AuthResponse
```

### Refresh Token 회전

```
POST /api/apps/sumtally/auth/refresh
     { refreshToken }
      │
      ▼
RefreshTokenService.refresh()
      │
      ├─→ tokenHash = BCrypt.hash(refreshToken)
      ├─→ DB 에서 해당 해시로 RefreshToken 조회
      │
      ├─→ 만료? → TokenExpiredException
      │
      ├─→ 이미 used? → (탈취 감지)
      │   ├─→ 같은 family_id 의 모든 토큰 무효화
      │   ├─→ 유저에게 전체 재로그인 요구
      │   └─→ InvalidTokenException
      │
      ├─→ 정상: old 토큰 used_at = now
      │
      ├─→ 새 refresh token 발급 (같은 family_id 유지, sumtally.refresh_tokens)
      ├─→ 새 access token 발급 (appSlug: "sumtally" claim 포함)
      │
      └─→ AuthTokens { accessToken, refreshToken: new }
```

### 탈퇴 (Soft Delete)

```
POST /api/apps/sumtally/auth/withdraw
     { reason }
     (Authorization: Bearer xxx 필요, appSlug: "sumtally")
      │
      ▼
WithdrawService.withdraw(userId, reason)
      │
      ├─→ User.deleted_at = now
      ├─→ RefreshTokenRepository.revokeAllByUserId(userId)
      │
      └─→ (30일 후 hard delete 는 Phase 1 의 스케줄러가 담당)
```

---

## 데이터베이스 구조

> **이 섹션은 기존 '통합 계정' 모델에서 '앱별 독립 유저' 모델로 변경된 내용을 반영합니다.**
> `core` schema 는 제거되었습니다. 유저/인증 테이블은 각 앱 schema 에 있습니다.

### Schema

단일 `postgres` database 안에 여러 schema 가 공존합니다.

```
postgres (database)
│
├── sumtally                        ← apps/app-sumtally 전용 schema
│   ├── users                       ← sumtally 유저 (독립)
│   ├── social_identities
│   ├── refresh_tokens
│   ├── email_verification_tokens
│   ├── password_reset_tokens
│   ├── devices
│   ├── budget_groups               ← sumtally 도메인 테이블
│   ├── expenses
│   └── ...
│
├── rny                             ← apps/app-rny 전용 schema
│   ├── users                       ← rny 유저 (독립, sumtally 와 별개)
│   ├── social_identities
│   ├── refresh_tokens
│   ├── ...
│   ├── asset_groups                ← rny 도메인 테이블
│   └── ...
│
├── <app_slug>                      ← 각 앱 전용 schema (파생 레포에서 new-app.sh 로 생성)
│   ├── users
│   ├── social_identities
│   ├── refresh_tokens
│   ├── email_verification_tokens
│   ├── password_reset_tokens
│   ├── devices
│   └── (앱별 도메인 테이블들)
│
└── public                          ← 건드리지 않음 (Supabase 기본)
```

### 역할 분리

각 앱 모듈은 자기 schema 에만 접근 권한을 가진 DB role 로 접속합니다. `core` schema 전용 role 은 더 이상 없습니다.

```sql
-- 앱별 role (파생 레포에서 new-app.sh 가 안내)
CREATE ROLE sumtally_app LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA sumtally TO sumtally_app;
GRANT ALL ON ALL TABLES IN SCHEMA sumtally TO sumtally_app;
REVOKE ALL ON SCHEMA rny FROM sumtally_app;  -- 다른 앱 schema 접근 불가

CREATE ROLE rny_app LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA rny TO rny_app;
GRANT ALL ON ALL TABLES IN SCHEMA rny TO rny_app;
REVOKE ALL ON SCHEMA sumtally FROM rny_app;  -- 다른 앱 schema 접근 불가
```

이 권한 분리는 **"앱 모듈이 실수로라도 다른 schema 의 테이블에 접근할 수 없도록"** 강제합니다.

### DataSource 분리

Spring Boot 는 각 앱 schema 별로 별도의 DataSource 와 HikariCP 풀을 가집니다. `core` DataSource 는 없습니다. 각 앱 모듈이 자기 DataSource 를 직접 주입받아 사용하므로 멀티테넌트 라우팅(`AbstractRoutingDataSource`, `ThreadLocal`) 이 필요 없습니다.

```yaml
spring:
  datasource:
    # core DataSource 없음 — 유저/인증 테이블은 앱 schema 에 있음
    sumtally:
      url: jdbc:postgresql://...?currentSchema=sumtally
      username: ${SUMTALLY_DB_USER}
      password: ${SUMTALLY_DB_PASSWORD}
      hikari:
        maximum-pool-size: 10
    rny:
      url: jdbc:postgresql://...?currentSchema=rny
      username: ${RNY_DB_USER}
      password: ${RNY_DB_PASSWORD}
      hikari:
        maximum-pool-size: 10
```

커넥션 풀이 분리되어 있어서, 한 앱의 커넥션 고갈이 다른 앱에 영향을 주지 않습니다.

---

## Multi-DataSource Wiring

Template 은 앱별 독립 DataSource 패턴을 제공 (Item 10b). 각 앱이 자기 schema 에 붙는 DataSource / EntityManagerFactory / TransactionManager / Flyway 빈을 소유.

```
bootstrap/CoreDataSourceConfig (@Primary, slug="core")
  @Bean dataSource / entityManagerFactory / transactionManager / flyway
         ▲
         │ coexists with
         │
apps/app-<slug>/config/<Slug>DataSourceConfig (slug="<slug>")
  @Bean <slug>DataSource / <slug>EntityManagerFactory / <slug>TransactionManager / <slug>Flyway
  @EnableJpaRepositories(basePackages = "apps.<slug>.repository",
                         entityManagerFactoryRef = "<slug>EntityManagerFactory")
```

두 Config 모두 `common-persistence/AbstractAppDataSourceConfig` 의 `build*` 헬퍼 재사용. 새 앱 추가 시 `new-app.sh` 가 Config 클래스 자동 생성. 상세 결정: [`conventions/decisions-infra.md I-08`](../infra/decisions-infra.md).

---

## 호스팅 구성

환경별 구성도 (로컬 / 운영), 포트 표, 프로비저닝 상태, 책임 분담은 **[`infrastructure.md`](../infra/infrastructure.md)** 로 이관되었습니다.

- 로컬 개발 구성도: [`infrastructure.md §3`](../infra/infrastructure.md)
- 운영 구성도 (planned): [`infrastructure.md §4`](../infra/infrastructure.md)
- 책임 분담 표: [`infrastructure.md §5`](../infra/infrastructure.md)
- 선택 근거 (Supabase / NAS MinIO / 맥미니 / Cloudflare Tunnel): [`conventions/decisions-infra.md`](../infra/decisions-infra.md)

---

## Extraction 을 위한 6중 방어선

특정 앱이 대박 나서 독립 서비스로 빼내야 할 때를 대비해 6개의 방어선을 첫날부터 유지합니다. 각 방어선은 실수로 경계를 넘을 수 없도록 **기계적으로 강제** 됩니다.

### 방어선 1 — DB Role 권한 분리

각 schema 에 전용 role 을 만들고, 크로스 schema 접근은 DB 수준에서 permission denied 가 발생합니다. 위반 시 SQL 실행이 실패하므로 런타임에 즉시 발견됩니다.

### 방어선 2 — Spring DataSource 분리

각 모듈이 별도 HikariCP 커넥션 풀을 가지며, 각 풀은 자기 schema 에만 접속하도록 설정됩니다. 한 모듈의 코드가 다른 모듈의 DataSource 를 얻을 방법이 없습니다.

### 방어선 3 — Flyway 마이그레이션 분리

각 앱은 자기 `db/migration/<slug>/` 디렉토리에서 마이그레이션을 관리합니다. Flyway 히스토리 테이블도 schema 별로 분리됩니다. 앱 간 마이그레이션 간섭이 불가능합니다.

### 방어선 4 — 포트 인터페이스 의존 (Gradle convention plugin)

앱 모듈은 `core-*-api` 만 의존합니다. `core-*-impl` 에 직접 접근하는 코드는 **Gradle configuration 단계에서 거절** 됩니다. 컴파일도 시작되지 않습니다.

`build-logic/` 의 역할별 convention plugin (`factory.common-module`, `factory.core-api-module`, `factory.core-impl-module`, `factory.app-module`, `factory.bootstrap-module`) 이 `afterEvaluate` 에서 `ProjectDependency` 를 순회하며 허용/금지 규칙 검증. 위반 시 `GradleException` throw.

자세한 매트릭스와 규칙은 [`conventions/module-dependencies.md`](../conventions/module-dependencies.md).

### 방어선 5 — ArchUnit CI 강제

위 네 가지로 잡히지 않는 패턴 (예: 같은 패키지 이름 규칙 준수, 엔티티 노출 금지 등) 은 ArchUnit 테스트로 CI 에서 강제됩니다. 빌드 실패로 머지가 차단됩니다.

### 방어선 6 — Contract Test

포트가 약속한 행위를 `AbstractXxxPortContractTest` 로 명문화합니다. 모든 impl 은 이 abstract 를 상속하여 통과해야 머지 가능. JSON 직렬화 계약은 `AbstractJsonContractTest<T>` 로 강제됩니다. 테스트 실패 시 CI 에서 빌드가 멈춥니다.

이 방어선은 **추출 가능성의 형식적 보증** — impl 을 HTTP 어댑터로 교체해도 같은 abstract 를 통과하면 정상 작동이 확정됩니다. 자세한 규약은 [`conventions/contract-testing.md`](../conventions/contract-testing.md) 참조.

이 여섯 개가 모두 있으면 **"나중에 뽑을 수 있다"** 가 빈 약속이 아닌 **보장** 이 됩니다. 추출 작업이 필요해지는 시점에는 대략 다음 7~10 영업일 정도로 진행 가능합니다.

1. 새 레포 생성, 해당 앱 모듈 복사
2. `core-*-api` 의존을 유지한 채 `core-*-impl` 을 HTTP 클라이언트로 교체
3. `pg_dump -n <schema>` 로 해당 schema 덤프, 새 Postgres 인스턴스에 복구
4. 새 배포 파이프라인 구성
5. 리버스 프록시에서 해당 앱 경로 라우팅
6. 트래픽 이전 및 검증

---

## 관련 문서

- [`philosophy.md`](./philosophy.md) — 설계 결정의 이유
- [`conventions/`](../conventions) — 코딩 규약 (네이밍, API 응답 포맷, 설계 원칙 등 11개 문서)

---

## 📖 책 목차 — Journey 1단계

[`docs/README.md`](./README.md) 의 **1단계 — 이 레포가 뭐야?** 입니다.

| 방향 | 문서 | 한 줄 |
|---|---|---|
| ← 이전 | [`philosophy.md`](./philosophy.md) | 같은 1단계, 핵심 결정 1~3 |
| → 다음 | [`guides/onboarding.md`](./onboarding.md) | 2단계 — 어떻게 써? (로컬 dev) |

**막혔을 때**: [도그푸딩 함정](../reference/dogfood-pitfalls.md) / [FAQ](./dogfood-faq.md)
**왜 이렇게?**: [`philosophy.md`](./philosophy.md) (설계 결정 22개) / [`conventions/decisions-infra.md`](../infra/decisions-infra.md) (인프라 결정 I-01~I-14)
