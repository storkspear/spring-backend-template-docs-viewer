# App Scaffolding (`new-app.sh`)

이 문서는 새로운 앱 도메인 모듈을 생성하는 `tools/new-app/new-app.sh` 스크립트를 정리합니다.

템플릿은 하나의 바이너리로 여러 앱을 호스팅하는 **모듈러 모놀리스** 구조입니다. 앱을 추가할 때 Gradle 모듈, AutoConfiguration, 컨트롤러 스켈레톤, Flyway 마이그레이션, DataSource 설정, `.env` 변수, Postgres schema/role 까지 여러 곳을 동시에 건드려야 하는데, 이를 수작업으로 반복하면 실수가 쌓입니다. `new-app.sh` 는 이 과정을 **한 번에, 멱등하게** 수행합니다.

---

## 실행 방법

프로젝트 루트(`settings.gradle` 이 있는 디렉토리) 에서 실행합니다.

```bash
./tools/new-app/new-app.sh <slug>
```

예:

```bash
./tools/new-app/new-app.sh gymlog
./tools/new-app/new-app.sh my-app
./tools/new-app/new-app.sh fintrack2
```

### 인자

| 인자 | 설명 |
|---|---|
| `<slug>` | 앱 식별자. 소문자 알파벳으로 시작, 소문자/숫자/하이픈만 허용 |
| `--provision-db` | Postgres schema + role 까지 자동 생성 (DATABASE_URL 환경변수 필요) |

### slug 검증

스크립트는 다음 정규식으로 slug 를 검증합니다.

```bash
if ! [[ "$SLUG" =~ ^[a-z][a-z0-9-]*$ ]]; then
    fail "유효하지 않은 slug: '${SLUG}'. 소문자 알파벳으로 시작, 소문자/숫자/하이픈만 허용."
fi
```

내부적으로는 같은 slug 에서 세 가지 변형이 만들어집니다.

| 변형 | 규칙 | `my-app` 예시 |
|---|---|---|
| `SLUG` | 원본 | `my-app` |
| `SLUG_PASCAL` | Pascal case (URL 경로, 클래스명) | `MyApp` |
| `SLUG_UPPER` | UPPER_SNAKE (환경변수) | `MY_APP` |
| `SLUG_PACKAGE` | 하이픈 제거 (Java 패키지, Postgres 식별자) | `myapp` |

Postgres 는 식별자에 하이픈을 허용하지 않으므로 schema/role 이름에는 `SLUG_PACKAGE` 를 사용합니다.

---

## 자동으로 생성되는 파일

`apps/app-<slug>/` 디렉토리 하위에 다음이 생성됩니다.

### Gradle 모듈

```
apps/app-<slug>/
└── build.gradle
```

핵심 의존은 아래와 같습니다.

```gradle
// tools/new-app/new-app.sh — build.gradle 템플릿
dependencies {
    implementation project(':core:core-auth-api')
    implementation project(':core:core-user-api')
    implementation project(':core:core-device-api')
    implementation project(':core:core-push-api')
    implementation project(':common:common-web')
    implementation project(':common:common-persistence')
    implementation project(':common:common-security')

    // QueryDsl
    implementation "com.querydsl:querydsl-jpa:${querydslVersion}:jakarta"
    annotationProcessor "com.querydsl:querydsl-apt:${querydslVersion}:jakarta"

    implementation 'org.flywaydb:flyway-core'
    runtimeOnly 'org.flywaydb:flyway-database-postgresql'
    runtimeOnly 'org.postgresql:postgresql'
    // ...
}
```

앱 모듈은 `core-*-api` 만 의존합니다. `core-*-impl` 에 직접 의존하지 않아서 모듈 경계가 지켜집니다.

### Java 컨트롤러

```
apps/app-<slug>/src/main/java/com/factory/apps/<slugPackage>/
├── controller/
│   └── <SlugPascal>HealthController.java
├── auth/
│   └── <SlugPascal>AuthController.java
├── service/
├── repository/
├── entity/
└── config/
    ├── <SlugPascal>AppAutoConfiguration.java
    └── <SlugPascal>DataSourceConfig.java
```

**HealthController** 는 `GET /api/apps/<slug>/health` 를 제공하여 빠르게 동작 확인을 할 수 있게 해줍니다.

```java
@RestController
@RequestMapping("/api/apps/<slug>")
@Tag(name = "<slug>", description = "<SlugPascal> 앱 API")
public class <SlugPascal>HealthController {

    @GetMapping("/health")
    public ApiResponse<Map<String, String>> health() {
        return ApiResponse.ok(Map.of("app", "<slug>", "status", "ok"));
    }
}
```

**AuthController** 는 `core/core-auth-impl/src/main/java/com/factory/core/auth/impl/controller/AuthController.java` 를 레퍼런스 소스로 삼아 복제됩니다. `AuthPort` 에 위임하는 얇은 컨트롤러이며, 경로는 `/api/apps/<slug>/auth/*` 입니다.

> `core-auth-impl` 의 `AuthController` 는 `@Import` 되지 않아 런타임 bean 으로 등록되지 않습니다. 앱 모듈이 추가되는 순간부터 해당 slug 의 인증 엔드포인트만 노출됩니다. 템플릿 상태(앱 0개) 에서는 인증 엔드포인트가 전혀 노출되지 않습니다.

### AutoConfiguration

```java
// apps/app-<slug>/src/main/java/.../config/<SlugPascal>AppAutoConfiguration.java
@AutoConfiguration
@ComponentScan(basePackages = "com.factory.apps.<slugPackage>")
public class <SlugPascal>AppAutoConfiguration {
}
```

Spring Boot 가 이를 인식하도록 `AutoConfiguration.imports` 파일도 같이 생성됩니다.

```
apps/app-<slug>/src/main/resources/META-INF/spring/
└── org.springframework.boot.autoconfigure.AutoConfiguration.imports
```

내용:

```
com.factory.apps.<slugPackage>.config.<SlugPascal>AppAutoConfiguration
```

### DataSource Config

각 앱은 **독립된 schema + DataSource + Flyway 히스토리**를 갖습니다. `<SlugPascal>DataSourceConfig` 가 이를 담당합니다.

```java
// apps/app-<slug>/src/main/java/.../config/<SlugPascal>DataSourceConfig.java
@Configuration
@EnableJpaRepositories(
    basePackages = "com.factory.apps.<slugPackage>.repository",
    entityManagerFactoryRef = "<slugPackage>EntityManagerFactory",
    transactionManagerRef = "<slugPackage>TransactionManager"
)
public class <SlugPascal>DataSourceConfig extends AbstractAppDataSourceConfig {

    public <SlugPascal>DataSourceConfig(
        @Value("${<SLUG_UPPER>_DB_URL}") String url,
        @Value("${<SLUG_UPPER>_DB_USER}") String user,
        @Value("${<SLUG_UPPER>_DB_PASSWORD}") String password
    ) {
        super("<slugPackage>", url, user, password);
    }

    @Bean(name = "<slugPackage>DataSource")
    public DataSource <slugPackage>DataSource() {
        return buildDataSource();
    }

    @Bean(name = "<slugPackage>EntityManagerFactory")
    @DependsOn("<slugPackage>Flyway")  // Flyway 선행 → hbm2ddl=validate 통과
    public LocalContainerEntityManagerFactoryBean <slugPackage>EntityManagerFactory(
        @Qualifier("<slugPackage>DataSource") DataSource ds
    ) {
        return buildEntityManagerFactory(ds);
    }
    // ... Flyway, TransactionManager 빈도 동일 패턴
}
```

`AbstractAppDataSourceConfig` 가 build\* 헬퍼를 제공하고 concrete class 가 `@Bean` 으로 래핑하는 구조입니다. 이렇게 하면 앱마다 `HikariCP` pool 이 하나씩 생기고, 빈 이름이 `<slugPackage>` prefix 로 유니크하게 갈라져 여러 앱이 한 JVM 에서 충돌 없이 공존합니다.

Repository scan 이 `apps.<slugPackage>.repository` 만 대상으로 한정되는 이유는, `core-*` 레포지토리가 이미 자기 `@EnableJpaRepositories` 에서 default EMF 에 등록되었기 때문입니다. 여기서 다시 core 패키지를 스캔하면 `BeanDefinitionOverrideException` 이 납니다.

### Flyway Migration

```
apps/app-<slug>/src/main/resources/db/migration/<slug>/
├── V001__init_users.sql
├── V002__init_social_identities.sql
├── V003__init_refresh_tokens.sql
├── V004__init_email_verification_tokens.sql
├── V005__init_password_reset_tokens.sql
└── V006__init_devices.sql
```

V001~V006 은 인증/디바이스 공통 테이블입니다 (`core-auth`, `core-user`, `core-device` 엔티티에 매핑). V007 이상부터는 앱 도메인 테이블을 직접 작성합니다.

마이그레이션 경로가 `db/migration/<slug>/` 처럼 slug 별로 격리되어 있어서, 각 앱 DataSource 의 Flyway 가 자기 디렉토리만 읽습니다.

### README

`apps/app-<slug>/README.md` 에 해당 앱의 구조와 템플릿 동기화 방법이 기록됩니다. `template-v*` 태그가 있으면 그 버전을 함께 기록합니다.

### settings.gradle / bootstrap/build.gradle 업데이트

두 파일에 자동으로 줄이 추가됩니다.

```gradle
// settings.gradle
include ':apps:app-<slug>'
```

```gradle
// bootstrap/build.gradle
dependencies {
    // ...
    implementation project(':apps:app-<slug>')
}
```

bootstrap 은 앱 모듈을 `implementation` 으로 의존해야 `@AutoConfiguration` 이 활성화되고 컨트롤러가 런타임에 노출됩니다.

---

## `.env` 변수 주입

`.env` 파일이 없으면 `.env.example` 에서 복사하고, 다음 변수들을 추가합니다 (이미 있으면 skip).

### DB 변수

```env
<SLUG_UPPER>_DB_URL=jdbc:postgresql://<host>:5432/postgres?currentSchema=<slugPackage>
<SLUG_UPPER>_DB_USER=<slugPackage>_app
<SLUG_UPPER>_DB_PASSWORD=CHANGE_ME
```

`<host>` 는 수동으로 교체해야 합니다 (로컬은 `localhost:5433`, 운영은 Supabase pooler 호스트 등). `--provision-db` 를 지정하면 비밀번호는 자동으로 생성되어 치환됩니다.

### MinIO 버킷

```env
APP_STORAGE_MINIO_BUCKETS_<N>=<slug>-bucket
```

`<N>` 은 기존 `APP_STORAGE_MINIO_BUCKETS_*` 변수들의 최대 인덱스 + 1 로 결정됩니다. Spring 기동 시 `BucketProvisioner` 가 해당 이름의 버킷을 MinIO 에 자동 생성합니다.

### 소셜 로그인 Credentials

```env
APP_CREDENTIALS_<SLUG_UPPER>_GOOGLE_CLIENT_IDS_0=CHANGE_ME
APP_CREDENTIALS_<SLUG_UPPER>_GOOGLE_CLIENT_IDS_1=CHANGE_ME
APP_CREDENTIALS_<SLUG_UPPER>_APPLE_BUNDLE_ID=com.example.<slugLower>
```

실제 값 발급 방법은 `docs/social-auth-setup.md` 를 참조합니다.

### 멱등성

`.env` 에 이미 키가 있으면 덮어쓰지 않고 skip 합니다.

```bash
# tools/new-app/new-app.sh — inject_env_line 헬퍼
if grep -qE "^${key}=" .env 2>/dev/null; then
    info "  skip: ${key} already in .env"
    return 0
fi
echo "${key}=${value}" >> .env
```

---

## `--provision-db` 옵션

이 옵션을 지정하면 스크립트가 `psql` 로 `infra/scripts/init-app-schema.sql` 을 실행해 schema + role 까지 만듭니다.

### 사용 전 필요 조건

**로컬 docker** — `.env` 기본값이 자동 사용되므로 export 불필요:

```bash
./tools/new-app/new-app.sh gymlog --provision-db
# .env 의 DATABASE_URL=postgresql://postgres:dev@localhost:5433/postgres 자동 로드
```

**운영 DB** (Supabase 등) — admin credential 은 `.env` 에 저장 금지, shell export 로만:

```bash
export DATABASE_URL='postgresql://postgres.<ref>:<pw>@<supabase-host>:5432/postgres'
./tools/new-app/new-app.sh gymlog --provision-db
# shell 환경변수가 .env 값보다 우선 — 운영 DB 에 provision
```

- `DATABASE_URL` 은 schema/role 을 생성할 권한이 있는 **관리자 credential** 이어야 합니다 (앱 role 아님).
- 로컬에선 `bootstrap.sh` 로 띄운 Postgres 컨테이너 superuser, 운영에선 Supabase `postgres` 계정입니다.
- `psql` 이 설치되어 있어야 합니다 (`brew install libpq` 또는 `postgresql`).

### provision_db 동작

```bash
# tools/new-app/new-app.sh
provision_db() {
    local SLUG_IDENT="$1"      # schema 이름
    local SLUG_PACKAGE="$2"    # role prefix

    local password
    password=$(openssl rand -hex 24)

    APP_SLUG="${SLUG_IDENT}" \
    APP_ROLE="${SLUG_PACKAGE}_app" \
    APP_PASSWORD="${password}" \
    psql "${DATABASE_URL}" \
        -v ON_ERROR_STOP=1 \
        -v app_slug="${SLUG_IDENT}" \
        -v app_role="${SLUG_PACKAGE}_app" \
        -v app_password="${password}" \
        -f "${REPO_ROOT}/infra/scripts/init-app-schema.sql"

    # .env 의 _DB_PASSWORD 를 생성된 값으로 교체
    if grep -q "^${SLUG_UPPER}_DB_PASSWORD=CHANGE_ME$" .env; then
        sed -i.bak "s|^${SLUG_UPPER}_DB_PASSWORD=CHANGE_ME$|${SLUG_UPPER}_DB_PASSWORD=${password}|" .env
        rm -f .env.bak
    fi
}
```

`openssl rand -hex 24` 로 48자 hex 비밀번호를 만들고, `init-app-schema.sql` 실행 후 `.env` 의 placeholder 를 해당 비밀번호로 치환합니다.

### init-app-schema.sql 이 하는 일

```sql
-- infra/scripts/init-app-schema.sql
-- 1. Schema 생성 (이미 있으면 skip)
CREATE SCHEMA IF NOT EXISTS <app_slug>

-- 2. Role 생성 (이미 있으면 skip)
CREATE ROLE <app_role> LOGIN PASSWORD <app_password>
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = <app_role>)

-- 3. schema 권한 부여 — Flyway 가 flyway_schema_history 생성 / DDL 실행 가능해야 함
GRANT USAGE, CREATE ON SCHEMA <app_slug> TO <app_role>
GRANT ALL ON ALL TABLES IN SCHEMA <app_slug> TO <app_role>
GRANT ALL ON ALL SEQUENCES IN SCHEMA <app_slug> TO <app_role>

-- 4. Default privileges — 이후 생성될 테이블/시퀀스에도 자동 적용
ALTER DEFAULT PRIVILEGES IN SCHEMA <app_slug> GRANT ALL ON TABLES TO <app_role>
ALTER DEFAULT PRIVILEGES IN SCHEMA <app_slug> GRANT ALL ON SEQUENCES TO <app_role>

-- 5. public schema 접근 금지
REVOKE ALL ON SCHEMA public FROM <app_role>
```

스크립트는 slug 형식도 방어합니다 — Postgres identifier 는 소문자/숫자/밑줄만 허용하므로, 하이픈이 포함된 slug 는 내부적으로 `SLUG_PACKAGE`(하이픈 제거) 로 변환되어 전달됩니다. 형식이 어긋나면 `division-by-zero` trick 으로 실행이 중단됩니다.

---

## 멱등성

`new-app.sh` 는 같은 slug 로 두 번 실행해도 안전하도록 설계되지는 **않았습니다**. 앱 모듈 디렉토리가 이미 있으면 즉시 종료합니다.

```bash
APP_DIR="${REPO_ROOT}/apps/app-${SLUG}"
if [[ -d "${APP_DIR}" ]]; then
    fail "이미 존재합니다: ${APP_DIR}"
fi
```

반면 **부분적인 요소들**은 멱등합니다.

| 대상 | 멱등성 |
|---|---|
| `apps/app-<slug>/` 디렉토리 | **없음** — 존재 시 스크립트 종료 |
| `settings.gradle` 의 include | 있음 — grep 체크 후 skip |
| `bootstrap/build.gradle` 의 implementation | 있음 — 같은 줄이 있으면 skip |
| `.env` 변수 | 있음 — 키가 있으면 skip |
| Postgres schema 생성 | 있음 — `CREATE SCHEMA IF NOT EXISTS` |
| Postgres role 생성 | 있음 — `pg_roles` 체크 후 skip |

따라서 스크립트 실행 중 `apps/app-<slug>/` 생성 후 실패한 경우, 재시도 전에 해당 디렉토리를 수동으로 삭제해야 합니다. DB schema 는 그대로 두어도 재실행이 안전합니다.

---

## 실행 후 남는 수동 작업

스크립트가 끝나면 아래 안내가 출력됩니다.

```
남은 수동 작업:

1. Postgres schema 수동 생성 (--provision-db 재실행으로도 가능):
   export APP_SLUG=<slug> APP_ROLE=<slug>_app APP_PASSWORD='강력한비번'
   psql "$DATABASE_URL" -f infra/scripts/init-app-schema.sql

2. .env 의 placeholder 값 실제 값으로 교체:
   - <SLUG_UPPER>_DB_URL 의 <host> (Supabase pooler 호스트 등)
   - APP_CREDENTIALS_<SLUG_UPPER>_GOOGLE_CLIENT_IDS_0/1, _APPLE_BUNDLE_ID
   → 발급 방법: docs/social-auth-setup.md

3. 도메인 테이블 작성:
   apps/app-<slug>/src/main/resources/db/migration/<slug>/V007__init_domain.sql

4. 커밋:
   feat(apps): scaffold app-<slug>
```

요약하면 사람이 직접 해야 하는 것은 네 가지입니다.

1. `--provision-db` 를 쓰지 않았다면 Postgres schema 를 수동 생성
2. `.env` 의 `<host>` 와 소셜 로그인 credential placeholder 를 실제 값으로 교체
3. 도메인 테이블용 `V007__init_domain.sql` 작성
4. 커밋

---

## 문제 해결

### "이미 존재합니다" 에러

스크립트 중간에 실패했거나 일부만 생성된 경우 발생합니다.

```bash
rm -rf apps/app-<slug>
# settings.gradle 과 bootstrap/build.gradle 에서 해당 줄도 수동 제거
./tools/new-app/new-app.sh <slug>
```

### Spring bootRun 시 Flyway validate 실패

V001~V006 의 체크섬이 맞지 않으면 Flyway 가 거부합니다. 공통 마이그레이션 파일을 수정하지 않았다면 원인은 대개 DB 에 남은 이전 실행 흔적입니다. schema 를 drop 하고 재생성합니다.

```sql
DROP SCHEMA <slug> CASCADE;
-- 그 다음 init-app-schema.sql 재실행
```

### `<SLUG_UPPER>_DB_PASSWORD=CHANGE_ME` 가 남아있음

`--provision-db` 를 쓰지 않았거나, 스크립트가 sed 치환 전에 실패한 경우입니다. `.env` 에서 직접 값을 넣거나, schema 를 drop 한 뒤 `--provision-db` 로 재실행하면 자동 치환됩니다.

### Postgres identifier 에러 (하이픈 관련)

slug 자체는 하이픈을 허용하지만 Postgres schema/role 이름에는 `SLUG_PACKAGE` (하이픈 제거 버전) 가 사용됩니다. `my-app` slug 로 만든 앱의 schema 는 `myapp` 입니다. 수동 psql 명령 실행 시 `APP_SLUG` 환경변수는 반드시 하이픈을 뺀 버전으로 설정해야 합니다.

---

## bootstrap.sh 와의 관계

`tools/bootstrap.sh` 는 파생 레포를 처음 클론했을 때 **환경 부팅** 을 담당합니다. JDK/Docker/Node prereqs 확인, `.env` 준비, docker compose(postgres + minio) 기동, Postgres ready 대기까지 수행합니다. bootstrap 자체는 앱 모듈을 만들지 않습니다.

사용 순서는 이렇습니다.

```bash
# 1. 환경 부팅 (처음 한 번) — .env 자동 생성, DATABASE_URL 기본값 포함
./tools/bootstrap.sh

# 2. 앱 모듈 생성 (앱마다 한 번) — 로컬 docker 는 export 불필요
./tools/new-app/new-app.sh gymlog --provision-db

# 3. Spring Boot 기동
./gradlew :bootstrap:bootRun
```

---

## 요약

- `new-app.sh <slug>` 는 Gradle 모듈, Java 컨트롤러/AutoConfiguration/DataSource, Flyway V001~V006, `.env` 변수를 한 번에 생성합니다.
- `--provision-db` 는 Postgres schema + role 을 `infra/scripts/init-app-schema.sql` 로 자동 생성하고 `.env` 비밀번호 placeholder 를 치환합니다.
- slug 는 세 가지 변형(`SLUG`, `SLUG_PASCAL`, `SLUG_UPPER`, `SLUG_PACKAGE`) 으로 전개되어 URL 경로/클래스명/환경변수/Postgres 식별자에 각각 쓰입니다.
- 각 앱은 독립된 schema + DataSource + Flyway 히스토리를 가지며, 빈 이름이 `<slugPackage>` prefix 로 격리됩니다.
- 디렉토리 자체는 멱등하지 않지만 `.env` 주입과 DB schema/role 생성은 멱등합니다.
- 실행 후 수동 작업은 `.env` 의 host/credential 치환, 도메인 테이블 V007 작성, 커밋입니다.
