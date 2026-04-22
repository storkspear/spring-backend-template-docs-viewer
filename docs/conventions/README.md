# Coding Conventions

이 디렉토리는 `spring-backend-template` 및 이를 파생한 모든 레포의 **코딩 규약** 을 담습니다.

규약은 취향이 아니라 **일관성을 위한 계약** 입니다. 혼자 작업하더라도, 6개월 뒤의 나 자신이 과거 코드를 이해할 수 있어야 합니다. 그리고 파생 레포가 여러 개 생겼을 때 각 레포의 코드 스타일이 비슷해야 cherry-pick backport 가 매끄럽습니다.

---

## 문서 구성

- [`naming.md`](./naming.md) — 패키지/클래스/메서드/DB 네이밍 규칙
- [`api-response.md`](./api-response.md) — API 응답 포맷, 에러 코드, HTTP 상태, 페이지네이션
- [`design-principles.md`](./design-principles.md) — SOLID, DRY, YAGNI, 포트/어댑터, 의존 방향
- [`exception-handling.md`](./exception-handling.md) — 예외 계층, ErrorCode enum, HTTP 매핑, 추가 절차, 테스트 검증
- [`contract-testing.md`](./contract-testing.md) — 3층 테스트 구조, Port 계약, Fake adapter 패턴
- [`json-contract.md`](./json-contract.md) — DTO JSON 직렬화 정책, `AbstractJsonContractTest` 사용법
- [`module-dependencies.md`](./module-dependencies.md) — 모듈 의존 허용 매트릭스, Gradle convention plugin, ArchUnit 12개 규칙
- [`git-workflow.md`](./git-workflow.md) — 브랜치 · 커밋 규약 · Merge 전략 · Conventional Commits
- [`versioning.md`](./versioning.md) — semver · CHANGELOG · Deprecation · 릴리스 프로세스
- [`dto-factory.md`](./dto-factory.md) — DTO 팩토리 패턴 (from/of/with), Mapper 폐기, Entity `to<Dto>()` 패턴
- [`records-and-classes.md`](./records-and-classes.md) — record vs class 결정 기준
- [`observability.md`](./observability.md) — 메트릭·로그·알림 3축, `appSlug` 의무 태깅, 임계치
- [`rate-limiting.md`](./rate-limiting.md) — Bucket4j 키 설계, 민감 엔드포인트, 초과 응답
- [`storage.md`](./storage.md) — StoragePort Signed URL 패턴, bucket naming, retention, 용량 계산

---

## 규약의 우선순위

서로 충돌하는 것처럼 보이는 규약이 있을 때 다음 순서로 해결합니다.

1. **동작하는 코드** 가 이상적인 규약보다 우선입니다. 규약을 지키기 위해 테스트가 실패하거나 런타임 동작이 깨지면 규약이 틀린 것입니다.
2. **이 문서에 명시된 규약** 이 개인 취향보다 우선합니다.
3. **프로젝트 내 기존 패턴** 이 새 패턴보다 우선입니다. 기존 코드와 일관성 있게 따라가고, 필요하면 문서를 업데이트한 후 일괄 리팩토링합니다.
4. **SOLID/DRY/YAGNI** 같은 원칙은 참조점이지 절대 기준이 아닙니다. 상황에 맞게 적용합니다.

---

## 규약을 지키는 방법

**자동화가 1순위입니다.** 가능한 한 IDE, 빌드, CI 가 규약을 강제하도록 만듭니다.

- **Gradle 빌드** — 모듈 의존 관계 강제
- **ArchUnit 테스트** — 패키지 구조 및 네이밍 강제
- **checkstyle / spotless** — 포맷팅 강제 (Phase 1+ 도입 예정)
- **pre-commit hook** — 커밋 메시지 형식 검증 (선택)

사람의 의지로 지키는 규약은 2~3주 안에 무너집니다. 기계가 막아주도록 만드는 것이 유일한 지속 가능한 방법입니다.

---

## 모듈 README 유지 규칙

각 모듈 디렉토리(`common/*`, `core/*`, `bootstrap`, `apps/*`)에는 `README.md` 가 있습니다. 코드를 변경할 때 다음 중 하나라도 해당되면 **같은 커밋에서** 해당 모듈의 `README.md` 를 함께 업데이트합니다.

1. **새 public 클래스를 추가**했을 때 → "제공 기능" 섹션에 추가
2. **기존 클래스를 삭제/이름 변경**했을 때 → README 에서 제거/수정
3. **의존 모듈이 바뀌었을 때** (build.gradle 변경) → "의존" 섹션 업데이트
4. **주요 설계 결정이 바뀌었을 때** → "주의" 섹션 업데이트
5. **환경변수/설정이 추가/변경**됐을 때 → 해당 섹션 업데이트

별도 "docs 업데이트" 커밋으로 분리하지 않고, 코드 변경과 같은 커밋에 포함합니다. 이렇게 해야 코드와 문서가 어긋나지 않습니다.

---

## 기여

규약은 고정되어 있지 않습니다. 개선 의견이 있으면 해당 문서에 직접 수정을 제안하거나, 기존 규약이 실제 코드 작성에서 걸림돌이 되면 즉시 재평가합니다. 다만 **"이 결정의 이유가 여전히 유효한가"** 를 먼저 확인한 후 바꿉니다.
