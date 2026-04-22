# Item 10b — Multi-DataSource Wiring Implementation Plan

> **Status**: ✅ Complete (2026-04-19). 상세 결과는 [`docs/backlog.md`](../backlog.md) archive 섹션 + [`docs/conventions/decisions-infra.md I-08`](../conventions/decisions-infra.md) 참조. 본 plan 은 작업 당시 기록용.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Template 에 multi-DataSource 패턴 + helper + new-app.sh 자동 생성 추가. 파생 레포가 `new-app.sh <slug>` 로 독립적 DataSource 빈을 자동 wiring 받도록.

**Architecture:** `common-querydsl` 모듈을 `common-persistence` 로 rename 후 `AbstractAppDataSourceConfig` 추상 클래스 추가. new-app.sh 가 `<Slug>DataSourceConfig.java` 를 자동 생성. Bootstrap 기존 단일 DataSource (core schema) 는 그대로 유지.

**Tech Stack:** Java 21, Spring Boot 3.3, Spring Data JPA, Hibernate, Flyway, HikariCP, QueryDsl 5.1.0, Gradle 8.x

**Design spec**: [`2026-04-19-item10b-multi-datasource-design.md`](./2026-04-19-item10b-multi-datasource-design.md)

---

## 메타

- **작성일**: 2026-04-19
- **예상 작업량**: 4~5 시간
- **선행**: Item 10 (`ff4bcbb`), Item 11 (`03112a6`), Design spec 승인 (`94a5ab1`)
- **현재 브랜치**: `feature/item10b-multi-datasource` (체크아웃됨)

---

## File Structure

### 수정 대상 (rename 영향)
```
Gradle:
  settings.gradle                                    (include path 수정)
  bootstrap/build.gradle                             (project 참조 수정)
  core/core-user-impl/build.gradle                   (project 참조 수정)
  core/core-device-impl/build.gradle                 (project 참조 수정)

Java (package 선언 + import):
  common/common-querydsl/ 전체 디렉토리 → common/common-persistence/
    src/main/java/com/factory/common/querydsl/**   → com/factory/common/persistence/**
    src/test/java/com/factory/common/querydsl/**   → com/factory/common/persistence/**
  core/core-user-impl/src/main/java/com/factory/core/user/impl/entity/User.java  (1 import)
  core/core-device-impl/src/main/java/com/factory/core/device/impl/entity/Device.java  (1 import)

META-INF:
  common/common-persistence/src/main/resources/META-INF/spring/
    org.springframework.boot.autoconfigure.AutoConfiguration.imports (package rename)

문서:
  docs/architecture.md              (common-querydsl → common-persistence 언급)
  docs/philosophy.md                (line 305, 323 언급)
  docs/conventions/module-dependencies.md  (line 104 예시)
  docs/plans/2026-04-18-item9-infra-docs.md  (plan 의 A.2 인벤토리 — 역사 기록이라 유지 고민, 본 plan Task 1 에서 판단)
  common/common-persistence/README.md       (rename)
  common/common-web/README.md               (line 23 언급)
```

### 신설 파일
```
common/common-persistence/src/main/java/com/factory/common/persistence/
  AbstractAppDataSourceConfig.java          (Item 10b core)
common/common-persistence/src/test/java/com/factory/common/persistence/
  AbstractAppDataSourceConfigTest.java      (단위 테스트)
```

### 수정 (로직)
```
tools/new-app/new-app.sh                    (Step 13.5 신설 — Config 자동 생성)
tools/new-app/tests/test-e2e.sh             (Config 파일 존재 + bootRun 부팅 검증 추가)
tools/docs-check/exclusions.conf            (common-querydsl → common-persistence 문구 변경으로 C1 영향 없을 것, 만약 있으면 조정)
```

### 최종 문서 갱신
```
docs/guides/onboarding.md §5                (Config 자동 생성 언급)
docs/backlog.md                             (Item 10b archive)
```

---

## Tasks (TDD, bite-sized)

### Task 1: `common-querydsl` → `common-persistence` rename

**Files:**
- Rename: `common/common-querydsl/` → `common/common-persistence/` (디렉토리 전체)
- Rename: `common/common-persistence/src/{main,test}/java/com/factory/common/querydsl/` → `com/factory/common/persistence/`
- Modify: `settings.gradle`
- Modify: `bootstrap/build.gradle`
- Modify: `core/core-user-impl/build.gradle`
- Modify: `core/core-device-impl/build.gradle`
- Modify: `core/core-user-impl/src/main/java/com/factory/core/user/impl/entity/User.java` (import)
- Modify: `core/core-device-impl/src/main/java/com/factory/core/device/impl/entity/Device.java` (import)
- Modify: `common/common-persistence/src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`
- Modify: `common/common-persistence/README.md` (제목)
- Modify: `common/common-web/README.md` (line 23)
- Modify: `docs/philosophy.md` (line 305, 323)
- Modify: `docs/conventions/module-dependencies.md` (line 104)
- Modify: `docs/architecture.md` (common-querydsl 언급 전부)

- [ ] **Step 1: 현재 전체 빌드 상태 확인 (baseline)**

```bash
./gradlew build --no-daemon -q
echo "exit: $?"
```
Expected: `exit: 0`. 실패 시 baseline 부터 fix 후 Task 1 재시작.

- [ ] **Step 2: Gradle 모듈 이름 + 디렉토리 rename**

```bash
git mv common/common-querydsl common/common-persistence
```

- [ ] **Step 3: Java 패키지 디렉토리 rename (main + test)**

```bash
git mv common/common-persistence/src/main/java/com/factory/common/querydsl \
       common/common-persistence/src/main/java/com/factory/common/persistence
git mv common/common-persistence/src/test/java/com/factory/common/querydsl \
       common/common-persistence/src/test/java/com/factory/common/persistence
```

- [ ] **Step 4: Java 파일 package 선언 + import 수정 (bulk sed)**

```bash
# common-persistence 내부 파일들 package 선언
find common/common-persistence/src -name "*.java" -exec \
  sed -i.bak 's|package com\.factory\.common\.querydsl|package com.factory.common.persistence|g; s|import com\.factory\.common\.querydsl|import com.factory.common.persistence|g' {} +
find common/common-persistence -name "*.bak" -delete

# User.java, Device.java 의 BaseEntity import
sed -i.bak 's|import com\.factory\.common\.querydsl\.entity\.BaseEntity|import com.factory.common.persistence.entity.BaseEntity|' \
  core/core-user-impl/src/main/java/com/factory/core/user/impl/entity/User.java \
  core/core-device-impl/src/main/java/com/factory/core/device/impl/entity/Device.java
rm -f core/core-user-impl/src/main/java/com/factory/core/user/impl/entity/User.java.bak
rm -f core/core-device-impl/src/main/java/com/factory/core/device/impl/entity/Device.java.bak
```

검증:
```bash
grep -rn "common\.querydsl" common/common-persistence core/ --include="*.java"
# 출력 0 줄이어야 함
```

- [ ] **Step 5: Gradle 참조 수정**

```bash
# settings.gradle
sed -i.bak "s|':common:common-querydsl'|':common:common-persistence'|" settings.gradle
rm settings.gradle.bak

# build.gradle 들
for f in bootstrap/build.gradle core/core-user-impl/build.gradle core/core-device-impl/build.gradle; do
    sed -i.bak "s|':common:common-querydsl'|':common:common-persistence'|" "$f"
    rm "${f}.bak"
done
```

검증:
```bash
grep -rn "common-querydsl" --include="*.gradle" .
# 출력 0 줄
```

- [ ] **Step 6: AutoConfiguration.imports 수정**

```bash
sed -i.bak 's|com\.factory\.common\.querydsl|com.factory.common.persistence|' \
  common/common-persistence/src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
rm common/common-persistence/src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports.bak
```

- [ ] **Step 7: 문서 참조 수정**

```bash
# README 갱신
sed -i.bak 's|common-querydsl|common-persistence|g' common/common-persistence/README.md
rm common/common-persistence/README.md.bak

sed -i.bak 's|common-querydsl|common-persistence|g' common/common-web/README.md
rm common/common-web/README.md.bak

# conventions/module-dependencies.md
sed -i.bak 's|common-querydsl|common-persistence|g' docs/conventions/module-dependencies.md
rm docs/conventions/module-dependencies.md.bak

# philosophy.md
sed -i.bak 's|common-querydsl|common-persistence|g' docs/philosophy.md
rm docs/philosophy.md.bak

# architecture.md
sed -i.bak 's|common-querydsl|common-persistence|g' docs/architecture.md
rm docs/architecture.md.bak
```

**주의**: `docs/plans/2026-04-18-item9-infra-docs.md` 와 `docs/plans/2026-04-19-item10b-multi-datasource-design.md` 는 **역사 기록 / 본 작업 맥락** 이므로 rename 하지 않음 (plan 파일 자체는 작성 시점의 이름을 보존).

검증:
```bash
grep -rn "common-querydsl" docs/ common/ bootstrap/ core/ --include="*.md" --include="*.java" --include="*.gradle" --include="*.imports" --include="*.yml" 2>/dev/null \
  | grep -v /plans/
# 출력 0 줄 이어야 함 (plan 파일은 의도적 유지)
```

- [ ] **Step 8: 빌드 + 테스트 통과 확인**

```bash
./gradlew clean build --no-daemon 2>&1 | tail -10
```
Expected: `BUILD SUCCESSFUL`. 기존 테스트 (BaseEntityTest, QueryDslSortBuilderTest, QueryDslPredicateBuilderTest, QueryUtilTest, ArchUnit 등) 전부 통과.

실패 시:
- ArchUnit 이 `common.querydsl` 경로 하드코딩했다면 `ArchitectureRules.java` 확인
- 누락 import 발견되면 해당 파일 수정

- [ ] **Step 9: docs-check 확인**

```bash
./tools/docs-check/docs-contract-test.sh
```
Expected: 3/3 PASS. 실패 시 해당 drift fix.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor(common)!: common-querydsl → common-persistence rename

모듈이 DataSource + JPA + QueryDsl + BaseEntity 를 포괄하게 되어 이름을
내용 반영하도록 rename. Item 10b 의 multi-DataSource wiring 선행 작업.

변경: Gradle 모듈, Java 패키지, import, AutoConfiguration.imports,
관련 문서 전부. 파생 레포 0개 상태라 breaking 영향 없음.

BREAKING CHANGE: Gradle :common:common-querydsl → :common:common-persistence
Java com.factory.common.querydsl → com.factory.common.persistence
"
```

---

### Task 2: `AbstractAppDataSourceConfig` 작성 + 단위 테스트

**Files:**
- Create: `common/common-persistence/src/main/java/com/factory/common/persistence/AbstractAppDataSourceConfig.java`
- Create: `common/common-persistence/src/test/java/com/factory/common/persistence/AbstractAppDataSourceConfigTest.java`

- [ ] **Step 1: 단위 테스트 작성 (실패 예상)**

```java
package com.factory.common.persistence;

import com.factory.common.testing.AbstractIntegrationTest;
import com.zaxxer.hikari.HikariDataSource;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;

import static org.assertj.core.api.Assertions.assertThat;

@Import(AbstractAppDataSourceConfigTest.TestConfig.class)
class AbstractAppDataSourceConfigTest extends AbstractIntegrationTest {

    @Autowired
    @Qualifier("testappDataSource")
    DataSource testappDataSource;

    @Autowired
    @Qualifier("testappEntityManagerFactory")
    LocalContainerEntityManagerFactoryBean testappEmf;

    @Autowired
    @Qualifier("testappTransactionManager")
    PlatformTransactionManager testappTm;

    @Autowired
    @Qualifier("testappFlyway")
    Flyway testappFlyway;

    @Test
    void registersAllFourBeans() {
        assertThat(testappDataSource).isInstanceOf(HikariDataSource.class);
        assertThat(testappEmf).isNotNull();
        assertThat(testappTm).isNotNull();
        assertThat(testappFlyway).isNotNull();
    }

    @Test
    void dataSourceUsesHikariPool() {
        HikariDataSource hikari = (HikariDataSource) testappDataSource;
        assertThat(hikari.getMaximumPoolSize()).isEqualTo(10);
    }

    @TestConfiguration
    @EnableJpaRepositories(
        basePackages = "com.factory.common.persistence",
        entityManagerFactoryRef = "testappEntityManagerFactory",
        transactionManagerRef = "testappTransactionManager"
    )
    static class TestConfig extends AbstractAppDataSourceConfig {
        public TestConfig() {
            super("testapp",
                  "jdbc:postgresql://localhost:5433/postgres?currentSchema=testapp",
                  "postgres",
                  "dev");
        }
    }
}
```

- [ ] **Step 2: Run test to verify fail**

```bash
./gradlew :common:common-persistence:test --no-daemon --tests AbstractAppDataSourceConfigTest 2>&1 | tail -20
```
Expected: FAIL with "AbstractAppDataSourceConfig 클래스 없음".

- [ ] **Step 3: `AbstractAppDataSourceConfig` 구현**

```java
package com.factory.common.persistence;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import jakarta.persistence.EntityManagerFactory;
import org.flywaydb.core.Flyway;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;
import java.util.Properties;

/**
 * 앱별 DataSource + JPA + Flyway wiring 의 abstract 기반.
 *
 * <p>각 앱 모듈은 이 클래스를 extends 하여 자기 DataSource 빈을 등록합니다.
 * Bean name 은 slug 를 prefix 로 자동 생성 — 앱 간 충돌 방지.
 *
 * <p>자동 제공되는 빈 (bean name = slug + suffix):
 * <ul>
 *   <li>{@code <slug>DataSource} — HikariCP 기반</li>
 *   <li>{@code <slug>EntityManagerFactory} — core + apps 엔티티 scan</li>
 *   <li>{@code <slug>TransactionManager}</li>
 *   <li>{@code <slug>Flyway} — classpath:db/migration/&lt;slug&gt; 실행</li>
 * </ul>
 *
 * <p>소비자(앱 모듈) 는 @EnableJpaRepositories 를 자기 Config 에 직접 선언해야 합니다 —
 * annotation 은 concrete 클래스에서만 설정 가능하므로 abstract 에 넣을 수 없습니다.
 *
 * <p>기본 basePackages 권장:
 * <ul>
 *   <li>com.factory.core.user.impl.repository</li>
 *   <li>com.factory.core.auth.impl.repository</li>
 *   <li>com.factory.core.device.impl.repository</li>
 *   <li>com.factory.apps.&lt;slug&gt;.repository</li>
 * </ul>
 */
@Configuration
public abstract class AbstractAppDataSourceConfig {

    /**
     * 엔티티 scan 기본 basePackages. 자식 클래스에서 apps.&lt;slug&gt; 추가.
     */
    protected static final String[] CORE_ENTITY_PACKAGES = {
        "com.factory.core.user.impl.entity",
        "com.factory.core.auth.impl.entity",
        "com.factory.core.device.impl.entity",
        "com.factory.common.persistence.entity"
    };

    /**
     * HikariCP 기본 pool size.
     */
    protected static final int DEFAULT_POOL_SIZE = 10;

    private final String slug;
    private final String url;
    private final String username;
    private final String password;

    protected AbstractAppDataSourceConfig(String slug, String url, String username, String password) {
        this.slug = slug;
        this.url = url;
        this.username = username;
        this.password = password;
    }

    /**
     * 엔티티 scan packages. 자식이 override 하여 apps.&lt;slug&gt;.entity 추가 가능.
     */
    protected String[] entityPackagesToScan() {
        String[] withApp = new String[CORE_ENTITY_PACKAGES.length + 1];
        System.arraycopy(CORE_ENTITY_PACKAGES, 0, withApp, 0, CORE_ENTITY_PACKAGES.length);
        withApp[CORE_ENTITY_PACKAGES.length] = "com.factory.apps." + slug + ".entity";
        return withApp;
    }

    @Bean
    public DataSource dataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(DEFAULT_POOL_SIZE);
        config.setPoolName(slug + "-pool");
        return new HikariDataSource(config);
    }

    @Bean
    public LocalContainerEntityManagerFactoryBean entityManagerFactory() {
        LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(dataSource());
        emf.setPackagesToScan(entityPackagesToScan());
        emf.setPersistenceUnitName(slug);

        HibernateJpaVendorAdapter vendor = new HibernateJpaVendorAdapter();
        emf.setJpaVendorAdapter(vendor);

        Properties props = new Properties();
        props.setProperty("hibernate.default_schema", slug);
        props.setProperty("hibernate.hbm2ddl.auto", "validate");
        emf.setJpaProperties(props);

        return emf;
    }

    @Bean
    public PlatformTransactionManager transactionManager() {
        JpaTransactionManager tm = new JpaTransactionManager();
        EntityManagerFactory emf = entityManagerFactory().getObject();
        if (emf == null) {
            throw new IllegalStateException("EntityManagerFactory bootstrap failed for slug=" + slug);
        }
        tm.setEntityManagerFactory(emf);
        return tm;
    }

    @Bean(initMethod = "migrate")
    public Flyway flyway() {
        return Flyway.configure()
            .dataSource(dataSource())
            .schemas(slug)
            .locations("classpath:db/migration/" + slug)
            .baselineOnMigrate(true)
            .load();
    }

    protected String slug() {
        return slug;
    }
}
```

**빈 이름 전략**: Spring 은 `@Bean` method name 을 빈 이름으로 씁니다. Abstract 는 `dataSource()`, `entityManagerFactory()` 등 generic 이름 사용 — concrete 가 `@Bean` 이름을 명시적으로 override 해야 `<slug>DataSource` 등이 됨. 이건 Task 3 에서 concrete 생성 시 처리.

**수정 필요**: 위 abstract 의 빈 이름을 concrete 가 override 가능하게 하려면 `@Bean(name = "...")` 을 concrete 에 선언해야. 그러나 @Bean annotation 은 메서드 override 해도 기본 상속 안 됨. 해결책:

**실제 접근**: Abstract 가 `@Bean` 은 달지 않고, concrete 가 super 호출 후 자기 `@Bean` method 선언:

```java
// Abstract (수정):
public DataSource buildDataSource() { /* ... */ }  // @Bean 없이
public LocalContainerEntityManagerFactoryBean buildEntityManagerFactory(DataSource ds) { /* ... */ }
public PlatformTransactionManager buildTransactionManager(EntityManagerFactoryBean emf) { /* ... */ }
public Flyway buildFlyway(DataSource ds) { /* ... */ }
```

```java
// Concrete (Task 3):
@Bean
public DataSource sumtallyDataSource() {
    return buildDataSource();
}

@Bean(name = "sumtallyEntityManagerFactory")
public LocalContainerEntityManagerFactoryBean sumtallyEntityManagerFactory(
    @Qualifier("sumtallyDataSource") DataSource ds
) {
    return buildEntityManagerFactory(ds);
}
// ... 등
```

**실제 구현 수정**: Step 3 의 code 에서 `@Bean` 제거, method 이름 `build*` 로 변경:

```java
@Configuration
public abstract class AbstractAppDataSourceConfig {

    protected static final String[] CORE_ENTITY_PACKAGES = { /* 위와 동일 */ };
    protected static final int DEFAULT_POOL_SIZE = 10;

    private final String slug;
    private final String url;
    private final String username;
    private final String password;

    protected AbstractAppDataSourceConfig(String slug, String url, String username, String password) {
        this.slug = slug;
        this.url = url;
        this.username = username;
        this.password = password;
    }

    protected String slug() { return slug; }

    protected String[] entityPackagesToScan() { /* 위와 동일 */ }

    // Build helpers (concrete 가 @Bean 으로 래핑)

    protected DataSource buildDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(DEFAULT_POOL_SIZE);
        config.setPoolName(slug + "-pool");
        return new HikariDataSource(config);
    }

    protected LocalContainerEntityManagerFactoryBean buildEntityManagerFactory(DataSource ds) {
        LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds);
        emf.setPackagesToScan(entityPackagesToScan());
        emf.setPersistenceUnitName(slug);

        HibernateJpaVendorAdapter vendor = new HibernateJpaVendorAdapter();
        emf.setJpaVendorAdapter(vendor);

        Properties props = new Properties();
        props.setProperty("hibernate.default_schema", slug);
        props.setProperty("hibernate.hbm2ddl.auto", "validate");
        emf.setJpaProperties(props);

        return emf;
    }

    protected PlatformTransactionManager buildTransactionManager(EntityManagerFactory emf) {
        JpaTransactionManager tm = new JpaTransactionManager();
        tm.setEntityManagerFactory(emf);
        return tm;
    }

    protected Flyway buildFlyway(DataSource ds) {
        return Flyway.configure()
            .dataSource(ds)
            .schemas(slug)
            .locations("classpath:db/migration/" + slug)
            .baselineOnMigrate(true)
            .load();
    }
}
```

**Test 도 수정**: 위 concrete 패턴 따라서 `TestConfig` 내부에 `@Bean` 선언:

```java
@TestConfiguration
@EnableJpaRepositories(
    basePackages = "com.factory.common.persistence",
    entityManagerFactoryRef = "testappEntityManagerFactory",
    transactionManagerRef = "testappTransactionManager"
)
static class TestConfig extends AbstractAppDataSourceConfig {
    public TestConfig() {
        super("testapp",
              "jdbc:postgresql://localhost:5433/postgres?currentSchema=testapp",
              "postgres",
              "dev");
    }

    @Bean(name = "testappDataSource")
    public DataSource testappDataSource() { return buildDataSource(); }

    @Bean(name = "testappEntityManagerFactory")
    public LocalContainerEntityManagerFactoryBean testappEntityManagerFactory(
        @org.springframework.beans.factory.annotation.Qualifier("testappDataSource") DataSource ds
    ) {
        return buildEntityManagerFactory(ds);
    }

    @Bean(name = "testappTransactionManager")
    public PlatformTransactionManager testappTransactionManager(
        @org.springframework.beans.factory.annotation.Qualifier("testappEntityManagerFactory")
        jakarta.persistence.EntityManagerFactory emf
    ) {
        return buildTransactionManager(emf);
    }

    @Bean(name = "testappFlyway", initMethod = "migrate")
    public Flyway testappFlyway(
        @org.springframework.beans.factory.annotation.Qualifier("testappDataSource") DataSource ds
    ) {
        return buildFlyway(ds);
    }
}
```

- [ ] **Step 4: Run test to verify pass**

```bash
./gradlew :common:common-persistence:test --no-daemon --tests AbstractAppDataSourceConfigTest 2>&1 | tail -10
```
Expected: `BUILD SUCCESSFUL`, `registersAllFourBeans` + `dataSourceUsesHikariPool` PASS.

**주의**: 테스트는 Testcontainers Postgres 필요. Docker daemon 실행 중이어야 함. 실패 시 Docker 상태 확인.

또한 테스트는 testapp schema 가 postgres DB 에 없으면 Flyway 가 `baselineOnMigrate=true` 로 처리. db/migration/testapp 디렉토리는 테스트 리소스에 없어도 OK (빈 migration).

- [ ] **Step 5: Commit**

```bash
git add common/common-persistence/src/
git commit -m "feat(common-persistence): AbstractAppDataSourceConfig — multi-DataSource abstract

앱별 DataSource/EMF/TM/Flyway 빈 생성의 공통 로직. Concrete Config 가
build* 헬퍼를 @Bean 으로 래핑하여 <slug>Prefix 빈 이름 부여.

Item 10b Task 2."
```

---

### Task 3: `new-app.sh` 확장 — `<Slug>DataSourceConfig.java` 자동 생성

**Files:**
- Modify: `tools/new-app/new-app.sh` (Step 13 과 Step 14 사이에 Step 13.5 추가)

- [ ] **Step 1: 테스트 코드 (test-e2e.sh 확장)**

`tools/new-app/tests/test-e2e.sh` 의 `.env 검증` 블록 뒤에 추가:

```bash
echo "=== <Slug>DataSourceConfig.java 생성 검증 ==="
CONFIG_FILE="apps/app-testapp/src/main/java/com/factory/apps/testapp/config/TestappDataSourceConfig.java"
[ -f "${CONFIG_FILE}" ] || { echo "FAIL: ${CONFIG_FILE} 없음"; exit 1; }
grep -q "extends AbstractAppDataSourceConfig" "${CONFIG_FILE}" || { echo "FAIL: abstract 상속 안 됨"; exit 1; }
grep -q "testappDataSource\|testappEntityManagerFactory\|testappTransactionManager\|testappFlyway" "${CONFIG_FILE}" || { echo "FAIL: 빈 이름 없음"; exit 1; }
echo "PASS: TestappDataSourceConfig"
```

- [ ] **Step 2: Run (fail expected — Config 파일 생성 로직 없음)**

```bash
bash tools/new-app/tests/test-e2e.sh
```
Expected: `FAIL: apps/app-testapp/.../TestappDataSourceConfig.java 없음`

- [ ] **Step 3: `new-app.sh` 에 Step 13.5 추가**

기존 Step 13 (credentials placeholder) 뒤, Step 14 (--provision-db) 앞 지점에 삽입:

```bash
# ─── Step 13.5: DataSource Config 자동 생성 ──────────────────────────────────
info "Step 13.5: ${SLUG_PASCAL}DataSourceConfig.java 생성 중..."

CONFIG_DIR="${APP_DIR}/src/main/java/${JAVA_BASE}/config"
mkdir -p "${CONFIG_DIR}"

cat > "${CONFIG_DIR}/${SLUG_PASCAL}DataSourceConfig.java" << EOF
package com.factory.apps.${SLUG_PACKAGE}.config;

import com.factory.common.persistence.AbstractAppDataSourceConfig;
import jakarta.persistence.EntityManagerFactory;
import org.flywaydb.core.Flyway;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;

/**
 * ${SLUG_PASCAL} 앱 전용 DataSource / JPA / Flyway 빈.
 *
 * <p>AbstractAppDataSourceConfig 의 build* 헬퍼를 @Bean 으로 래핑하여
 * ${SLUG_PACKAGE} prefix 빈 이름 부여.
 *
 * <p>Repository scan: core.{user,auth,device}.impl.repository + apps.${SLUG_PACKAGE}.repository.
 */
@Configuration
@EnableJpaRepositories(
    basePackages = {
        "com.factory.core.user.impl.repository",
        "com.factory.core.auth.impl.repository",
        "com.factory.core.device.impl.repository",
        "com.factory.apps.${SLUG_PACKAGE}.repository"
    },
    entityManagerFactoryRef = "${SLUG_PACKAGE}EntityManagerFactory",
    transactionManagerRef = "${SLUG_PACKAGE}TransactionManager"
)
public class ${SLUG_PASCAL}DataSourceConfig extends AbstractAppDataSourceConfig {

    public ${SLUG_PASCAL}DataSourceConfig(
        @Value("\${${SLUG_UPPER}_DB_URL}") String url,
        @Value("\${${SLUG_UPPER}_DB_USER}") String user,
        @Value("\${${SLUG_UPPER}_DB_PASSWORD}") String password
    ) {
        super("${SLUG_PACKAGE}", url, user, password);
    }

    @Bean(name = "${SLUG_PACKAGE}DataSource")
    public DataSource ${SLUG_PACKAGE}DataSource() {
        return buildDataSource();
    }

    @Bean(name = "${SLUG_PACKAGE}EntityManagerFactory")
    public LocalContainerEntityManagerFactoryBean ${SLUG_PACKAGE}EntityManagerFactory(
        @Qualifier("${SLUG_PACKAGE}DataSource") DataSource ds
    ) {
        return buildEntityManagerFactory(ds);
    }

    @Bean(name = "${SLUG_PACKAGE}TransactionManager")
    public PlatformTransactionManager ${SLUG_PACKAGE}TransactionManager(
        @Qualifier("${SLUG_PACKAGE}EntityManagerFactory") EntityManagerFactory emf
    ) {
        return buildTransactionManager(emf);
    }

    @Bean(name = "${SLUG_PACKAGE}Flyway", initMethod = "migrate")
    public Flyway ${SLUG_PACKAGE}Flyway(
        @Qualifier("${SLUG_PACKAGE}DataSource") DataSource ds
    ) {
        return buildFlyway(ds);
    }
}
EOF

ok "${SLUG_PASCAL}DataSourceConfig.java 생성 완료"
```

**주의**: heredoc 의 `\$` 는 bash 에서 `$` 로 보존 (Spring Boot 의 `@Value("${...}")` 문법). `${SLUG_UPPER}` 등은 bash 변수 확장.

- [ ] **Step 4: Run E2E test — PASS 확인**

```bash
bash tools/new-app/tests/test-e2e.sh
```
Expected: `PASS: E2E`, `PASS: TestappDataSourceConfig` 둘 다 출력.

- [ ] **Step 5: Commit**

```bash
git add tools/new-app/new-app.sh tools/new-app/tests/test-e2e.sh
git commit -m "feat(tools): new-app.sh Step 13.5 — <Slug>DataSourceConfig.java 자동 생성

Item 10b Task 3. 새 앱 추가 시 AbstractAppDataSourceConfig 상속하는
Config 클래스 자동 생성. E2E 테스트에서 파일 존재 + 상속 + 빈 이름
검증."
```

---

### Task 4: Spring bootRun 통합 테스트 추가 (E2E 확장)

**Files:**
- Modify: `tools/new-app/tests/test-e2e.sh`

**목적**: `new-app.sh` 로 앱 생성 후 실제로 Spring bootRun 시 Flyway migration 통과 + 부팅 성공 검증.

**제약**: E2E 는 Postgres 컨테이너 실제 필요. Docker daemon 실행 중이어야 함. `--provision-db` 필수.

- [ ] **Step 1: 테스트 확장 — Spring bootRun**

`tools/new-app/tests/test-e2e.sh` 에 `gradle compileJava` 뒤에 추가:

```bash
echo "=== Spring bootRun + testapp schema Flyway 검증 ==="

# Docker daemon 확인
if ! docker info >/dev/null 2>&1; then
    echo "SKIP: Docker daemon 없음 — bootRun 검증 스킵"
else
    # Postgres 기동
    docker compose -f infra/docker-compose.dev.yml up -d postgres
    # 준비 대기
    until docker exec spring-backend-template-postgres-dev pg_isready -U postgres -t 2 >/dev/null 2>&1; do sleep 1; done

    # testapp schema + role 생성 (new-app.sh --provision-db 우회 — DATABASE_URL 이미 테스트 중)
    export DATABASE_URL="postgresql://postgres:dev@localhost:5433/postgres"
    export APP_SLUG=testapp
    export APP_ROLE=testapp_app
    export APP_PASSWORD=testpass123

    psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 \
        -v app_slug=testapp -v app_role=testapp_app -v app_password=testpass123 \
        -f infra/scripts/init-app-schema.sql > /dev/null

    # .env 의 TESTAPP_DB_* 를 실제 값으로 업데이트
    sed -i.bak "s|^TESTAPP_DB_URL=.*$|TESTAPP_DB_URL=jdbc:postgresql://localhost:5433/postgres?currentSchema=testapp|" .env
    sed -i.bak "s|^TESTAPP_DB_USER=.*$|TESTAPP_DB_USER=testapp_app|" .env
    sed -i.bak "s|^TESTAPP_DB_PASSWORD=.*$|TESTAPP_DB_PASSWORD=testpass123|" .env
    rm -f .env.bak

    # JWT_SECRET placeholder 도 실제 값으로 (길이 32+)
    sed -i.bak 's|^JWT_SECRET=.*$|JWT_SECRET=local-test-secret-32-characters-minimum-abc|' .env
    rm -f .env.bak

    # bootRun (백그라운드) — 부팅 성공 시 Tomcat 메시지
    set -a; source .env; set +a
    timeout 120 ./gradlew :bootstrap:bootRun --no-daemon > /tmp/bootrun-e2e.log 2>&1 &
    BOOT_PID=$!

    # 최대 90초 대기하며 "Started FactoryApplication" 또는 "Application run failed" 탐지
    ELAPSED=0
    while [ $ELAPSED -lt 90 ]; do
        if grep -q "Started FactoryApplication" /tmp/bootrun-e2e.log 2>/dev/null; then
            break
        fi
        if grep -q "Application run failed" /tmp/bootrun-e2e.log 2>/dev/null; then
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done

    # 종료
    kill -TERM $BOOT_PID 2>/dev/null
    wait $BOOT_PID 2>/dev/null

    # 검증
    if grep -q "Started FactoryApplication" /tmp/bootrun-e2e.log; then
        echo "PASS: bootRun — Started FactoryApplication"
    else
        echo "FAIL: bootRun 기동 실패"
        grep -E "ERROR|Application run failed|Exception" /tmp/bootrun-e2e.log | head -5
        exit 1
    fi

    # testapp schema 에 Flyway migration 실행됐는지 확인
    TABLES=$(psql "${DATABASE_URL}" -tAc "SELECT tablename FROM pg_tables WHERE schemaname='testapp';" | wc -l)
    if [ "${TABLES}" -gt 0 ]; then
        echo "PASS: testapp schema 에 ${TABLES} 개 테이블 생성됨"
    else
        echo "FAIL: testapp schema 에 테이블 없음"
        exit 1
    fi

    # Cleanup
    psql "${DATABASE_URL}" -c "DROP SCHEMA testapp CASCADE; DROP ROLE testapp_app;" > /dev/null 2>&1
    docker compose -f infra/docker-compose.dev.yml down -v > /dev/null 2>&1
    rm -f /tmp/bootrun-e2e.log
fi
```

- [ ] **Step 2: Run E2E — bootRun PASS 확인**

```bash
bash tools/new-app/tests/test-e2e.sh
```
Expected: `PASS: bootRun — Started FactoryApplication` + `PASS: testapp schema 에 N 개 테이블 생성됨`.

**실패 시 분석**:
1. Flyway migration (`db/migration/testapp/V001~V006`) 가 실행됐는지 로그 확인
2. `TestappDataSourceConfig` 이 Spring context 에 등록됐는지
3. Hibernate hbm2ddl.auto=validate 가 테이블 구조 미스매치로 fail 하는지

- [ ] **Step 3: Commit**

```bash
git add tools/new-app/tests/test-e2e.sh
git commit -m "test(tools): new-app.sh E2E — Spring bootRun + Flyway 통합 검증

Item 10b Task 4. testapp schema 에 Flyway migration 실제 실행 +
Started FactoryApplication 로그 감지. Docker daemon 없으면 SKIP."
```

---

### Task 5: 문서 최종 갱신 + backlog archive

**Files:**
- Modify: `docs/guides/onboarding.md` (§5 Config 자동 생성 언급)
- Modify: `docs/architecture.md` (multi-DataSource 흐름 추가)
- Modify: `docs/conventions/decisions-infra.md` (I-08 신규 결정 추가 가능)
- Modify: `docs/conventions/module-dependencies.md` (common-persistence 에 AbstractAppDataSourceConfig 언급)
- Modify: `docs/backlog.md` (Item 10b archive)

- [ ] **Step 1: onboarding.md §5 업데이트**

기존:
```
1단계 — 코드 scaffolding (자동)
- apps/app-gymlog/ 모듈 생성 (build.gradle, HealthController, AuthController 예시)
- ...
```

수정 (추가):
```
- apps/app-gymlog/config/GymlogDataSourceConfig.java 자동 생성 (multi-DataSource wiring, Item 10b)
```

- [ ] **Step 2: architecture.md — multi-DataSource 섹션 추가**

`## 호스팅 구성` 섹션 앞에 신설:

```markdown
## Multi-DataSource Wiring

Template 은 앱별 독립 DataSource 패턴을 제공 (Item 10b). 각 앱이 자기 schema 에 붙는 DataSource / EntityManagerFactory / TransactionManager / Flyway 빈을 소유.

```
common-persistence/AbstractAppDataSourceConfig (abstract)
         ▲
         │ extends
         │
apps/app-<slug>/config/<Slug>DataSourceConfig
  @Bean <slug>DataSource (HikariCP)
  @Bean <slug>EntityManagerFactory (scan core + apps.<slug>)
  @Bean <slug>TransactionManager
  @Bean <slug>Flyway (db/migration/<slug>)
```

새 앱 추가 시 `new-app.sh` 가 Config 클래스 자동 생성. 상세:
[`conventions/decisions-infra.md I-08`](./conventions/decisions-infra.md).
```

- [ ] **Step 3: decisions-infra.md — I-08 추가**

기존 I-07 뒤에:

```markdown
## 결정 I-08. Multi-DataSource — 앱 모듈 자기 제공 패턴

- **status**: `provisioned` (Item 10b 구현 완료)
- **결정일**: 2026-04-19
- **결정**: 각 앱 모듈이 `AbstractAppDataSourceConfig` 를 extends 한 `<Slug>DataSourceConfig` 를 소유. Template 은 abstract 만 제공.
- **근거**:
  - philosophy 결정 3 (core-api/impl 분리) 정신 일치 — 앱이 자기 infra 책임
  - 파생 레포가 template bootstrap 수정 불필요 → cherry-pick 충돌 회피
  - `new-app.sh` 자동 생성으로 boilerplate 부담 제거
- **대안**:
  - Bootstrap 중앙 집중 (yml map) — 파생 레포가 template 수정해야 함
  - AbstractRoutingDataSource 런타임 분기 — Phase 0 에 과잉, 복잡도 ↑
- **Trade-off**:
  - 앱 당 Config 파일 1개 (자동 생성이라 실제 부담 0)
  - 같은 Repository 가 여러 EMF 에 scan → Spring Data JPA 의 bean name 구분 의존
- **재검토 트리거**:
  - DataSource 수 > 10 (bean context 부하)
  - Hot-swap DataSource 필요 시점 (AbstractRoutingDataSource 재고)
- **관련 문서**:
  - `../infrastructure.md §4` (multi-DataSource 흐름)
  - `common/common-persistence/` (abstract 구현)
  - `tools/new-app/new-app.sh` (Config 자동 생성)
```

재검토 트리거 요약 표에도 추가:
```
| DataSource 수 > 10 | I-08 multi-DS | AbstractRoutingDataSource 재고 |
```

- [ ] **Step 4: module-dependencies.md — common-persistence 역할 업데이트**

기존 `common-querydsl` 소개 섹션이 있으면 `common-persistence` 로 rename + 역할 확장 명시 (DataSource abstract 포함).

- [ ] **Step 5: backlog.md 업데이트**

- 대기 DX 섹션의 `Item 10b — Multi-DataSource wiring` 항목 제거
- archive 섹션에 추가:
  ```
  - [x] Item 10b — Multi-DataSource wiring (완료일: 2026-04-19, merge: TBD)
  ```
  (merge hash 는 머지 후 갱신)

- [ ] **Step 6: docs-check 통과 확인**

```bash
./tools/docs-check/docs-contract-test.sh
```
Expected: 3/3 PASS.

C1 / C2 / C3 이 common-persistence 이름 변경 때문에 실패할 가능성 있음 — 로컬에서 재확인 + exclusions.conf 조정.

- [ ] **Step 7: 전체 build + E2E 최종 재확인**

```bash
./gradlew clean build --no-daemon 2>&1 | tail -5
bash tools/docs-check/tests/test-docs-check.sh
bash tools/new-app/tests/test-e2e.sh
```
3개 전부 PASS 필요.

- [ ] **Step 8: Commit**

```bash
git add docs/
git commit -m "docs: Item 10b 완료 반영 — multi-DS 아키텍처 + decisions-infra I-08 + backlog archive"
```

---

## 완료 기준 (DoD)

- [ ] Task 1 (rename) 완료 — 기존 테스트 전부 통과
- [ ] Task 2 (AbstractAppDataSourceConfig) 완료 — 단위 테스트 PASS
- [ ] Task 3 (new-app.sh 확장) 완료 — Config 자동 생성 + E2E PASS
- [ ] Task 4 (bootRun 통합 테스트) 완료 — testapp schema migration 검증
- [ ] Task 5 (문서 갱신) 완료 — onboarding / architecture / decisions-infra / backlog 갱신
- [ ] `./gradlew build` → BUILD SUCCESSFUL
- [ ] `./tools/docs-check/docs-contract-test.sh` → 3/3 PASS
- [ ] `bash tools/new-app/tests/test-e2e.sh` → 전부 PASS
- [ ] Feature branch 머지 + main push + backlog archive 에 merge hash 기록

---

## 위험 요소

| 위험 | 영향 | 완화 |
|---|---|---|
| Rename 누락 참조 | 빌드 실패 | ArchUnit + Gradle dependency resolve 로 즉시 감지 |
| `@EnableJpaRepositories` 가 bootstrap 단일 DataSource 와 충돌 | Repository 빈 ambiguous | concrete Config 의 `entityManagerFactoryRef` 필수 명시 — Task 3 자동 생성 코드에 포함 |
| Hibernate `hbm2ddl.auto=validate` 가 schema 미존재 fail | 부팅 실패 | Flyway 가 migrate 먼저 실행하도록 `@Bean(initMethod = "migrate")` + initialization order |
| Flyway init order | Flyway 가 EMF 보다 늦게 실행 | `@DependsOn` 으로 EMF 가 Flyway 후에 생성되도록 concrete 에 명시 필요할 수도 — Task 4 bootRun 결과 보고 조정 |
| Docker daemon 없이 Task 2/4 실행 | 테스트 실패 | Docker 상태 확인 후 실행. 없으면 SKIP 처리 |
| Testcontainers 가 Task 2 단위 테스트에서 느림 | 테스트 시간 ↑ | Task 4 e2e 와 통합 고려 (Task 2 는 abstract 검증, Task 4 는 실제 부팅) |
| `@Bean` 이름 override 방식 | abstract method vs concrete @Bean 매핑 혼란 | build* helper 패턴 확정 — design spec §5 반영 |

---

## 진행 추적

- [ ] Task 1: common-querydsl → common-persistence rename
- [ ] Task 2: AbstractAppDataSourceConfig + 단위 테스트
- [ ] Task 3: new-app.sh 확장 — Config 자동 생성
- [ ] Task 4: E2E bootRun + Flyway 통합 검증
- [ ] Task 5: 문서 갱신 + backlog archive
- [ ] Final: main merge + push + backlog merge hash 기록
