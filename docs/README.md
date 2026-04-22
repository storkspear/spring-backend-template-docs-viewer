# 📚 spring-backend-template — 책 목차 (Developer Journey)

이 문서는 `docs/` 안의 모든 문서를 **읽는 순서** 로 안내합니다.

`README.md` 의 30분 QuickStart 만으로도 첫 기동은 됩니다. 이 책은 그 이후, 레포의 정체와 사용 흐름을 차근차근 이해하고 싶을 때 읽는 안내서입니다.

각 단계 끝에는 다음 단계로 넘어가는 링크가 있습니다. 책처럼 위에서 아래로 한 번 흐르듯 읽으면 자연스럽게 전체 그림이 잡힙니다.

> 💡 막히면: [도그푸딩 함정 모음](./troubleshooting/dogfood-pitfalls.md) / [도그푸딩 FAQ](./guides/dogfood-faq.md) 부터 검색해 보세요.

---

## 0. 시작 전 — README 의 QuickStart (30분)

이미 마치셨다면 1단계로 넘어가세요. 안 했다면 [`README.md`](../README.md) 의 "30분 QuickStart" 부터 따라가세요.

QuickStart 는 다음을 합니다.

- 로컬 dev 환경 부팅 (`tools/bootstrap.sh`)
- Spring 첫 기동 확인
- 첫 앱 모듈 생성 (`tools/new-app/new-app.sh`)

이 책은 QuickStart 가 끝났다는 가정에서 시작합니다.

---

## 1. 이 레포가 뭐야? (15분)

이 레포의 **정체** 를 이해합니다. 어떤 종류의 프로젝트이고, 왜 이렇게 설계됐는지 큰 그림을 잡습니다.

읽을 문서:

1. [`philosophy.md`](./philosophy.md) 의 **결정 1 ~ 3** 만 먼저 읽으세요.
   - 결정 1: 모듈러 모놀리스 (왜 마이크로서비스가 아닌가)
   - 결정 2: GitHub Template Repository 패턴 (왜 fork 가 아닌 template 인가)
   - 결정 3: `core/` 모듈을 `-api` / `-impl` 로 분리 (왜 인터페이스/구현 분리인가)

2. [`architecture.md`](./architecture.md) 의 **§ 전체 구성 요약** 한 섹션만 읽으세요. 모듈 3종류 (`common/` · `core/` · `apps/`) 와 기술 스택의 한눈 요약이 있습니다.

여기까지 읽으면 "이 레포가 뭘 하려는 도구인지" 감이 잡힙니다. 더 깊은 결정 (4 ~ 22번) 은 나중에 필요할 때 돌아오세요.

---

## 2. 어떻게 써? — 로컬 개발 (1시간)

본인 노트북에서 dev 환경을 띄우고 Spring 을 직접 돌려 봅니다.

읽을 문서:

- [`guides/onboarding.md`](./guides/onboarding.md) — 전체 한 번 정독.

핵심 흐름은 다음과 같습니다.

1. `§1 사전 설치 체크리스트` — JDK 21+, Docker, Node 18+ 설치 확인.
2. `§2 파생 레포 생성` — "Use this template" 으로 본인 레포 만들기 (지금은 template 자체를 보고 있다면 skip).
3. `§3 환경 변수 설정` — `.env.example` → `.env` 복사 후 채우기.
4. `§4 첫 기동` — `tools/bootstrap.sh` 실행 → Spring `bootRun` 으로 동작 확인.

여기까지 마치면 본인 노트북에서 Spring 이 살아 움직입니다.

---

## 3. 클론 후 뭐부터? — 첫 앱 모듈 추가 (30분)

template 은 비즈니스 로직 없이 뼈대만 가지고 있습니다. 실제로 쓰려면 **앱 모듈** 을 하나 추가해야 합니다.

읽을 문서:

- [`guides/onboarding.md`](./guides/onboarding.md) **§5 앱 모듈 추가 (`new-app.sh`)** 섹션.

수행하는 일:

```bash
./tools/new-app/new-app.sh <slug> --provision-db
```

이 명령은 `apps/app-<slug>/` 디렉터리를 만들고, Postgres 에 앱 전용 schema + role 을 자동 생성합니다. 자세한 동작과 생성되는 파일 목록은 위 §5 에 표로 정리돼 있습니다.

여기까지 끝나면 본인 앱 도메인이 코드 위에 올라간 상태가 됩니다.

---

## 4. 발급은 어디서? — 외부 리소스 (1시간)

운영 배포로 넘어가려면 외부 서비스의 자격 증명을 발급받아야 합니다. 어디서 어떻게 받는지가 막히는 지점이라, 두 문서로 나뉘어 안내합니다.

### 4.1 소셜 로그인 자격 증명

[`social-auth-setup.md`](./social-auth-setup.md) 를 읽으세요.

- Google Sign In Client ID 발급 절차 + Console 에서 입력할 값
- Apple Sign In Bundle ID + Service ID 발급 절차

각 발급 후 `.env` 의 `APP_CREDENTIALS_<SLUG>_*` 변수에 채워 넣습니다.

### 4.2 운영 배포 자격 증명 (Tailscale OAuth · GitHub PAT · Supabase)

[`guides/dogfood-setup.md`](./guides/dogfood-setup.md) **§3 외부 리소스 발급** 섹션을 읽으세요.

- §3.1 GitHub PAT (GHCR push 권한)
- §3.2 Tailscale OAuth client (GHA → Mac mini 라우팅)
- §3.3 Mac mini SSH 셋업
- §3.5 Supabase Connection 정보

각 항목에 화면 캡처 없이도 따라갈 수 있게 클릭 경로 + 주의사항 (잘못 발급되는 함정 포함) 까지 적혀 있습니다.

---

## 5. 테스트 어떻게? — 도그푸딩 자동 검증 (자동)

발급 받은 값으로 template 자체가 운영 환경에 올라가는지 한 사이클 검증합니다.

읽을 문서:

- [`guides/dogfood-setup.md`](./guides/dogfood-setup.md) **§4 ~ §6** (작성 + 실행 + 동작 확인).
- 막히면 [`troubleshooting/dogfood-pitfalls.md`](./troubleshooting/dogfood-pitfalls.md).

핵심 명령은 두 줄입니다.

```bash
cp tools/dogfooding/.env.dogfood{.example,}
$EDITOR tools/dogfooding/.env.dogfood
bash tools/dogfooding/setup.sh
```

`setup.sh` 가 GitHub Actions Variables / Secrets 일괄 등록 + GHA 용 SSH 키 발급 + DEPLOY_ENABLED 토글 + 자동 배포 trigger 까지 한 번에 처리합니다.

배포가 실행되는 전체 흐름이 궁금하다면 [`architecture/ci-cd-flow.md`](./architecture/ci-cd-flow.md) 의 다이어그램을 참고하세요.

---

## 6. 정리? — cleanup (5분)

검증이 끝났으면 깨끗하게 정리하고 template 순수 상태로 돌립니다.

읽을 문서:

- [`guides/dogfood-setup.md`](./guides/dogfood-setup.md) **§7 `cleanup.sh` 실행** 섹션.

핵심 명령은 한 줄입니다.

```bash
bash tools/dogfooding/cleanup.sh
```

이 명령이 다음을 모두 처리합니다.

- GitHub Variables / Secrets 전체 삭제
- Mac mini 의 spring 컨테이너 + kamal-proxy + authorized_keys 의 GHA 키 정리
- GHCR 의 도그푸딩 이미지 삭제

외부 서비스 (PAT / Tailscale OAuth) 의 키 자체는 **본인이 직접 폐기** 해야 합니다. 절차는 [`security/key-rotation.md`](./security/key-rotation.md) 에 있습니다.

---

## 7. 이제 use this template — 파생 레포 첫 배포 (30분)

template 의 구조와 자동화를 이해했으니, 이제 실제 본인 프로젝트로 옮길 차례입니다.

읽을 문서:

1. [`guides/deployment.md`](./guides/deployment.md) — "Use this template" 으로 만든 파생 레포를 Mac mini 에 처음 배포하는 onboarding.
2. [`guides/cross-repo-cherry-pick.md`](./guides/cross-repo-cherry-pick.md) — template 에 새 변경이 생겼을 때 파생 레포로 가져오는 방법.

핵심 흐름은 도그푸딩과 거의 동일합니다 (5 ~ 6단계). 차이는:

- 파생 레포는 본인 도메인 / 본인 인프라 값으로 채웁니다.
- DEPLOY_ENABLED 가 본격 운영 모드라 cleanup 으로 되돌릴 일이 없습니다.

---

## 깊이 있는 참조 (필요할 때 돌아오는 곳)

위 책 본문에서는 "왜?" 를 자세히 다루지 않습니다. 본문이 가볍게 흘러가게 하기 위함입니다. 깊이 들어가고 싶을 때 다음 문서들을 참고하세요.

| 궁금한 것 | 문서 | 한 줄 설명 |
|---|---|---|
| 왜 이렇게 설계? | [`philosophy.md`](./philosophy.md) | 핵심 결정 22개 (1 ~ 22) |
| 인프라 결정 근거 | [`conventions/decisions-infra.md`](./conventions/decisions-infra.md) | I-01 ~ I-14 결정 카드 (Supabase / Mac mini / Kamal / GHCR PAT 등) |
| 모듈 구조 상세 | [`architecture.md`](./architecture.md) | 731줄 — 파일 트리 + 의존 그래프 + 기술 스택 |
| 환경별 인프라 현황 | [`infrastructure.md`](./infrastructure.md) | 어떤 서비스가 어디에서 도는지 |
| 코딩 규약 11종 | [`conventions/`](./conventions/) | naming / api-response / exception 등 |
| 평시 배포 / 롤백 / 장애 | [`runbook.md`](./runbook.md) | 운영자용 절차서 |
| 장애 시나리오 분석 | [`edge-cases.md`](./edge-cases.md) | 무엇이 깨질 수 있나 |
| 미완 항목 추적 | [`backlog.md`](./backlog.md) | 진행 중 / 대기 |
| 키 교체 절차 | [`security/key-rotation.md`](./security/key-rotation.md) | PAT / Tailscale OAuth / Supabase / SSH 주기 |
| Mac mini 운영 호스트 | [`guides/mac-mini-setup.md`](./guides/mac-mini-setup.md) | 물리 호스트 셋업 가이드 (template 버전) |
| 관측성 스택 | [`guides/monitoring-setup.md`](./guides/monitoring-setup.md) | Loki / Grafana / Prometheus / Alertmanager |
| 오브젝트 스토리지 | [`guides/storage-setup.md`](./guides/storage-setup.md) | MinIO 로컬 / NAS |
| 마이그레이션 | [`migration/README.md`](./migration/README.md) | Flyway 규칙 + 포트/어댑터 |
| 내부 작업 기록 (참고용) | [`internal/plans/`](./internal/plans/) | 과거 큰 작업 (item9 / item10 / item11) 의 상세 plan 파일 — 일반 사용자 비대상 |

---

## 이 책 다음에는?

7단계까지 한 번 흐르고 나면 template 의 전체 사용 흐름이 머릿속에 잡힙니다. 그 다음은 **본인 프로젝트의 도메인을 만들어 나가는 것** 이 자연스러운 다음 단계입니다.

진행하면서 막히는 부분이 있으면 위 "깊이 있는 참조" 의 해당 문서를 펼쳐 보세요. 모든 문서는 서로 연결돼 있으며, 어디로 가야 할지 막힌다면 이 책 목차로 다시 돌아오면 됩니다.

행운을 빕니다.
