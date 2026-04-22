# Item 11 — Documentation Contract Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문서의 claim (파일 경로 / 환경변수 이름 / 폐기된 심볼 부재) 이 실제 artifact 와 일치하는지 CI 에서 자동 검증하여 문서 drift 를 예방.

**Architecture:** 단일 bash runner (`tools/docs-check/docs-contract-test.sh`) 에 3 개 체크 함수. Exclusions 는 `exclusions.conf` 로 분리. GitHub Actions 에서 PR + push-to-main 트리거. 외부 도구 의존 없음 (grep/find 만 사용).

**Tech Stack:** bash 4+, GNU grep (ripgrep 선택적), GitHub Actions `ubuntu-latest`

---

## 메타

- **작성일**: 2026-04-19
- **선행 완료**:
  - Item 9 v2 — 인프라/사용법 문서 정비 (`fe8fe56` + 후속)
  - Item 10 — 앱 프로비저닝 통합 스크립트 (`ff4bcbb`)
- **연관 backlog 항목** (완료 시 archive):
  - `[DX] Item 11 — Documentation contract test (문서 claim ↔ 실제 artifact 자동 검증 CI)`
- **후행 예약**:
  - Item 10b — Multi-DataSource wiring
  - Item Ops-1 — 운영 배포 묶음
  - 미래: inventory 기계 추출 파일 (`.inventory.yml`) — Item 11 의 로직을 기반으로 확장 가능
- **예상 작업량**: 2~3 시간
- **결과물**:
  - 신설: `tools/docs-check/docs-contract-test.sh`, `exclusions.conf`, `tests/test-docs-check.sh`
  - 신설: `.github/workflows/docs-check.yml`
  - 수정: `docs/conventions/git-workflow.md` (문서 검증 자동화 섹션)
  - 수정: `docs/backlog.md` (Item 11 archive)

---

## 1. Context — 왜 이 Item 인가

### 1.1 Item 9 v2 에서 드러난 문제

Phase D 역방향 검증 (수동) 에서 60+ claim 점검 후 **FAIL 1 건** 발견 (storage.md → infrastructure 링크 누락). 수동 검증은 쉽게 잊힘. Item 10 후에도 추가 linkage 변경이 생겼고, 앞으로도 발생 예정.

**자동화하지 않으면**: 파생 레포가 생길 때마다 동일 drift 발견이 반복됨. 각 레포가 자기 drift 를 해결해야 함.

### 1.2 스코프 — MVP 3 개 체크

드리프트 유형은 많지만 **효용 높고 구현 간단한 3 개만** 먼저 자동화:

| # | 체크 | 대상 | 실패 조건 |
|---|---|---|---|
| C1 | **폐기 심볼 블랙리스트** | `docs/**/*.md`, `README.md`, 모듈 READMEs | Item 7 에서 rename 된 심볼 (`UserCredentials`, `TokenPair`, `PushResult`, `verifyReceipt`, `toCredentials`) 이 문서에 여전히 참조됨 |
| C2 | **Markdown 파일 경로 링크** | `[text](./path.md)` 스타일 링크 | 링크된 상대 경로 파일이 실제로 존재 안 함 |
| C3 | **환경변수 이름 일관성** | `.env.example`, `application-*.yml` | 문서에 언급된 env var (`APP_*` / `SPRING_*` / `JWT_*` / `DB_*` 등 prefix) 가 `.env.example` 또는 yml 어디에도 없음 |

**제외** (Item 11 MVP 스코프 밖):
- 클래스/메서드 존재 검증 (Java grep 복잡도 ↑)
- 문서 간 양방향 링크 매트릭스 (config 필요, 설계 시간 ↑)
- 버전 매트릭스 (CHANGELOG vs 실제 릴리스)
- 외부 URL (HTTP) validity — 인터넷 의존
- Inventory 기계 추출 파일 생성

### 1.3 설계 원칙

1. **의존성 0** — bash + POSIX grep/find 만. 러너에 따로 도구 설치 불필요
2. **Exclusions 명시** — false positive 는 `exclusions.conf` 에 등록 (이유 주석 필수)
3. **개발자 친화적 에러** — 실패 시 파일:라인 + 기대값/실제값 출력
4. **CI 통합** — PR + push-to-main 에서 실행. 실패 시 block
5. **Idempotent** — 여러 번 실행해도 같은 결과

---

## 2. File structure

### 2.1 신설 파일

```
tools/docs-check/
├── docs-contract-test.sh        (main runner, ~200 줄 예상)
├── exclusions.conf              (false-positive 화이트리스트)
└── tests/
    └── test-docs-check.sh       (meta-test: runner 자체 검증)

.github/workflows/
└── docs-check.yml               (CI 워크플로우)
```

### 2.2 수정 파일

```
docs/conventions/git-workflow.md  (Documentation 자동 검증 섹션 추가)
docs/backlog.md                   (Item 11 archive)
```

### 2.3 참조 전용 (수정 없음)

```
docs/**/*.md                      (C1, C2, C3 검사 대상)
README.md, apps/README.md, core/*/README.md, common/*/README.md  (C1 검사 대상)
.env.example, bootstrap/src/main/resources/application-*.yml  (C3 대조 대상)
```

---

## 3. Architectural decisions

### 3.1 단일 러너 vs 다중 스크립트

**선택: 단일 bash 러너** (`docs-contract-test.sh`) 에 각 체크를 함수로.
- 이유: 3 체크는 공통 함수 (`fail_if`, `count_matches`) 공유. 파일 N 분리하면 boilerplate ↑
- Alternative rejected: 체크당 별도 파일 — 과도한 구조, 공유 함수 중복

### 3.2 Exclusions 포맷

```
# exclusions.conf — false-positive 화이트리스트
# 형식: <check-id>:<pattern>     (# 주석 허용)

# CHANGELOG 과 plan 파일은 역사 기록 — 옛 심볼 의도적 잔존
c1:CHANGELOG.md
c1:docs/plans/

# 문서 자체에 exclusion pattern 설명 목적
c1:docs/conventions/git-workflow.md:deprecated-blacklist-example
```

각 체크가 exclusion.conf 를 파싱하여 pattern 에 매칭되는 경로를 skip.

### 3.3 에러 출력 형식

```
❌ C1 (deprecated-symbols) FAIL
   docs/guides/storage-setup.md:12: 'UserCredentials' 참조 (Item 7 rename → UserAccount)
   docs/guides/storage-setup.md:45: 'TokenPair' 참조 (Item 7 rename → AuthTokens)

❌ C2 (broken-links) FAIL
   docs/architecture.md:150: 링크 대상 없음 './guides/old-setup.md'

✅ C3 (env-vars) PASS

========== 요약 ==========
2 checks FAILED, 1 check PASSED.
exit code 1
```

### 3.4 성능

예상 파일 크기: `docs/` ~30 파일, 모듈 README ~22 파일. grep 한 번당 < 100ms. 전체 CI run 5초 이내.

### 3.5 rg (ripgrep) vs GNU grep

**선택: GNU grep** — Ubuntu runner 기본 탑재. rg 는 설치 단계 추가 필요.
- `ripgrep` 이 있으면 속도 개선 (2~3x) 되지만 현재 스케일에서 무의미.

---

## 4. Tasks (TDD)

### Task 1: Runner skeleton + 메타 테스트 하네스

**Files:**
- Create: `tools/docs-check/docs-contract-test.sh`
- Create: `tools/docs-check/tests/test-docs-check.sh`

- [ ] **Step 1: Write failing test**

`tools/docs-check/tests/test-docs-check.sh`:

```bash
#!/usr/bin/env bash
# 메타 테스트: runner 자체가 돌아가는지 + 각 체크 함수 호출 가능한지 확인
set -euo pipefail

REPO=$(cd "$(dirname "$0")/../../.." && pwd)
RUNNER="${REPO}/tools/docs-check/docs-contract-test.sh"

# 테스트 1: runner 파일 존재 + 실행 권한
[ -x "${RUNNER}" ] || { echo "FAIL: ${RUNNER} 실행 권한 없음"; exit 1; }

# 테스트 2: --help 지원
"${RUNNER}" --help > /dev/null 2>&1 || { echo "FAIL: --help 미지원"; exit 1; }

# 테스트 3: 체크 0 개 시 exit 0 (모든 체크 주석처리 상태에선 pass)
# (runner 의 check dispatch 가 정상 작동 확인 용)
"${RUNNER}" --self-test > /dev/null 2>&1 && echo "PASS: Task 1 (runner skeleton)"
```

- [ ] **Step 2: Run test to verify fail**

Run: `bash tools/docs-check/tests/test-docs-check.sh`
Expected: `FAIL: .../docs-contract-test.sh 실행 권한 없음` (runner 아직 없음)

- [ ] **Step 3: Write minimal runner**

`tools/docs-check/docs-contract-test.sh`:

```bash
#!/usr/bin/env bash
# ============================================================
# docs-contract-test.sh — 문서 contract 자동 검증
#
# 목적: 문서의 claim 이 실제 artifact 와 일치하는지 CI 에서 검증.
# 의존: bash 4+, GNU grep, find. 외부 도구 없음.
# 실행 위치: 프로젝트 루트 (settings.gradle 이 있는 디렉토리).
#
# 사용법:
#   ./tools/docs-check/docs-contract-test.sh               모든 체크 실행
#   ./tools/docs-check/docs-contract-test.sh --help        사용법 출력
#   ./tools/docs-check/docs-contract-test.sh --self-test   runner 자체 동작 확인
# ============================================================
set -euo pipefail

# ─── Globals ────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECK_DIR="${REPO_ROOT}/tools/docs-check"
EXCLUSIONS_FILE="${CHECK_DIR}/exclusions.conf"
FAILED_CHECKS=0
PASSED_CHECKS=0

# ─── Helpers ────────────────────────────────────────────────────────────────
info()  { echo "[INFO]  $*"; }
ok()    { echo "✅ $*"; PASSED_CHECKS=$((PASSED_CHECKS + 1)); }
fail()  { echo "❌ $*"; FAILED_CHECKS=$((FAILED_CHECKS + 1)); }

usage() {
    cat <<EOF
사용법: $0 [옵션]

옵션:
  --help         사용법 출력
  --self-test    runner 자체 동작 확인 (check 없이 exit 0)

체크:
  C1  deprecated-symbols  — Item 7 rename 심볼이 문서에 잔존 X
  C2  broken-links        — [text](./path.md) 링크 대상 존재
  C3  env-vars            — 문서 env var 가 .env.example / application-*.yml 에 존재
EOF
}

# ─── Main ──────────────────────────────────────────────────────────────────
main() {
    local mode="${1:-all}"
    case "$mode" in
        --help)       usage; exit 0 ;;
        --self-test)  info "self-test — runner 살아있음"; exit 0 ;;
    esac

    cd "${REPO_ROOT}"
    info "docs-contract-test 실행"

    # 체크는 Task 2 이후 추가됨
    echo ""
    echo "========== 요약 =========="
    echo "${PASSED_CHECKS} checks PASSED, ${FAILED_CHECKS} checks FAILED."

    if [[ "${FAILED_CHECKS}" -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
```

- [ ] **Step 4: 실행 권한 + 테스트 통과**

```bash
chmod +x tools/docs-check/docs-contract-test.sh tools/docs-check/tests/test-docs-check.sh
bash tools/docs-check/tests/test-docs-check.sh
```
Expected: `PASS: Task 1 (runner skeleton)`

- [ ] **Step 5: Commit**

```bash
git add tools/docs-check/
git commit -m "feat(tools): docs-contract-test runner skeleton + 메타 테스트"
```

---

### Task 2: C1 — Deprecated symbols 블랙리스트 체크

**Files:**
- Modify: `tools/docs-check/docs-contract-test.sh`
- Create: `tools/docs-check/exclusions.conf`
- Modify: `tools/docs-check/tests/test-docs-check.sh`

- [ ] **Step 1: Write failing test**

`tools/docs-check/tests/test-docs-check.sh` 끝에 추가:

```bash
# Task 2: C1 deprecated symbols
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# 가짜 레포 구조
mkdir -p "${TEST_DIR}/docs" "${TEST_DIR}/tools/docs-check"
cp "${RUNNER}" "${TEST_DIR}/tools/docs-check/docs-contract-test.sh"
cp "${REPO}/tools/docs-check/exclusions.conf" "${TEST_DIR}/tools/docs-check/exclusions.conf" 2>/dev/null || touch "${TEST_DIR}/tools/docs-check/exclusions.conf"

# Case 2a: 깨끗한 문서 — 통과
echo "# Clean doc" > "${TEST_DIR}/docs/clean.md"
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  || { echo "FAIL: C1 clean doc 에서 fail 발생"; exit 1; }

# Case 2b: 폐기 심볼 포함 → fail
echo "UserCredentials 는 OIDC 표준어" > "${TEST_DIR}/docs/dirty.md"
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  && { echo "FAIL: C1 dirty doc 에서 pass — 감지 실패"; exit 1; }

echo "PASS: Task 2 (C1 deprecated symbols)"
```

- [ ] **Step 2: Run test to verify fail**

Run: `bash tools/docs-check/tests/test-docs-check.sh`
Expected: `FAIL: C1 dirty doc 에서 pass — 감지 실패` (C1 아직 미구현)

- [ ] **Step 3: Create exclusions.conf**

`tools/docs-check/exclusions.conf`:

```
# exclusions.conf — docs-contract-test false-positive 화이트리스트
# 형식: <check-id>:<pattern>
#   <check-id>  c1 | c2 | c3
#   <pattern>   파일 경로 glob (docs-check 가 ${pattern}* 으로 startsWith 매칭)
# 주석 (#) 과 빈 줄은 무시됨.

# C1 (deprecated symbols) exclusions:
#   CHANGELOG: 역사 기록 — 옛 심볼 의도적 잔존
c1:CHANGELOG.md
#   plan 파일: 작업 당시 심볼명 기록 — 수정 대상 아님
c1:docs/plans/
#   이 runner 의 exclusion 설명이 심볼을 나열해야 함
c1:docs/conventions/git-workflow.md
c1:tools/docs-check/
```

- [ ] **Step 4: Implement C1 in runner**

`tools/docs-check/docs-contract-test.sh` 의 `# 체크는 Task 2 이후 추가됨` 주석 자리에 삽입:

```bash
check_c1_deprecated_symbols() {
    info "C1: deprecated symbols 체크 시작"
    local deprecated=(
        "UserCredentials"
        "TokenPair"
        "PushResult"
        "verifyReceipt"
        "toCredentials"
    )
    local excludes_args=()
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        if [[ "$line" =~ ^c1:(.+)$ ]]; then
            excludes_args+=("--exclude-dir=${BASH_REMATCH[1]}" "--exclude=${BASH_REMATCH[1]}")
        fi
    done < "${EXCLUSIONS_FILE}"

    local found=0
    local tmp; tmp=$(mktemp)
    for sym in "${deprecated[@]}"; do
        # 검색 범위: docs/, README.md, 모듈 README.md
        grep -rn --include="*.md" "${excludes_args[@]}" "${sym}" \
            docs/ README.md apps/*/README.md bootstrap/*/README.md \
            common/*/README.md core/*/README.md \
            > "${tmp}" 2>/dev/null || true
        if [[ -s "${tmp}" ]]; then
            found=1
            while IFS= read -r hit; do
                echo "   ${hit}  → Item 7 rename (참조 제거 필요)"
            done < "${tmp}"
        fi
    done
    rm -f "${tmp}"

    if [[ "${found}" -eq 1 ]]; then
        fail "C1 (deprecated-symbols) FAIL"
    else
        ok "C1 (deprecated-symbols) PASS"
    fi
}

# main 에서 호출
```

`main` 함수의 `# 체크는 Task 2 이후 추가됨` 위치에 `check_c1_deprecated_symbols` 추가. 또 `main` 의 `mode` 분기에서 `all` 일 때 실행되도록.

최종 main 모양:
```bash
main() {
    local mode="${1:-all}"
    case "$mode" in
        --help)       usage; exit 0 ;;
        --self-test)  info "self-test — runner 살아있음"; exit 0 ;;
    esac

    cd "${REPO_ROOT}"
    info "docs-contract-test 실행"

    check_c1_deprecated_symbols

    echo ""
    echo "========== 요약 =========="
    echo "${PASSED_CHECKS} checks PASSED, ${FAILED_CHECKS} checks FAILED."
    [[ "${FAILED_CHECKS}" -gt 0 ]] && exit 1
    exit 0
}
```

- [ ] **Step 5: Run test**

```bash
bash tools/docs-check/tests/test-docs-check.sh
```
Expected: `PASS: Task 2 (C1 deprecated symbols)`

- [ ] **Step 6: Run against real repo — verify baseline passes**

```bash
./tools/docs-check/docs-contract-test.sh
```
Expected: `C1 ... PASS` 또는 찾은 false-positive 는 exclusions.conf 에 추가.

- [ ] **Step 7: Commit**

```bash
git add tools/docs-check/
git commit -m "feat(tools): docs-contract C1 — deprecated symbols 블랙리스트 체크"
```

---

### Task 3: C2 — Broken markdown file-path links 체크

**Files:**
- Modify: `tools/docs-check/docs-contract-test.sh`
- Modify: `tools/docs-check/tests/test-docs-check.sh`

- [ ] **Step 1: Write failing test**

test-docs-check.sh 에 추가:

```bash
# Task 3: C2 broken links
# Case 3a: 유효한 링크 — pass
mkdir -p "${TEST_DIR}/docs/sub"
cat > "${TEST_DIR}/docs/sub/a.md" <<'MD'
# A
링크: [B 로](./b.md)
MD
echo "# B" > "${TEST_DIR}/docs/sub/b.md"
rm -f "${TEST_DIR}/docs/dirty.md"  # Task 2 잔재 제거
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  || { echo "FAIL: C2 valid link 에서 fail"; exit 1; }

# Case 3b: 깨진 링크 → fail
cat > "${TEST_DIR}/docs/sub/c.md" <<'MD'
깨진 링크: [없는 파일](./does-not-exist.md)
MD
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  && { echo "FAIL: C2 broken link 에서 pass — 감지 실패"; exit 1; }

echo "PASS: Task 3 (C2 broken links)"
```

- [ ] **Step 2: Run test to verify fail**

Expected: `FAIL: C2 broken link 에서 pass` (C2 미구현)

- [ ] **Step 3: Implement C2**

runner 에 함수 추가:

```bash
check_c2_broken_links() {
    info "C2: broken markdown links 체크 시작"
    local excludes_args=()
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        if [[ "$line" =~ ^c2:(.+)$ ]]; then
            excludes_args+=("--exclude-dir=${BASH_REMATCH[1]}" "--exclude=${BASH_REMATCH[1]}")
        fi
    done < "${EXCLUSIONS_FILE}"

    local found=0
    # 모든 .md 파일 순회
    while IFS= read -r md_file; do
        # 각 파일의 [text](path) 추출. path 는 .md 로 끝나거나 경로.
        while IFS= read -r linematch; do
            # linematch 형식: LINENO:LINE
            local lineno="${linematch%%:*}"
            local line="${linematch#*:}"
            # [text](./path.md) 또는 [text](../path.md) 등 상대 링크만
            while [[ "${line}" =~ \[([^]]+)\]\((\.[^)]+)\) ]]; do
                local link="${BASH_REMATCH[2]}"
                line="${line#*"${BASH_REMATCH[0]}"}"
                # fragment (#) 제거
                link="${link%%#*}"
                [[ -z "${link}" ]] && continue
                # 상대 경로 해석
                local md_dir; md_dir="$(dirname "${md_file}")"
                local resolved; resolved="$(cd "${md_dir}" 2>/dev/null && cd "$(dirname "${link}")" 2>/dev/null && pwd)/$(basename "${link}")"
                if [[ ! -e "${resolved}" ]]; then
                    echo "   ${md_file}:${lineno}  링크 대상 없음: ${link}"
                    found=1
                fi
            done
        done < <(grep -n "](\." "${md_file}" || true)
    done < <(find docs README.md apps/*/README.md bootstrap/*/README.md \
        common/*/README.md core/*/README.md -name "*.md" -type f 2>/dev/null \
        | grep -vE "$(IFS='|'; echo "${excludes_args[*]:-__NEVER__}" | sed 's/--exclude=//g; s/--exclude-dir=//g; s/ /|/g')" || true)

    if [[ "${found}" -eq 1 ]]; then
        fail "C2 (broken-links) FAIL"
    else
        ok "C2 (broken-links) PASS"
    fi
}
```

main 에 호출 추가:
```bash
check_c1_deprecated_symbols
check_c2_broken_links
```

**주의**: bash `[[ ... =~ ... ]]` 는 POSIX 확장. macOS 의 bash 3.x 에서도 동작. GNU grep `-n` 지원됨.

**단순화 제안**: 위 구현이 너무 복잡하면 awk 로 대체:

```bash
check_c2_broken_links() {
    info "C2: broken markdown links 체크 시작"
    local found=0
    local tmp; tmp=$(mktemp)
    # 모든 .md 를 awk 로 파싱
    find docs README.md apps/*/README.md bootstrap/*/README.md \
         common/*/README.md core/*/README.md -name "*.md" -type f 2>/dev/null |
    while IFS= read -r md_file; do
        # grep 으로 [text](./path.md) 추출 후 awk 로 link 만
        grep -oE "\]\(\.[^)]+\)" "${md_file}" | sed 's/^](//; s/)$//' |
        while IFS= read -r link; do
            link="${link%%#*}"
            [[ -z "${link}" ]] && continue
            local md_dir; md_dir="$(dirname "${md_file}")"
            # readlink 로 절대 경로 해석
            local resolved="${md_dir}/${link}"
            # .. 처리
            resolved="$(cd "${md_dir}" 2>/dev/null && realpath --canonicalize-missing "${link}" 2>/dev/null || echo "${md_dir}/${link}")"
            if [[ ! -e "${resolved}" ]]; then
                echo "   ${md_file}: 링크 대상 없음: ${link}" >> "${tmp}"
            fi
        done
    done
    if [[ -s "${tmp}" ]]; then
        cat "${tmp}"
        rm -f "${tmp}"
        fail "C2 (broken-links) FAIL"
    else
        rm -f "${tmp}"
        ok "C2 (broken-links) PASS"
    fi
}
```

**권장**: 단순화 제안 사용. 구현자가 macOS bash 3.x + 호환 확인.

- [ ] **Step 4: Run test to verify pass**

```bash
bash tools/docs-check/tests/test-docs-check.sh
```
Expected: `PASS: Task 3 (C2 broken links)`

- [ ] **Step 5: Run against real repo — fix findings**

```bash
./tools/docs-check/docs-contract-test.sh
```
찾은 실제 broken link 는 해당 문서를 수정하여 fix. 의도적 잔존은 exclusions.conf 에 c2:<pattern> 추가.

- [ ] **Step 6: Commit**

```bash
git add tools/docs-check/ docs/  # docs 수정 있을 수 있음
git commit -m "feat(tools): docs-contract C2 — broken markdown links 체크"
```

---

### Task 4: C3 — Env var consistency 체크

**Files:**
- Modify: `tools/docs-check/docs-contract-test.sh`
- Modify: `tools/docs-check/tests/test-docs-check.sh`

- [ ] **Step 1: Write failing test**

```bash
# Task 4: C3 env vars
# Case 4a: 알려진 변수 — pass
cat > "${TEST_DIR}/.env.example" <<'ENV'
SPRING_PROFILES_ACTIVE=dev
APP_KNOWN_VAR=value
ENV
echo "SPRING_PROFILES_ACTIVE 를 dev 로 설정" > "${TEST_DIR}/docs/envdoc.md"
rm -f "${TEST_DIR}/docs/sub/c.md"  # Task 3 잔재
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  || { echo "FAIL: C3 known var 에서 fail"; exit 1; }

# Case 4b: 미지의 변수 → fail
echo "FAKE_NONEXISTENT_VAR 같은 건 없어" > "${TEST_DIR}/docs/envbad.md"
(cd "${TEST_DIR}" && bash tools/docs-check/docs-contract-test.sh) > /dev/null 2>&1 \
  && { echo "FAIL: C3 fake var 에서 pass — 감지 실패"; exit 1; }

echo "PASS: Task 4 (C3 env vars)"
```

- [ ] **Step 2: Run test (fail expected)**

- [ ] **Step 3: Implement C3**

```bash
check_c3_env_vars() {
    info "C3: env var consistency 체크 시작"
    # 알려진 env var 모으기 (.env.example + application-*.yml placeholder)
    local known_file; known_file=$(mktemp)
    {
        grep -oE "^[A-Z][A-Z0-9_]*=" .env.example 2>/dev/null | sed 's/=$//'
        # application-*.yml 의 ${VAR} 또는 ${VAR:default}
        grep -rhoE '\$\{[A-Z][A-Z0-9_]*' bootstrap/src/main/resources/*.yml 2>/dev/null \
            | sed 's/^\${//'
    } | sort -u > "${known_file}"

    # 문서에서 env var 추출 (PREFIX 기반)
    local doc_vars; doc_vars=$(mktemp)
    # 대문자 시작 + 5 자 이상 + 언더스코어 포함 + 널리 쓰이는 prefix
    grep -rhoE '\b(APP|SPRING|JWT|POSTGRES|DB|RESEND|MINIO|LOKI|DISCORD|MANAGEMENT|GRAFANA|APP_STORAGE|APP_CREDENTIALS|APP_PUSH|APP_RATE|APP_DOMAIN)_[A-Z0-9_]+\b' \
        --include="*.md" docs/ README.md apps/*/README.md bootstrap/*/README.md \
        common/*/README.md core/*/README.md 2>/dev/null | sort -u > "${doc_vars}"

    # doc 에 있지만 known 에 없는 것
    local missing; missing=$(comm -23 "${doc_vars}" "${known_file}")

    # exclusions (c3:) 는 prefix 기준으로 skip — 단순화: exclusion 은 c3 에서는 "known 에 추가" 역할
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        if [[ "$line" =~ ^c3:(.+)$ ]]; then
            # exclusion 의 pattern 은 "이 env var 는 어디서도 정의 안 됐지만 의도적 참조" 명시
            missing=$(echo "${missing}" | grep -vFx "${BASH_REMATCH[1]}" || true)
        fi
    done < "${EXCLUSIONS_FILE}"

    rm -f "${known_file}" "${doc_vars}"

    if [[ -n "${missing}" ]]; then
        while IFS= read -r var; do
            echo "   ${var}  — 문서에 언급됐으나 .env.example / application-*.yml 어디에도 없음"
        done <<< "${missing}"
        fail "C3 (env-vars) FAIL"
    else
        ok "C3 (env-vars) PASS"
    fi
}
```

main 에 추가:
```bash
check_c1_deprecated_symbols
check_c2_broken_links
check_c3_env_vars
```

- [ ] **Step 4: Run test**

Expected: `PASS: Task 4 (C3 env vars)`

- [ ] **Step 5: Run against real repo**

```bash
./tools/docs-check/docs-contract-test.sh
```
False positive 는 exclusions.conf 에 `c3:<VAR_NAME>` 로 추가 (의도적 참조 표시).

- [ ] **Step 6: Commit**

```bash
git add tools/docs-check/
git commit -m "feat(tools): docs-contract C3 — env var consistency 체크"
```

---

### Task 5: GitHub Actions 워크플로우

**Files:**
- Create: `.github/workflows/docs-check.yml`

- [ ] **Step 1: Write workflow**

```yaml
name: docs-check

on:
  push:
    branches:
      - '**'
  pull_request:
    branches:
      - main

concurrency:
  group: docs-check-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  docs-contract:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - name: Run docs contract test
        run: |
          chmod +x tools/docs-check/docs-contract-test.sh
          ./tools/docs-check/docs-contract-test.sh

      - name: Run meta test (runner 자체 검증)
        run: |
          chmod +x tools/docs-check/tests/test-docs-check.sh
          bash tools/docs-check/tests/test-docs-check.sh
```

- [ ] **Step 2: Local validation**

```bash
# syntax check (yq or yamllint 없으면 python 으로)
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docs-check.yml'))" \
  && echo "yaml syntax OK"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/docs-check.yml
git commit -m "ci: docs-check 워크플로우 추가 (PR + push 트리거)"
```

---

### Task 6: 초기 baseline + exclusions 등록

**Files:**
- Modify (if needed): `tools/docs-check/exclusions.conf`
- Modify (if needed): `docs/*.md` (실제 drift 발견 시)

- [ ] **Step 1: Run runner against real repo**

```bash
./tools/docs-check/docs-contract-test.sh
```

- [ ] **Step 2: 각 FAIL 항목 분류**

각 실패 항목에 대해:
1. **실제 drift** — 문서 수정 필요 (잘못된 파일 경로, 옛 심볼 잔존)
2. **False positive** — 의도적 참조, exclusions.conf 에 추가 (이유 주석 포함)

- [ ] **Step 3: 수정 + exclusions 등록**

예시 exclusions.conf 추가:
```
# runner 가 자기 자신의 regex 패턴 문자열을 "UserCredentials" 매칭으로 감지 — false positive
c1:tools/docs-check/docs-contract-test.sh

# backlog.md 의 "Item 10b" 는 미래 Item 참조 — 문서 링크 체크 적용 안 함
# (실제로 c2 에 걸리지 않으면 무시)
```

실제 drift 는 해당 문서에서 수정.

- [ ] **Step 4: Run again — all PASS 확인**

```bash
./tools/docs-check/docs-contract-test.sh
echo "exit: $?"
```
Expected: `exit: 0`, 모든 체크 PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/docs-check/exclusions.conf docs/
git commit -m "chore(docs): Item 11 baseline — drift fix + exclusions 등록"
```

---

### Task 7: 문서 업데이트 + backlog archive

**Files:**
- Modify: `docs/conventions/git-workflow.md`
- Modify: `docs/backlog.md`

- [ ] **Step 1: git-workflow.md 에 "문서 자동 검증" 섹션 추가**

기존 "Backlog 운영 규칙" 섹션 뒤에:

```markdown
## 문서 자동 검증 (docs-check)

`tools/docs-check/docs-contract-test.sh` 가 CI 에서 문서 drift 를 자동 검증:

| 체크 | 확인 사항 |
|---|---|
| C1 | Item 7 rename 된 심볼 (`UserCredentials`, `TokenPair`, `PushResult`, `verifyReceipt`, `toCredentials`) 이 문서에 잔존 X (CHANGELOG / plans 예외) |
| C2 | Markdown 상대 경로 링크 `[text](./path.md)` 의 대상 파일 존재 |
| C3 | 문서에 언급된 env var (`APP_*` / `SPRING_*` / `JWT_*` 등) 가 `.env.example` 또는 `application-*.yml` 에 정의됨 |

### 로컬 실행
```bash
./tools/docs-check/docs-contract-test.sh
```

### False positive 처리
`tools/docs-check/exclusions.conf` 에 `<check-id>:<pattern>` 추가 (이유 주석 필수).

### 트리거
`.github/workflows/docs-check.yml` — PR + push-to-any-branch 에서 실행.
```

- [ ] **Step 2: backlog.md — Item 11 archive**

DX 섹션의 Item 11 제거, archive 섹션에 추가:

```markdown
## 완료 (archive, 지난 2개월)
- [x] Item 7 — ...
- [x] Item 9 v1 → v2 plan 개정 ...
- [x] Item 10 — 앱 프로비저닝 통합 스크립트 ...
- [x] Item 11 — Documentation contract test (완료일: 2026-04-19, merge: TBD)
```

- [ ] **Step 3: Commit**

```bash
git add docs/conventions/git-workflow.md docs/backlog.md
git commit -m "docs: Item 11 문서 검증 자동화 규칙 + backlog archive"
```

---

## 5. 완료 기준 (DoD)

- [ ] Task 1~7 전부 commit, 각자 테스트 통과
- [ ] `bash tools/docs-check/tests/test-docs-check.sh` → PASS
- [ ] `./tools/docs-check/docs-contract-test.sh` → exit 0 (현 main 기준 clean)
- [ ] `.github/workflows/docs-check.yml` 이 PR 에서 녹색 (merge 후 확인)
- [ ] `git-workflow.md` 에 "문서 자동 검증" 섹션 추가됨
- [ ] `backlog.md` Item 11 archive + merge hash 기록
- [ ] Feature branch → main 머지 + push

---

## 6. 위험 요소

| 위험 | 영향 | 완화 |
|---|---|---|
| C2 (broken links) 의 경로 해석 복잡도 | 거짓 양성 / 음성 | Task 3 에서 `realpath --canonicalize-missing` 사용. macOS 엔 없으므로 fallback 구현 (bash 만으로) |
| C3 의 env var prefix list 누락 | 새로운 prefix 추가 시 감지 누락 | Task 6 baseline 에서 발견. prefix 추가는 runner 의 grep 패턴 확장 |
| macOS bash 3.x 호환 | runner 자체 동작 실패 | 모든 함수 `bash -n` 검증 + CI 는 ubuntu bash 5.x |
| Exclusions 과도 사용 | drift 가 "의도적" 으로 위장됨 | exclusions.conf 에 **이유 주석 필수**, 리뷰어가 체크 |
| False positive 첫 baseline 이 많을 경우 | Task 6 시간 초과 | 명확한 실제 drift 만 fix, 나머지는 exclude. Task 7 끝날 때까지 baseline clean 목표 |
| CI 에서 runner 실패 | PR block | 로컬 실행으로 먼저 검증 — baseline clean 필수 |

---

## 7. 진행 추적

- [ ] Task 1: Runner skeleton + 메타 테스트
- [ ] Task 2: C1 deprecated symbols
- [ ] Task 3: C2 broken links
- [ ] Task 4: C3 env vars
- [ ] Task 5: GitHub Actions 워크플로우
- [ ] Task 6: Baseline + exclusions 등록
- [ ] Task 7: 문서 업데이트 + archive
- [ ] 최종 merge to main + push
