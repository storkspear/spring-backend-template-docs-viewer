# Item 10b — Multi-DataSource Wiring Design

> **Spec (design only)**. 구현 계획 (Task breakdown) 은 `writing-plans` 스킬이 별도 생성하거나 본 파일에 Task 섹션을 추가한다.

**작성일**: 2026-04-19
**상태**: ✅ Complete (2026-04-19, merge: `69ca16d`). 본 디자인 문서는 작업 당시 기록용.
**선행**:
- Item 10 (`new-app.sh` 2단계 자동화) 완료 `ff4bcbb`
- Item 11 (docs-contract-test CI) 완료 `03112a6`
- Item 10 Task 7 에서 multi-DataSource 분리 결정

**후행 예약**:
- Item Ops-1 (운영 배포 묶음)

---

## 1. Goal

Template 레포가 **multi-DataSource 패턴 + helper + `new-app.sh` 자동 생성** 을 제공하여, 파생 레포가 `./tools/new-app/new-app.sh <slug>` 한 번으로 "앱별 schema 에 독립적으로 붙는 DataSource + JPA + Flyway" 전부 자동 wiring 되게 한다.

---

## 2. Context — 왜 필요한가

`philosophy.md 결정 5` — 단일 Postgres + 앱당 schema + DB role 분리:

```
Postgres (Supabase 하나)
├── core schema           ← 템플릿 내부 테스트용 (레퍼런스)
├── sumtally schema       ← sumtally_app role 만 접근
├── rny schema            ← rny_app role
└── gymlog schema         ← gymlog_app role
```

**Item 10 후 상태**:
- `./new-app.sh gymlog` 실행 시 `.env` 에 `GYMLOG_DB_URL/USER/PASSWORD` 주입 완료 ✅
- `gymlog` schema + role 자동 생성 (`--provision-db`) ✅
- Flyway migration 파일 (`apps/app-gymlog/.../db/migration/gymlog/V001~V006`) 생성 ✅
- **그러나** Spring 에서 이 변수들을 실제로 소비하는 `DataSource` 빈 wiring **없음** ❌

Bootstrap 의 현재 단일 DataSource (`application-dev.yml`) 는 `postgres:dev` 로 core schema 만 본다. 새 앱 schema 에 접근할 방법 없음.

---

## 3. 구조적 선택 (brainstorming 결정 사항)

### 3.1 Pattern: 앱 모듈이 자기 DataSource 제공 (Option B)

`apps/app-<slug>/` 안에 `<Slug>DataSourceConfig.java` — 각 앱이 자기 DataSource 빈 소유.
- Template 은 추상/helper 제공
- 실제 인스턴스 (sumtally 용, rny 용) 은 파생 레포에
- `philosophy.md 결정 3` (core-api/impl 분리) 정신 일치
- 파생 레포가 template bootstrap 내부 수정 불필요 → cherry-pick 충돌 회피

**대안 기각**:
- Bootstrap 중앙 집중 (a): 파생 레포가 template 코드 수정 필요
- AbstractRoutingDataSource (c): Phase 0 규모에 과잉, 디버깅 어려움

### 3.2 Scope: A (MVP)

Template 의 기존 단일 DataSource 는 그대로 유지. Abstract 추가 + new-app.sh 확장만.

**대안 기각**:
- 확장 B: Bootstrap core DataSource 도 재작성 → 회귀 위험
- 미니멀 C: abstract 없이 인라인 → 3 앱부터 boilerplate 폭발

### 3.3 Module 위치: `common-querydsl` → `common-persistence` 로 rename

파생 레포 0개 상태에서 rename 비용 최저. 모듈이 JPA+DataSource 포함하게 되므로 이름 정확성 확보.

**대안 기각**:
- (x) 신설 `common-persistence`: 기존 querydsl 은 어색하게 남음
- (y) common-querydsl 유지: 이름이 내용 미반영
- (c) Java package 유지: Gradle/Java 이름 괴리 발생

---

## 4. Architecture

```
┌──────── common-persistence (rename 전: common-querydsl) ────────┐
│ AbstractAppDataSourceConfig (신규 abstract)                      │
│   protected 추상 메서드:                                           │
│     - String slug()                                               │
│     - DataSourceProperties properties()                           │
│   제공 @Bean (자동):                                               │
│     - <slug>DataSource          (HikariCP)                        │
│     - <slug>EntityManagerFactory                                  │
│     - <slug>TransactionManager                                    │
│     - <slug>Flyway              (migration: db/migration/<slug>)  │
│   @EnableJpaRepositories 기본 basePackages:                       │
│     - com.factory.core.{user,auth,device}.impl.repository         │
│     - com.factory.apps.<slug>.repository (override 가능)          │
│                                                                   │
│ QueryDslAutoConfiguration (기존 유지)                              │
│ QueryDslPredicateBuilder, QueryDslSortBuilder, QueryUtil          │
│ entity/BaseEntity                                                 │
└───────────────────────────────────────────────────────────────────┘
                           ▲
                           │ extends
                           │
apps/app-<slug>/.../config/<Slug>DataSourceConfig  ←── new-app.sh 자동 생성
  public class SumtallyDataSourceConfig extends AbstractAppDataSourceConfig {
      @Override protected String slug() { return "sumtally"; }
      @Override protected DataSourceProperties properties() {
          return bind(env, "SUMTALLY_DB_");
      }
  }

bootstrap/ 기존 단일 DataSource (core schema):
  @Primary 유지 — template 자체 테스트 + core-*-impl Testcontainer 용
  파생 레포의 앱 repository 는 이 EMF 에 바인딩 안 됨 (자기 <Slug>EMF 로)
```

### 4.1 핵심 설계 결정

| 결정 | 값 |
|---|---|
| **Bean naming** | `<slug>DataSource`, `<slug>EntityManagerFactory`, `<slug>TransactionManager`, `<slug>Flyway` |
| **Primary DataSource** | Bootstrap 기존 유지 (core schema). 각 앱 DataSource 는 `@Qualifier` 로 명시 |
| **JPA basePackages 기본** | `core.user.impl.repository`, `core.auth.impl.repository`, `core.device.impl.repository`, `apps.<slug>` |
| **Entity scan** | 동일 basePackages 의 entity 서브패키지 |
| **Flyway migration 위치** | `classpath:db/migration/<slug>` |
| **Flyway schema** | `<slug>` (ALTER TABLE, CREATE 모두 이 schema 에) |
| **HikariCP 기본 poolSize** | 10 (override 가능) |

---

## 5. Components

### 5.1 `AbstractAppDataSourceConfig` (신규)

책임:
- DataSource 빈 생성 (HikariCP)
- EntityManagerFactory 빈 생성 (Hibernate + core + apps 패키지 scan)
- TransactionManager 빈 생성
- Flyway 빈 생성 + `migrate()` 자동 호출 (ApplicationReadyEvent 전)
- `@EnableJpaRepositories` 의 `basePackages`, `entityManagerFactoryRef`, `transactionManagerRef` 기본값 제공

구현 포인트:
- `@EnableJpaRepositories` 는 annotation 이므로 concrete 클래스에 붙여야. Abstract 가 basePackages 를 제공하기 어려움. 대안: Abstract 가 helper 메서드 `defaultBasePackages()` 제공 → concrete 가 annotation 값에 배열 리터럴로 표기 (annotation literal 제약) → **Concrete 클래스가 명시적 선언** 필요.
- 즉 abstract 는 빈 생성 로직 (Java 코드) 만 재사용. @EnableJpaRepositories 는 concrete 에서.

### 5.2 `<Slug>DataSourceConfig` (new-app.sh 자동 생성)

```java
@Configuration
@EnableJpaRepositories(
    basePackages = {
        "com.factory.core.user.impl.repository",
        "com.factory.core.auth.impl.repository",
        "com.factory.core.device.impl.repository",
        "com.factory.apps.sumtally.repository"
    },
    entityManagerFactoryRef = "sumtallyEntityManagerFactory",
    transactionManagerRef = "sumtallyTransactionManager"
)
public class SumtallyDataSourceConfig extends AbstractAppDataSourceConfig {

    public SumtallyDataSourceConfig(
        @Value("${SUMTALLY_DB_URL}") String url,
        @Value("${SUMTALLY_DB_USER}") String user,
        @Value("${SUMTALLY_DB_PASSWORD}") String password
    ) {
        super("sumtally", url, user, password);
    }
}
```

`new-app.sh` 가 slug 대입해서 생성 — 비즈니스 로직 없음, pure scaffolding.

### 5.3 `new-app.sh` 확장

기존 Item 10 의 Step 15 "남은 수동 안내" 에 있던 "bootstrap DataSource 설정 추가 (Item 10b 예정)" 메시지 제거.

신규 Step: `<Slug>DataSourceConfig.java` 자동 생성 — `apps/app-<slug>/src/main/java/com/factory/apps/<slug_package>/config/` 에 배치.

---

## 6. Data Flow — Spring 부팅 순서

```
1. Spring Context 초기화
   ├─ Bootstrap 의 단일 DataSource @Primary 등록 (core schema)
   ├─ SumtallyDataSourceConfig 인스턴스화
   │   ├─ sumtallyDataSource 빈 등록
   │   ├─ sumtallyEntityManagerFactory 빈 등록 (scan core.user.impl, core.auth.impl, apps.sumtally)
   │   ├─ sumtallyTransactionManager 빈 등록
   │   └─ sumtallyFlyway 빈 등록
   │
   ├─ RnyDataSourceConfig 인스턴스화 (똑같이)
   │   └─ rnyDataSource, rnyEntityManagerFactory, ...
   │
   └─ @EnableJpaRepositories scan
       ├─ core.user.impl.repository.UserRepository → 각 앱 EMF 별로 빈 N개 (name: userRepository_sumtally, userRepository_rny — Spring Data JPA 의 bean name generator 가 이렇게 구분)

2. ApplicationReadyEvent
   ├─ sumtallyFlyway.migrate() — apps/app-sumtally/db/migration/sumtally/ V001~V006 실행
   ├─ rnyFlyway.migrate() — rny 용 migration
   └─ core schema Flyway 는 bootstrap 의 기본 설정으로 이미 실행됨 (template 내부 테스트용)

3. AuthServiceImpl (core-auth-impl) 사용:
   - 각 앱 controller (apps/app-sumtally/auth/SumtallyAuthController) 가 자기 context 의
     AuthServiceImpl 을 주입받음
   - AuthServiceImpl 은 sumtallyUserRepository 를 주입받아 sumtally schema 에서 동작
```

---

## 7. Error Handling / Edge Cases

| 상황 | 처리 |
|---|---|
| `<SLUG>_DB_URL` env var 미설정 | Spring 부팅 실패 (`@Value` resolve 실패). 명확한 에러 — `.env` 에 변수 추가 안내 |
| Flyway migration 실패 | 부팅 실패. 다른 앱 DataSource 는 영향 없음 (ApplicationReadyEvent 전) |
| 동일 `UserRepository` 빈 이름 충돌 | `@EnableJpaRepositories` 의 `entityManagerFactoryRef` 로 구분. Spring Data JPA 가 자동으로 다른 빈 이름 생성 |
| Testcontainer 에서 multi-DataSource | 테스트는 `@SpringBootTest` 에 특정 app profile 지정. AbstractIntegrationTest 가 이 분기 처리 |
| 앱 `@Repository` 가 다른 앱 schema 접근 시도 | DB role permission denied (schema 레벨) — philosophy 결정 4 의 5중 방어선 중 1번 |

---

## 8. Testing Strategy

### 8.1 Unit 테스트 (Template)
- `AbstractAppDataSourceConfigTest` — 추상 클래스의 빈 생성 로직 검증 (Testcontainer 1개로)

### 8.2 Integration 테스트 (Template)
- `<Slug>DataSourceConfigTest` (테스트용 fake slug "testapp") — 실제 Testcontainers Postgres 에 testapp schema 생성 + Flyway 실행 + Repository 쿼리 동작 확인

### 8.3 E2E 테스트 (파생 레포 시뮬)
- 기존 `tools/new-app/tests/test-e2e.sh` 확장 — `./new-app.sh testapp --provision-db` 후:
  - `testapp` schema + role 생성 확인 (기존)
  - `<testapp>DataSourceConfig.java` 파일 생성 확인 (신규)
  - Gradle compile 통과 (기존)
  - **Spring bootRun + 부팅 성공 + testapp schema migration 실행 확인** (신규, Testcontainer 스타일)

### 8.4 ArchUnit 추가 규칙 (선택)
- `r23`: `<Slug>DataSourceConfig` 는 `AbstractAppDataSourceConfig` 를 extends 해야 함
- 파생 레포가 규약 위반 시 빌드 실패

---

## 9. Scope + 제외 사항

### 9.1 포함 (본 Item)
1. `common-querydsl` → `common-persistence` rename (Gradle + Java package + 문서)
2. `AbstractAppDataSourceConfig` 추상 클래스 + 빈 4종 (DataSource/EMF/TM/Flyway)
3. `new-app.sh` 에 `<Slug>DataSourceConfig.java` 자동 생성 Step 추가
4. E2E 테스트 확장 — Spring bootRun + Flyway 검증
5. 문서 갱신 (architecture.md, decisions-infra.md, onboarding.md §5, module-dependencies.md, backlog archive)

### 9.2 제외 (별도 Item 또는 의도적 유지)
- Bootstrap 의 기존 단일 DataSource 리팩토링 — MVP 밖
- `core-*-impl` 의 Flyway migration 파일 — template 자체 테스트용, 유지
- 도메인 테이블 자동 생성 (V007+) — 비즈니스 로직
- `AbstractRoutingDataSource` 런타임 분기 — 복잡도 ↑, 필요 시점에 brainstorming
- DB read replica / 분리 — 미래
- ArchUnit r23 — 선택. 구현 복잡도 확인 후 결정

---

## 10. File Structure (구현 단계에서 Task 로 분해됨)

### 신설 / 수정 파일

```
common/common-persistence/ (common-querydsl rename)
  ├─ build.gradle                                    (rename 영향)
  ├─ src/main/java/com/factory/common/persistence/   (package rename)
  │   ├─ AbstractAppDataSourceConfig.java            🆕 신설
  │   ├─ QueryDslAutoConfiguration.java              (package rename)
  │   ├─ QueryDslPredicateBuilder.java               (package rename)
  │   ├─ QueryDslSortBuilder.java                    (package rename)
  │   ├─ QueryUtil.java                              (package rename)
  │   └─ entity/BaseEntity.java                      (package rename)
  └─ src/test/java/com/factory/common/persistence/
      └─ AbstractAppDataSourceConfigTest.java        🆕 신설

tools/new-app/
  ├─ new-app.sh                                      (Step 15.5 신설 — Config 자동 생성)
  └─ tests/test-e2e.sh                               (Config 생성 검증 + bootRun 검증 추가)

settings.gradle                                      (:common-querydsl → :common-persistence)
build-logic/src/main/groovy/factory.common-module.gradle (참조 경우 rename)

# 전체 build.gradle 의 project(':common:common-querydsl') 치환 (약 8곳)
apps/README.md 의 예시, core/*/build.gradle 도 해당

# 문서 갱신
docs/architecture.md                                 (common-persistence 언급 갱신 + multi-DS flow 추가)
docs/conventions/decisions-infra.md                  (I-0N 결정 추가 가능)
docs/conventions/module-dependencies.md              (common-persistence 이름)
docs/conventions/naming.md                           (관련 언급 시)
docs/guides/onboarding.md §5                         (자동 생성 config 언급)
docs/backlog.md                                      (Item 10b archive + Item 10 Task 7 로 deferred 했던 것 해소)
README.md                                            (필요시)

# 실제 Spring Boot autoconfig 등록
common/common-persistence/src/main/resources/META-INF/spring/
  org.springframework.boot.autoconfigure.AutoConfiguration.imports (package rename)
```

### Task breakdown (writing-plans 단계에서 확정)

예상 Task 구성:
1. common-querydsl → common-persistence rename (Gradle + Java + imports + 문서)
2. AbstractAppDataSourceConfig 작성 + 단위 테스트
3. new-app.sh 확장 — Config 자동 생성
4. E2E 테스트 확장 — bootRun 검증
5. 문서 갱신 + backlog archive

---

## 11. Risks

| 위험 | 영향 | 완화 |
|---|---|---|
| Rename 중 참조 누락 | 빌드 실패 | ArchUnit + Gradle dependency 강제 — 놓치면 compile error |
| Abstract class 의 annotation 제약 | `@EnableJpaRepositories` basePackages 배열 리터럴 필요 | Concrete 클래스에 명시 — Abstract 는 빈 로직만 |
| 같은 Repository 빈 N개 생성 | 소비자 `@Qualifier` 없으면 ambiguous | `entityManagerFactoryRef` 로 Spring Data JPA 가 자동 구분 — 검증 필요 |
| Flyway migration 실행 순서 | 앱 간 의존 없음 — 각자 독립 | 문제 없음 |
| bootstrap 의 Primary DataSource 와 충돌 | Repository auto-inject 가 Primary 로 감 | `@Qualifier` 필수 + `@EnableJpaRepositories` 의 EMF ref 명시 |
| Testcontainer 시나리오 복잡도 | 테스트 환경 세팅 오래 걸림 | 단일 Testcontainers Postgres + 여러 schema 로 시뮬 |

---

## 12. Success Criteria

- [ ] `common-persistence` 모듈로 rename 완료, 모든 참조 갱신됨, 빌드 + 기존 테스트 통과
- [ ] `AbstractAppDataSourceConfig` 작성 + 단위 테스트 통과
- [ ] `new-app.sh testapp` 실행 시 `TestappDataSourceConfig.java` 자동 생성
- [ ] Spring bootRun 시 testapp schema 에 Flyway migration 자동 실행
- [ ] Bootstrap 기존 단일 DataSource 는 여전히 정상 — 기존 `UserServiceImplContractTest` 등 회귀 없음
- [ ] 문서 5 개 갱신 (architecture, decisions-infra, module-dependencies, onboarding §5, backlog)
- [ ] `docs-check.sh` 3/3 PASS 유지
- [ ] main 머지 + push
