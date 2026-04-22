# Item 10 — 앱 프로비저닝 통합 스크립트 (`new-app.sh` 확장)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `./tools/new-app/new-app.sh <slug>` 한 번 실행으로 **2단계 setup 까지 자동화** — 현재 "1단계 코드 scaffolding" 만 자동인 것을 "2단계 환경 setup (`.env` 주입, schema 생성 등)" 까지 포함.

**Architecture:** 기존 `new-app.sh` (586줄 bash) 를 **확장** (신설 아님). Step 10 의 수동 안내 중 자동 가능한 항목들을 실제 자동 수행 Step 으로 전환. Postgres schema 자동 생성은 `--provision-db` opt-in 플래그. multi-DataSource wiring 은 현재 bootstrap 구조가 미완이므로 Task 4 에서 조사 후 범위 판단.

**Tech Stack:** bash 4+, `sed`, `psql` (opt-in), Spring Boot 3.3, Gradle 8

---

## 메타

- **작성일**: 2026-04-19
- **선행 완료**:
  - Item 9 v2 — 인프라/사용법 문서 정비 (`ac5d66d`)
  - Backlog Item 10 scope 상세화 (user 입력 반영, `ac5d66d`)
- **연관 backlog 항목** (완료 시 archive):
  - `[DX] Item 10 — 앱 프로비저닝 통합 스크립트 ... slug 입력만으로 .env 자동 주입 ...`
- **후행 예약**:
  - Item Ops-1 — 운영 배포 묶음 (secrets/CF Tunnel/Jenkins 등)
  - Item 11 — Documentation contract test
  - (발견 시) Multi-DataSource wiring Item — Task 4 결론에 따라 별도 Item 분리 가능
- **예상 작업량**: 3~5 시간
- **결과물**:
  - 수정: `tools/new-app/new-app.sh` (Step 10 대체 + Step 11~14 신설)
  - 갱신: `docs/guides/onboarding.md` §5 (자동화 반영)
  - 갱신: `docs/backlog.md` (Item 10 항목 archive)
  - (조건부) 신설: `tools/new-app/tests/` — bats 또는 shell 테스트

---

## 1. Context — 왜 이 Item 인가

### 1.1 현재 상태 (Item 9 v2 dogfooding 에서 확인)

`new-app.sh` 는 **1단계 (코드 scaffolding) 만 자동**, **2단계 (환경 setup) 는 수동**:

| 단계 | 작업 | 현재 |
|---|---|---|
| 1 | Java 모듈 디렉토리/파일 생성 | ✅ 자동 |
| 1 | `settings.gradle` / `bootstrap/build.gradle` 수정 | ✅ 자동 |
| 2 | Postgres schema 생성 | ❌ 수동 (psql 명령 안내) |
| 2 | `.env` 에 `{SLUG_UPPER}_DB_URL/USER/PASSWORD` 추가 | ❌ 수동 |
| 2 | `.env` 에 `APP_STORAGE_MINIO_BUCKETS_<N>={slug}-uploads` 추가 | ❌ 수동 |
| 2 | `.env` 에 `APP_CREDENTIALS_{SLUG_UPPER}_*` placeholder 추가 | ❌ 수동 |
| 2 | `application.yml` 에 DataSource 설정 추가 | ❌ 수동 — 현재 bootstrap 에 multi-DataSource 인프라 **미존재** |
| 2 | 도메인 테이블 작성 (V007+) | ❌ 수동 (의도적 유지 — 비즈니스 로직) |

### 1.2 이 Item 의 범위

**포함** (본 plan):
- `.env` 자동 주입 3종 (DB, bucket, credentials placeholder)
- Postgres schema 자동 생성 (`--provision-db` opt-in)
- Task 4 에서 DataSource wiring 현황 조사 후 **가능하면** 자동 반영, **아니면** 별도 Item 으로 분리 + 문서 갱신
- 테스트 (bash 스크립트를 temp dir 에서 실제 실행하여 결과 검증)
- `onboarding.md` / `backlog.md` 갱신

**제외** (별도 Item 또는 의도적 수동 유지):
- 도메인 테이블 작성 (`V007+`) — 비즈니스 로직이라 의도적 수동
- Cloudflare Tunnel DNS 등록 — Item Ops-1
- 새 앱 slug 의 GitHub Secrets 등록 — Item Ops-1

### 1.3 설계 원칙

1. **Idempotent** — 재실행해도 안전. `.env` 의 기존 라인은 수정 안 함 (중복 추가 방지).
2. **Opt-in 위험 작업** — psql 호출은 `--provision-db` 플래그로만.
3. **Fallback 안내** — 자동 주입 실패 시 기존 수동 안내 메시지 유지.
4. **TDD** — bash 테스트 (bats 또는 shell-based) 로 각 Task 검증.

---

## 2. File structure

### 2.1 수정 파일

```
tools/new-app/new-app.sh                       (586줄 → 약 750줄 예상)
  ├─ Step 1~9 (기존) — 변경 없음
  ├─ Step 10 (변경) — .env 파일 준비 (없으면 cp .env.example)
  ├─ Step 11 (신설) — DB 변수 자동 주입
  ├─ Step 12 (신설) — bucket 이름 자동 주입
  ├─ Step 13 (신설) — credentials placeholder 자동 주입
  ├─ Step 14 (신설, 조건부) — --provision-db 플래그 시 psql 호출
  ├─ Step 15 (신설, Task 4 결과 반영) — DataSource 자동 반영 or 수동 안내
  └─ Step 16 (변경) — 남은 수동 안내 (축소)

docs/guides/onboarding.md §5                   (자동화 확대 반영)
docs/backlog.md                                (Item 10 archive)
```

### 2.2 신설 파일

```
tools/new-app/tests/test-provision.bats        (bats 테스트; 없으면 shell 기반)
  또는
tools/new-app/tests/test-provision.sh          (simpler shell-based verifier)
```

### 2.3 참조 전용 (수정 없음)

```
infra/scripts/init-app-schema.sql              (Task 5 에서 psql 로 호출)
.env.example                                   (cp 대상)
bootstrap/src/main/resources/application-*.yml (Task 4 조사 대상)
```

---

## 3. Architectural decisions

### 3.1 `.env` 주입 방식 — **append** 만, 기존 라인 **불변**

bash 로 `.env` 수정 시 옵션:
- **A. 파일 끝에 append** (선택) — 이미 키가 있으면 skip. 구현 단순. 순서 비결정성 허용.
- B. sed 로 in-place edit — 기존 라인 수정 가능하나 `.env` 주석/포맷 깨질 위험.
- C. 별도 `.env.d/<slug>.env` 생성 — Spring Boot 가 기본 지원 안 함. 복잡도 증가.

**선택: A**. 이미 `grep -q '^{KEY}=' .env` 로 존재 확인 후 없을 때만 append.

### 3.2 bucket index (`APP_STORAGE_MINIO_BUCKETS_<N>`) 자동 계산

```bash
next_bucket_index() {
    local max
    max=$(grep -oE '^APP_STORAGE_MINIO_BUCKETS_[0-9]+=' .env 2>/dev/null \
          | grep -oE '[0-9]+' | sort -n | tail -1)
    echo $((${max:-(-1)} + 1))
}
```

결과: 없으면 0, 이미 0~2 있으면 3.

### 3.3 Schema 생성 — `--provision-db` opt-in

psql 호출은 network + credential 필요. 개발자가 DATABASE_URL env 를 준비한 경우만:

```bash
./tools/new-app/new-app.sh gymlog --provision-db
# DATABASE_URL 미설정 시 에러
```

`init-app-schema.sql` 을 `envsubst` 또는 `psql -v` 로 `APP_SLUG`, `APP_ROLE`, `APP_PASSWORD` 치환.

### 3.4 DataSource wiring — Task 4 에서 조사 후 결정

현재 `bootstrap/src/main/resources/application-*.yml` 에 **단일 DataSource** 만. 앱별 DataSource 는 아직 인프라 없음. 3 선택지:

- **3-a**. 본 Item 에서 함께 해결: yml 에 앱별 `spring.datasource.<slug>` 섹션 자동 추가 + Java config 자동 생성. **복잡도 높음** (2-3 시간).
- **3-b**. 별도 Item (`Item 10b — Multi-DataSource wiring`) 로 분리. 본 Item 은 `.env` 만 자동 주입.
- **3-c**. Spring Boot 의 `@ConfigurationProperties + @Qualifier` 패턴으로 app-<slug> 모듈이 자기 DataSource 빈을 제공하도록 — 이게 정석. 하지만 기존 apps 모듈 템플릿 수정 필요.

**판단 지연**: Task 4 시작 시 현재 bootstrap 상태 상세 조사 후 3-a/b/c 중 택. Plan 에서는 3 Task 자체를 "조사 + 범위 결정 + 구현 or 분리" 로 정의.

---

## 4. Tasks (TDD)

### Task 1: 환경 주입 헬퍼 함수 추가 (bash)

**Files:**
- Modify: `tools/new-app/new-app.sh` (Step 10 직전, 헬퍼 함수 섹션에 추가)

- [ ] **Step 1: Write failing test**

Create `tools/new-app/tests/test-provision.sh`:

```bash
#!/usr/bin/env bash
# 간단한 shell-based test (bats 없어도 실행 가능)
set -euo pipefail

TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# 테스트 1: inject_env_line — 새 라인 추가
source tools/new-app/new-app.sh --source-only || true  # 헬퍼만 로드 (구현 후 지원 추가)
cd "$TEST_DIR"
touch .env

inject_env_line "FOO_BAR" "value1"
grep -q "^FOO_BAR=value1$" .env || { echo "FAIL: inject_env_line new line"; exit 1; }

# 테스트 2: 기존 키 있으면 skip
inject_env_line "FOO_BAR" "value2"
count=$(grep -c "^FOO_BAR=" .env)
[ "$count" -eq 1 ] || { echo "FAIL: duplicate injection, count=$count"; exit 1; }

echo "PASS: Task 1 (inject_env_line)"
```

- [ ] **Step 2: Run test to verify fail**

Run: `bash tools/new-app/tests/test-provision.sh`
Expected: `--source-only` 미지원으로 실패 또는 함수 미존재로 실패.

- [ ] **Step 3: Implement helper functions in new-app.sh**

`tools/new-app/new-app.sh` 의 helper 섹션 (기존 `info`/`ok` 함수 근처) 에 추가:

```bash
# ─── helpers: .env 주입 ─────────────────────────────────────────────────────

# .env 에 키=값 추가. 이미 키가 있으면 skip. $1=KEY, $2=VALUE.
inject_env_line() {
    local key="$1"
    local value="$2"
    if [[ -z "${key}" ]]; then fail "inject_env_line: empty key"; fi
    if grep -qE "^${key}=" .env 2>/dev/null; then
        info "  skip: ${key} already in .env"
        return 0
    fi
    echo "${key}=${value}" >> .env
    ok "  add: ${key}"
}

# APP_STORAGE_MINIO_BUCKETS_<N> 의 다음 빈 N 반환.
next_bucket_index() {
    local max
    max=$(grep -oE '^APP_STORAGE_MINIO_BUCKETS_[0-9]+=' .env 2>/dev/null \
          | grep -oE '[0-9]+' | sort -n | tail -1)
    echo $((${max:--1} + 1))
}

# .env 존재 확인, 없으면 .env.example 복사. 없으면 .env.example 도 없으면 에러.
ensure_env_file() {
    if [[ -f .env ]]; then return 0; fi
    if [[ -f .env.example ]]; then
        cp .env.example .env
        info "  .env 를 .env.example 에서 복사"
    else
        fail ".env 및 .env.example 둘 다 없음. 최소 하나 필요."
    fi
}

# --source-only 플래그로 호출 시 함수만 로드 (테스트용)
if [[ "${1:-}" == "--source-only" ]]; then
    return 0 2>/dev/null || exit 0
fi
```

- [ ] **Step 4: Run test to verify pass**

Run: `bash tools/new-app/tests/test-provision.sh`
Expected: `PASS: Task 1 (inject_env_line)`

- [ ] **Step 5: Commit**

```bash
git add tools/new-app/new-app.sh tools/new-app/tests/test-provision.sh
git commit -m "feat(tools): new-app.sh 에 .env 주입 헬퍼 함수 추가"
```

---

### Task 2: Step 10 확장 — `.env` 파일 준비

**Files:**
- Modify: `tools/new-app/new-app.sh` (Step 10 교체)

- [ ] **Step 1: Write failing test**

`tools/new-app/tests/test-provision.sh` 에 추가:

```bash
# 테스트: .env 가 없으면 .env.example 에서 자동 생성
rm -f .env
echo "SPRING_PROFILES_ACTIVE=dev" > .env.example
ensure_env_file
[ -f .env ] || { echo "FAIL: ensure_env_file 생성 실패"; exit 1; }
grep -q "SPRING_PROFILES_ACTIVE=dev" .env || { echo "FAIL: .env.example 내용 미복사"; exit 1; }
echo "PASS: Task 2 (ensure_env_file)"
```

- [ ] **Step 2: Run test to verify fail or pass**

Run: `bash tools/new-app/tests/test-provision.sh`
이미 Task 1 구현에 `ensure_env_file` 포함됐으면 PASS — 그럼 Step 3 skip 하고 Step 5 로.

- [ ] **Step 3 (필요 시): Implement `ensure_env_file`**

Task 1 의 helper 섹션에 이미 포함. 재확인만.

- [ ] **Step 4: 기존 Step 10 교체**

`tools/new-app/new-app.sh` 의 Step 10 (`# ─── Step 10: 수동 작업 안내 ───`) 바로 **앞에** 신규 Step 10 추가:

```bash
# ─── Step 10: .env 파일 준비 ──────────────────────────────────────────────────
info "Step 10: .env 준비 중..."
ensure_env_file
ok ".env 준비 완료"
```

기존 Step 10 헤더는 `# ─── Step 16: 남은 수동 작업 안내` 로 개명 (Task 6 에서 처리).

- [ ] **Step 5: Commit**

```bash
git add tools/new-app/new-app.sh tools/new-app/tests/test-provision.sh
git commit -m "feat(tools): new-app.sh Step 10 에서 .env 자동 준비"
```

---

### Task 3: Step 11 — DB 변수 자동 주입

**Files:**
- Modify: `tools/new-app/new-app.sh`

- [ ] **Step 1: Write failing test**

```bash
# 테스트: DB 3 변수 자동 주입
cd "$TEST_DIR" && rm -f .env && touch .env
SLUG="gymlog"
SLUG_UPPER="GYMLOG"
SLUG_PACKAGE="gymlog"
SLUG_IDENT="gymlog"

# 아직 함수 없으므로 fail 예상
inject_db_vars "${SLUG_UPPER}" "${SLUG_IDENT}" "${SLUG_PACKAGE}" 2>/dev/null \
  || { echo "expected fail at this point"; }

# 구현 후:
# grep -q "^GYMLOG_DB_URL=" .env || fail "no GYMLOG_DB_URL"
# grep -q "^GYMLOG_DB_USER=gymlog_app$" .env || fail "no GYMLOG_DB_USER"
# grep -q "^GYMLOG_DB_PASSWORD=CHANGE_ME$" .env || fail "no GYMLOG_DB_PASSWORD"
echo "PASS: Task 3 placeholder (will be validated after implement)"
```

- [ ] **Step 2: Run test**

Run: `bash tools/new-app/tests/test-provision.sh`

- [ ] **Step 3: Implement `inject_db_vars`**

`tools/new-app/new-app.sh` helper 섹션에 추가:

```bash
# $1=SLUG_UPPER (예: GYMLOG), $2=SLUG_IDENT (schema 이름), $3=SLUG_PACKAGE (role 이름)
inject_db_vars() {
    local SLUG_UPPER="$1"
    local SLUG_IDENT="$2"
    local SLUG_PACKAGE="$3"
    inject_env_line "${SLUG_UPPER}_DB_URL" \
        "jdbc:postgresql://<host>:5432/postgres?currentSchema=${SLUG_IDENT}"
    inject_env_line "${SLUG_UPPER}_DB_USER" "${SLUG_PACKAGE}_app"
    inject_env_line "${SLUG_UPPER}_DB_PASSWORD" "CHANGE_ME"
}
```

- [ ] **Step 4: Add Step 11 to main flow**

`tools/new-app/new-app.sh` 에 Step 10 바로 뒤에:

```bash
# ─── Step 11: DB 변수 주입 ────────────────────────────────────────────────────
info "Step 11: .env 에 DB 변수 추가 중..."
inject_db_vars "${SLUG_UPPER}" "${SLUG_IDENT}" "${SLUG_PACKAGE}"
ok "DB 변수 주입 완료 (DB_URL 의 <host> 는 수동 교체 필요)"
```

- [ ] **Step 5: 테스트 확장 + 재실행**

test-provision.sh 의 Task 3 placeholder 부분에 실제 검증 추가:

```bash
inject_db_vars "GYMLOG" "gymlog" "gymlog"
grep -q "^GYMLOG_DB_URL=.*currentSchema=gymlog" .env || { echo "FAIL: DB_URL"; exit 1; }
grep -q "^GYMLOG_DB_USER=gymlog_app$" .env || { echo "FAIL: DB_USER"; exit 1; }
grep -q "^GYMLOG_DB_PASSWORD=CHANGE_ME$" .env || { echo "FAIL: DB_PASSWORD"; exit 1; }
echo "PASS: Task 3 (inject_db_vars)"
```

Run: `bash tools/new-app/tests/test-provision.sh`

- [ ] **Step 6: Commit**

```bash
git add tools/new-app/new-app.sh tools/new-app/tests/test-provision.sh
git commit -m "feat(tools): new-app.sh Step 11 에서 DB 변수 자동 주입"
```

---

### Task 4: Step 12 — Bucket 이름 자동 주입

**Files:**
- Modify: `tools/new-app/new-app.sh`

- [ ] **Step 1: Write failing test**

```bash
# 테스트: 기존 BUCKETS 없으면 _0, 있으면 다음 index
cd "$TEST_DIR" && rm -f .env && touch .env
inject_bucket "gymlog" "uploads"
grep -q "^APP_STORAGE_MINIO_BUCKETS_0=gymlog-uploads$" .env || { echo "FAIL: bucket index 0"; exit 1; }

inject_bucket "rny" "profiles"
grep -q "^APP_STORAGE_MINIO_BUCKETS_1=rny-profiles$" .env || { echo "FAIL: bucket index 1"; exit 1; }
echo "PASS: Task 4 (inject_bucket)"
```

- [ ] **Step 2: Run test (fail expected)**

Run: `bash tools/new-app/tests/test-provision.sh`

- [ ] **Step 3: Implement `inject_bucket`**

```bash
# $1=slug_ident, $2=category (uploads/receipts/avatars ...)
inject_bucket() {
    local slug="$1"
    local category="$2"
    local idx
    idx=$(next_bucket_index)
    inject_env_line "APP_STORAGE_MINIO_BUCKETS_${idx}" "${slug}-${category}"
}
```

- [ ] **Step 4: Add Step 12**

```bash
# ─── Step 12: Bucket 이름 주입 ────────────────────────────────────────────────
info "Step 12: .env 에 bucket 이름 추가 중..."
inject_bucket "${SLUG_IDENT}" "uploads"
ok "Bucket 이름 주입 완료 (Spring 재기동 시 BucketProvisioner 가 자동 생성)"
```

- [ ] **Step 5: Run test to verify pass**

- [ ] **Step 6: Commit**

```bash
git commit -am "feat(tools): new-app.sh Step 12 에서 bucket 이름 자동 주입"
```

---

### Task 5: Step 13 — Credentials placeholder 자동 주입

**Files:**
- Modify: `tools/new-app/new-app.sh`

- [ ] **Step 1: Write failing test**

```bash
cd "$TEST_DIR" && rm -f .env && touch .env
inject_credentials "GYMLOG"
grep -q "^APP_CREDENTIALS_GYMLOG_GOOGLE_CLIENT_IDS_0=CHANGE_ME$" .env || { echo "FAIL"; exit 1; }
grep -q "^APP_CREDENTIALS_GYMLOG_APPLE_BUNDLE_ID=com.example.gymlog$" .env || { echo "FAIL"; exit 1; }
echo "PASS: Task 5 (inject_credentials)"
```

- [ ] **Step 2: Run test (fail expected)**

- [ ] **Step 3: Implement**

```bash
# $1=SLUG_UPPER
inject_credentials() {
    local SLUG_UPPER="$1"
    local slug_lower
    slug_lower=$(echo "${SLUG_UPPER}" | tr '[:upper:]_' '[:lower:].')
    inject_env_line "APP_CREDENTIALS_${SLUG_UPPER}_GOOGLE_CLIENT_IDS_0" "CHANGE_ME"
    inject_env_line "APP_CREDENTIALS_${SLUG_UPPER}_GOOGLE_CLIENT_IDS_1" "CHANGE_ME"
    inject_env_line "APP_CREDENTIALS_${SLUG_UPPER}_APPLE_BUNDLE_ID" "com.example.${slug_lower}"
}
```

- [ ] **Step 4: Add Step 13**

```bash
# ─── Step 13: Credentials placeholder 주입 ───────────────────────────────────
info "Step 13: .env 에 credentials placeholder 추가 중..."
inject_credentials "${SLUG_UPPER}"
ok "Credentials placeholder 주입 완료 (실제 발급: docs/social-auth-setup.md)"
```

- [ ] **Step 5: Run test + Commit**

```bash
git commit -am "feat(tools): new-app.sh Step 13 에서 credentials placeholder 주입"
```

---

### Task 6: Step 14 — `--provision-db` 플래그로 Postgres schema 생성

**Files:**
- Modify: `tools/new-app/new-app.sh`
- Reference: `infra/scripts/init-app-schema.sql`

- [ ] **Step 1: Argument parsing 추가**

`tools/new-app/new-app.sh` 의 Step 1 (slug 검증) 앞에:

```bash
PROVISION_DB=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --provision-db) PROVISION_DB=1; shift ;;
        --source-only)  return 0 2>/dev/null || exit 0 ;;
        -*)             fail "unknown flag: $1" ;;
        *)              SLUG="${SLUG:-$1}"; shift ;;
    esac
done
```

- [ ] **Step 2: Implement `provision_db`**

```bash
# $1=SLUG_IDENT, $2=SLUG_PACKAGE (role prefix)
provision_db() {
    local SLUG_IDENT="$1"
    local SLUG_PACKAGE="$2"
    if [[ -z "${DATABASE_URL:-}" ]]; then
        fail "--provision-db 사용 시 DATABASE_URL 환경변수 필요 (예: export DATABASE_URL='postgresql://...')"
    fi
    if ! command -v psql >/dev/null 2>&1; then
        fail "psql 설치 필요 (brew install libpq 또는 postgresql)"
    fi

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
        -f infra/scripts/init-app-schema.sql

    # .env 의 _DB_PASSWORD 를 생성된 값으로 교체 (기존 CHANGE_ME 를 sed 로 대체)
    if grep -q "^${SLUG_UPPER}_DB_PASSWORD=CHANGE_ME$" .env; then
        sed -i.bak "s|^${SLUG_UPPER}_DB_PASSWORD=CHANGE_ME$|${SLUG_UPPER}_DB_PASSWORD=${password}|" .env
        rm -f .env.bak
        ok "  .env 의 ${SLUG_UPPER}_DB_PASSWORD 를 생성된 값으로 갱신"
    fi
}
```

- [ ] **Step 3: Add Step 14 (조건부)**

```bash
# ─── Step 14: Postgres schema 자동 생성 (--provision-db 지정 시) ──────────────
if [[ "${PROVISION_DB}" -eq 1 ]]; then
    info "Step 14: --provision-db — schema 생성 중..."
    provision_db "${SLUG_IDENT}" "${SLUG_PACKAGE}"
    ok "schema + role 생성 완료"
else
    info "Step 14: --provision-db 미지정 — schema 생성 skip (수동 안내 참조)"
fi
```

- [ ] **Step 4: Manual test (Docker Postgres 로)**

Local docker postgres 띄우고 실제 테스트:
```bash
docker compose -f infra/docker-compose.dev.yml up -d postgres
export DATABASE_URL="postgresql://postgres:dev@localhost:5433/postgres"
# 테스트용 디렉토리에서:
./tools/new-app/new-app.sh testapp --provision-db
psql "${DATABASE_URL}" -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name='testapp';"
# 기대: 1 row
```

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(tools): new-app.sh --provision-db 플래그로 schema 자동 생성"
```

---

### Task 7: Step 15 — DataSource wiring 조사 + 구현 or 분리 결정

**Files:**
- Investigate: `bootstrap/src/main/resources/application*.yml`
- Investigate: `bootstrap/src/main/java/com/factory/bootstrap/`
- Modify (조건부): `tools/new-app/new-app.sh` 또는 위 파일들

- [ ] **Step 1: 현황 조사**

```bash
find bootstrap/src/main -name "*.java" | xargs grep -l "DataSource" 2>/dev/null
grep -A 5 "datasource:" bootstrap/src/main/resources/application*.yml
grep -rE "spring\.datasource" apps/ 2>/dev/null || echo "apps 에 DataSource 없음"
```

- [ ] **Step 2: 결과 판단**

3 선택지 중 택 (§3.4 참조):

- **3-a. 본 Item 에서 구현**: bootstrap 에 multi-DataSource 인프라 (Java config + yml) 를 new-app.sh 가 자동 추가.
- **3-b. 별도 Item 분리**: "Item 10b — Multi-DataSource wiring" 로 분리. 본 plan 은 `.env` 주입까지만.
- **3-c. 앱 모듈에 DataSource 빈 자체 포함**: 각 앱이 자기 DataSource 제공. 기존 모듈 template 수정 필요.

**추천 기본값**: 3-b (별도 Item). 이유:
- Multi-DataSource 는 Spring 전문 영역 — 디자인 제대로 해야 함 (브레인스토밍 필요)
- 본 Item 의 가치 (env 자동 주입) 는 독립적으로 유효
- 분리해야 리뷰/revert 단위 깔끔

- [ ] **Step 3 (3-b 선택 시): backlog 에 Item 10b 추가**

```bash
# docs/backlog.md 의 DX 섹션에 추가
# - [ ] [DX] Item 10b — Multi-DataSource wiring (bootstrap 에 앱별 DataSource 빈 + yml 구조)
#   — Item 10 에서 분리 (2026-04-19)
```

- [ ] **Step 4: Step 15 내용 결정**

3-b 면 Step 15 는 "남은 수동 안내" 에 통합 (Task 8).
3-a 면 별도 구현 Task 추가 필요 (plan 확장).

- [ ] **Step 5: Commit (Task 7 조사 결과)**

```bash
git commit -am "docs: Item 10 Task 7 조사 — multi-DataSource 는 Item 10b 로 분리"
```

---

### Task 8: Step 16 — 남은 수동 작업 안내 축소

**Files:**
- Modify: `tools/new-app/new-app.sh` (기존 Step 10 대체)

- [ ] **Step 1: 기존 Step 10 의 8개 echo 항목 중 **자동화된 것 제거****

남길 항목:
- (5) 도메인 테이블 V007+ 작성 — 의도적 수동
- (7) Grafana 앱 필터 설정 — Item Ops-1
- (8) 커밋 제안

제거 항목:
- (1) schema 생성 — `--provision-db` 로 자동화됨
- (2) DB 변수 추가 — Step 11 자동화
- (3) credentials — Step 13 자동화
- (4) application.yml DataSource — Task 7 결과에 따라 (Item 10b 로 분리 시 유지)
- (6) MinIO bucket — Step 12 자동화

- [ ] **Step 2: 신규 Step 16 작성**

```bash
# ─── Step 16: 남은 수동 작업 안내 ──────────────────────────────────────────────
echo ""
echo "=========================================================="
echo "  apps/app-${SLUG} 생성 완료! ✅"
echo "=========================================================="
echo ""
echo "자동 수행됨:"
echo "  ✅ Java 모듈 scaffolding (Step 1~9)"
echo "  ✅ .env 에 DB / bucket / credentials placeholder 추가 (Step 10~13)"
if [[ "${PROVISION_DB}" -eq 1 ]]; then
    echo "  ✅ Postgres schema + role 생성 (Step 14, --provision-db)"
else
    echo "  ⏭  Postgres schema 생성 skip (--provision-db 미지정)"
fi
echo ""
echo "남은 수동 작업:"
echo ""
if [[ "${PROVISION_DB}" -ne 1 ]]; then
    echo "1. Postgres schema 수동 생성 (또는 --provision-db 재실행):"
    echo "   export APP_SLUG=${SLUG_IDENT} APP_ROLE=${SLUG_PACKAGE}_app APP_PASSWORD='강력한비번'"
    echo "   psql \"\$DATABASE_URL\" -f infra/scripts/init-app-schema.sql"
    echo ""
fi
echo "2. .env 의 placeholder 값 실제 값으로 교체:"
echo "   - ${SLUG_UPPER}_DB_URL 의 <host> (Supabase pooler 호스트 등)"
echo "   - APP_CREDENTIALS_${SLUG_UPPER}_GOOGLE_CLIENT_IDS_0/1, _APPLE_BUNDLE_ID"
echo "   → 발급 방법: docs/social-auth-setup.md"
echo ""
echo "3. bootstrap 의 DataSource 설정에 ${SLUG_UPPER} 추가 (Item 10b 예정):"
echo "   현재는 application-dev.yml / application-prod.yml 에 수동 추가 필요"
echo ""
echo "4. 도메인 테이블 작성:"
echo "   ${MIGRATION_DIR}/V007__init_domain.sql"
echo ""
echo "5. 커밋:"
echo "   feat(apps): scaffold app-${SLUG}"
echo ""
```

- [ ] **Step 3: Commit**

```bash
git commit -am "feat(tools): new-app.sh Step 16 수동 안내 축소 + 자동화 반영"
```

---

### Task 9: 통합 E2E 테스트

**Files:**
- Use: `tools/new-app/tests/test-provision.sh` + temp clone

- [ ] **Step 1: End-to-end test script**

`tools/new-app/tests/test-e2e.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

TEST_DIR=$(mktemp -d)
REPO=$(pwd)
trap "rm -rf $TEST_DIR" EXIT

# 신규 디렉토리에 현재 작업 트리 복사 (git clone 대신 rsync)
rsync -a --exclude=build --exclude=.gradle --exclude=node_modules \
    "${REPO}/" "${TEST_DIR}/"

cd "${TEST_DIR}"
cp .env.example .env

# Execute
./tools/new-app/new-app.sh testapp

# Assertions
echo "=== .env 검증 ==="
grep -q "^TESTAPP_DB_URL=.*currentSchema=testapp" .env || { echo "FAIL: DB_URL"; exit 1; }
grep -q "^TESTAPP_DB_USER=testapp_app$" .env || { echo "FAIL: DB_USER"; exit 1; }
grep -q "^APP_STORAGE_MINIO_BUCKETS_[0-9]\+=testapp-uploads$" .env || { echo "FAIL: bucket"; exit 1; }
grep -q "^APP_CREDENTIALS_TESTAPP_APPLE_BUNDLE_ID=com.example.testapp$" .env || { echo "FAIL: credentials"; exit 1; }

echo "=== settings.gradle 검증 ==="
grep -q ":apps:app-testapp" settings.gradle || { echo "FAIL: settings.gradle"; exit 1; }

echo "=== gradle build 통과 검증 ==="
./gradlew :apps:app-testapp:compileJava --no-daemon -q || { echo "FAIL: compile"; exit 1; }

echo "PASS: E2E"
```

- [ ] **Step 2: Run**

```bash
bash tools/new-app/tests/test-e2e.sh
```

- [ ] **Step 3: Commit**

```bash
git add tools/new-app/tests/test-e2e.sh
git commit -m "test(tools): new-app.sh E2E 테스트 추가"
```

---

### Task 10: 문서 갱신

**Files:**
- Modify: `docs/guides/onboarding.md` §5
- Modify: `docs/backlog.md`

- [ ] **Step 1: onboarding.md §5 갱신**

기존 "2단계 환경 setup (수동)" 섹션을 **"자동 vs 수동 비교 표"** 로 교체:

```markdown
### 1단계 — 코드 scaffolding (자동)
... (기존 유지)

### 2단계 — 환경 setup (대부분 자동)

`./tools/new-app/new-app.sh gymlog` 가 자동 수행:
- ✅ `.env` 에 `GYMLOG_DB_URL/USER/PASSWORD` placeholder 추가
- ✅ `.env` 에 `APP_STORAGE_MINIO_BUCKETS_<N>=gymlog-uploads` 추가 (BucketProvisioner 가 Spring 기동 시 실제 생성)
- ✅ `.env` 에 `APP_CREDENTIALS_GYMLOG_*` placeholder 추가

Opt-in 자동 수행 (`--provision-db` 플래그):
- ✅ Postgres 에 `gymlog` schema + role 생성 (DATABASE_URL 환경변수 필요)

여전히 수동:
- DB_URL 의 `<host>` 실제 값으로 교체
- GOOGLE_CLIENT_IDS / APPLE_BUNDLE_ID 실제 값 발급 (`docs/social-auth-setup.md`)
- bootstrap DataSource 설정 추가 (Item 10b 예정)
- 도메인 테이블 작성 (V007+, 비즈니스 로직)
```

- [ ] **Step 2: backlog.md 갱신**

Item 10 항목을 "완료 (archive)" 섹션으로 이동:

```markdown
## 완료 (archive, 지난 2개월)
- [x] Item 10 — 앱 프로비저닝 통합 스크립트 (완료일: 2026-04-19, commit: <hash>)
```

Item 10b 신규 추가 (Task 7 결정 시):
```markdown
- [ ] [DX] Item 10b — Multi-DataSource wiring (bootstrap 에 앱별 DataSource 빈 + yml 구조) — Item 10 에서 분리 (2026-04-19)
```

- [ ] **Step 3: Commit**

```bash
git add docs/guides/onboarding.md docs/backlog.md
git commit -m "docs: Item 10 완료 반영 — onboarding §5 자동화 갱신 + backlog archive"
```

---

## 5. 완료 기준 (DoD)

- [ ] Task 1~9 전부 commit, 각자 테스트 통과
- [ ] Task 7 에서 3-a / 3-b / 3-c 선택 기록 완료
- [ ] E2E 테스트 (Task 9) PASS
- [ ] `onboarding.md §5` 갱신됨
- [ ] backlog `Item 10` archive, `Item 10b` (3-b 선택 시) 추가
- [ ] Feature branch → main 머지 + push

---

## 6. 위험 요소

| 위험 | 영향 | 완화 |
|---|---|---|
| bash 스크립트 plumbing 오류 (sed/grep 에지) | .env 손상 | `.env` 수정 전 `.env.bak` 자동 백업. Task 2 에서 `ensure_env_file` 후 검증 |
| `--provision-db` 의 psql 호출 실패 | 미성공 — DB state 애매 | `ON_ERROR_STOP=1` + transaction 보장 (init-app-schema.sql 이 이미 BEGIN/COMMIT 사용 중이면 유지) |
| DataSource wiring 복잡도 과소평가 | 본 Item scope creep | Task 7 에서 조사 후 Item 10b 로 분리 (3-b) 기본값 |
| Spring relaxed binding 오작동 (env → properties) | bucket list 미로드 | E2E test 에서 실제 Spring 기동 확인 (Task 9 확장 — 선택) |
| bats 미설치 환경 | 테스트 실행 불가 | shell-based test (bats 없이) 사용 — `tools/new-app/tests/test-provision.sh` |

---

## 7. 진행 추적

- [x] Task 1: 헬퍼 함수
- [x] Task 2: Step 10 (.env 준비)
- [x] Task 3: Step 11 (DB 변수)
- [x] Task 4: Step 12 (bucket)
- [x] Task 5: Step 13 (credentials)
- [x] Task 6: Step 14 (--provision-db)
- [x] Task 7: DataSource 조사 + 분리 결정 → **3-b 채택** (Item 10b 로 분리, backlog 추가). Step 15 는 Task 8 안내 메시지에 통합.
- [ ] Task 8: Step 16 (안내 축소)
- [ ] Task 9: E2E 테스트
- [ ] Task 10: 문서 갱신
- [ ] 최종 merge to main + push
