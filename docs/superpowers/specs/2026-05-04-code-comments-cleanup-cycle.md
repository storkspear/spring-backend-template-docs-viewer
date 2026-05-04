# Code Comments Cleanup Cycle — Light Spec

> **유형**: Spec · **독자**: Level 2 · **읽는 시간**: ~3분

**Goal** — `cleanup-legacy-cycle` 의 후속 sweep. bash / Java / Groovy 코드 코멘트 안 *우리 플젝 옛 흐름 변명* 표현 정리.

**전제** — 2026-05-04 cleanup-legacy-cycle (commit `9f81c77` 까지) 완료 후 추가 sweep.

---

## Scope

본 사이클이 다루는 영역:
- `tools/**/*.sh` 의 코멘트
- `core/`, `common/`, `apps/` 의 Java javadoc + 인라인 코멘트
- `build-logic/` 의 Groovy DSL + Java
- `.github/workflows/*.yml` 의 코멘트

**다루지 않는 영역** (별도 사이클 / 사용자 분류 OK):
- CHANGELOG.md 의 *2026-04~05 사이클 / Released timestamp / 이전엔 string literal* — CHANGELOG 표준 표현
- 테스트 fixture 의 `Instant.parse("2026-04-XX")` — 테스트 데이터 timestamp
- `옛 GHCR 이미지 / 옛 tailscale 1.42.0 / 태그 있는 옛 버전` — runtime 시간 / 외부 도구 옛 버전 (사용자 OK 분류)
- `cleanup.sh:239 [OK] 옛 docker images 정리` — runtime cleanup 대상 (외부 시간)

---

## 정리 대상 (5건)

| File:Line | 현재 표현 | 변환 방향 |
|---|---|---|
| `tools/init-server.sh:79` | `# - all:   기존 동작 (1+2회차 한 번에) — backward compat 또는 legacy` | *legacy* 라벨 제거 — `# - all: 1+2회차 한 번에 (default)` |
| `tools/init-server.sh:138` | `# default mode (--all) 일 때만 공동 작업자 자동 감지 (legacy 호환).` | *legacy 호환* 제거 — `# default mode (--all) 일 때만 공동 작업자 자동 감지.` |
| `tools/new-app/new-app.sh:7` | `#   <repo> new <slug>                legacy (동일 동작)` | *legacy* → *(별칭)* — `#   <repo> new <slug>                (별칭, 동일 동작)` |
| `tools/dogfooding/cleanup.sh:109` | `- Variables 2개 (DEPLOY_ENABLED, KAMAL_SERVICE_NAME) + 옛 Variables (DEPLOY_HOST 등 — graceful)` | *옛 Variables* → *추가 Variables (다른 등록 형태)* — graceful 의도 보존 |
| `tools/dogfooding/cleanup.sh:130` | `# 옛 버전에서 Variable 이었던 DEPLOY_HOST/SSH_USER/PUBLIC_HOSTNAME 도 함께 시도 (graceful).` | *옛 버전에서 Variable 이었던* → *Variable 형태로 등록된 경우* — graceful 의도 보존 |

---

## 변환 원칙

`docs/superpowers/specs/2026-05-04-cleanup-legacy-cycle-design.md` 의 변환 원칙 그대로 재사용:

- *플젝 시간 흐름 변명* (`legacy 호환 / 옛 버전 / 옛 Variables`) 제거
- *기능 / graceful 의도* 보존
- 외부 도구 옛 버전 / runtime 시간 / CHANGELOG 표준 표현은 보존

---

## 검증

```bash
# 1. 정리 대상 grep 0건 (의도적 보존 외)
grep -rEn 'legacy 호환|legacy \(동일|backward compat|옛 Variables|옛 버전' tools/ core/ common/ apps/ build-logic/ .github/workflows/

# 2. ci-test 5/5 PASS
bash tools/ci-test.sh

# 3. push 1회 (사이클 끝)
git push origin main
```

---

## Out-of-scope

- 본 사이클은 *코멘트 / 라벨* 만 정리. 함수 / 메서드 / 변수명은 변경하지 않음.
- bash 스크립트의 *기능 동작* 은 0 변경 (graceful 흐름 그대로).
