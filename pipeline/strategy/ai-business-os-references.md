# AI Business OS — 오픈소스 레퍼런스 가이드

> 2026-03-13 조사. 세일즈 시 "뭘 팔지" 구성할 때 참고.
> 관련 컨셉: `ai-business-os-concept.md`

---

## 추천 스택 조합

```
┌─────────────────────────────────────────┐
│           AI Business OS Stack          │
├─────────────┬───────────────────────────┤
│ 에이전트 코어  │ CrewAI or Agno            │
│ 워크플로우     │ LangGraph (점진적 자율화)   │
│ 자동화 통합   │ n8n (400+ API)            │
│ 지식 베이스   │ Dify (RAG)                │
│ 도구 연결    │ MCP 서버 생태계             │
│ CRM 모듈    │ AI CRM Agents 참조         │
│ 콘텐츠 모듈   │ Social Media Agent 참조    │
└─────────────┴───────────────────────────┘
```

---

## Tier 1: 핵심 엔진 (바로 활용 가능)

### CrewAI — 멀티 에이전트 오케스트레이션
- **Repo**: https://github.com/crewAIInc/crewAI (~44K stars)
- **예제**: https://github.com/crewAIInc/crewAI-examples
- **핵심**: 역할 기반 자율 AI 에이전트 프레임워크
- **활용**: 마케팅/세일즈/리서치/운영 에이전트를 역할로 정의하고 협업시키는 코어 엔진
- **예제 템플릿**: Lead Score Flow, Content Creator Flow, Email Auto Responder Flow 등 비즈니스 템플릿 이미 존재
- **세일즈 포인트**: "부서별 AI 에이전트를 세팅해드립니다"

### n8n — 워크플로우 자동화
- **Repo**: https://github.com/n8n-io/n8n (~150K stars)
- **핵심**: 400+ API 통합, 비주얼 노코드 + 코드 유연성
- **활용**: 고객에게 실제 납품할 자동화 파이프라인 구축 도구. SNS, 이메일, CRM, 인보이싱 등 기존 통합 활용
- **세일즈 포인트**: "코딩 없이도 관리 가능한 자동화 파이프라인"

### Dify — AI 앱 플랫폼
- **Repo**: https://github.com/langgenius/dify (~114K stars)
- **핵심**: RAG 파이프라인 + 워크플로우 빌더 + 멀티모델 지원
- **활용**: 비즈니스 지식 베이스(마크다운/텍스트) 관리, 고객 대면 챗봇/에이전트 배포
- **세일즈 포인트**: "사업 맥락을 이해하는 AI 지식 베이스 구축"

### OpenFang — Agent Operating System
- **Repo**: https://github.com/RightNow-AI/openfang (~14K stars)
- **핵심**: 30개 에이전트, 40개 채널, 38개 도구, 24/7 자율 운영. AI Business OS 컨셉과 가장 유사
- **활용**: 아키텍처 참조 — Clip(콘텐츠), Lead(데이터), Collector(인텔리전스), Predictor(예측), Browser(자동화) 구조
- **주의**: v0.3.x이므로 프로덕션은 주의 필요. 구조/컨셉 참조용

### LangGraph — 상태 기반 에이전트 그래프
- **Repo**: https://github.com/langchain-ai/langgraph (~35K stars)
- **Open Agent Platform**: https://github.com/langchain-ai/open-agent-platform
- **핵심**: 상태 관리, human-in-the-loop, 장/단기 메모리
- **활용**: 점진적 자율화(보조 → 반자동 → 자율) 구현에 최적. human-in-the-loop = co-pilot, 자율 실행 = autopilot
- **세일즈 포인트**: "처음엔 확인받고, 점차 알아서 처리하는 AI"

---

## Tier 2: 모듈별 참조

### Agno (구 Phidata) — CrewAI 대안
- **Repo**: https://github.com/agno-agi/agno (~20K stars)
- **핵심**: MCP 지원 멀티 에이전트 + 모니터링 UI + self-hosted
- **활용**: 고객 데이터 보호가 중요한 B2B에서 CrewAI 대안. 에이전트 모니터링 대시보드 제공

### AI CRM Agents — 세일즈 모듈 템플릿
- **Repo**: https://github.com/KlementMultiverse/ai-crm-agents
- **핵심**: 6개 자율 CRM 에이전트 (리드 자격, 이메일 인텔리전스, 세일즈 파이프라인, 고객 성공, 미팅 스케줄링, 분석)
- **활용**: 세일즈 파이프라인 자동화 모듈 참조. MIT 라이선스. 한국 1인 사업자 고객용 커스터마이즈 가능

### Agency Swarm — 계층적 에이전트
- **Repo**: https://github.com/VRSEN/agency-swarm (~5K stars)
- **핵심**: CEO → 팀 에이전트 위임(handoff) 구조
- **활용**: 현재 `agents/` 디렉토리의 CEO + 4개 팀 구조와 유사. HAAS(Hierarchical Autonomous Agent Swarm) 패턴 참조

### Social Media Agent — 콘텐츠 파이프라인
- **Repo**: https://github.com/langchain-ai/social-media-agent
- **핵심**: 소셜 미디어 소싱 → 큐레이션 → 스케줄링, human-in-the-loop
- **활용**: 듀얼 트랙 콘텐츠 파이프라인 (한국 서비스 + 영문 빌드인퍼블릭) 참조

### Open-KBS AI Marketing
- **Repo**: https://github.com/open-kbs/ai-marketing
- **핵심**: 국가/시장별 커스터마이즈 가능한 AI 마케팅 에이전트
- **활용**: 이미지/비디오/랜딩페이지/이메일 캠페인 생성. 한국 시장 커스터마이즈 레퍼런스

### MetaGPT — SOP 기반 협업 아키텍처
- **Repo**: https://github.com/FoundationAgents/MetaGPT (~45K stars)
- **핵심**: PM, 아키텍트, 엔지니어 역할의 멀티 에이전트. SOP 기반 협업
- **활용**: 부서별 SOP를 에이전트에 적용하는 패턴 참조

---

## Tier 3: MCP 도구 생태계

### 큐레이션 목록
- **awesome-mcp-servers**: https://github.com/punkpeye/awesome-mcp-servers (~40K stars)
- **MCP 공식 서버**: https://github.com/modelcontextprotocol/servers
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk

### 비즈니스 도구 MCP 서버

| MCP 서버 | 용도 | 고객 제공 시나리오 |
|---|---|---|
| HubSpot MCP | CRM | 리드/딜 관리 자동화 |
| Salesforce MCP | CRM/SOQL | 엔터프라이즈 CRM 연동 |
| Smartlead MCP | 이메일 마케팅 | 콜드 이메일 캠페인 |
| Metricool MCP | SNS 분석/스케줄링 | 소셜 미디어 자동 게시 |
| WhatsApp Business MCP | 메시징/CRM (244개 도구) | 고객 소통 자동화 |
| Zapier MCP | 수천 개 앱 통합 | 기존 도구 연결 |
| Odoo MCP | ERP/CRM | 통합 비즈니스 관리 |

---

## 세일즈 활용 포인트

### 고객에게 어필할 메시지
1. **"검증된 오픈소스 조합"** — 처음부터 만드는 게 아니라 44K+ stars 프레임워크 기반 → 빠르고 안정적
2. **"점진적 자율화"** — 테슬라 ADAS → FSD 비유. Phase 1은 알림만, 신뢰 쌓이면 자동화 확대
3. **"코딩 없이 관리"** — n8n 비주얼 워크플로우 + Dify 노코드 챗봇
4. **"데이터 소유권"** — self-hosted로 고객 데이터 외부 유출 없음

### 패키지별 스택 매핑

| 패키지 | 스택 | 제공 범위 |
|---|---|---|
| **Starter ₩50만** | n8n + 기본 워크플로우 2~3개 | 반복 업무 자동화 (이메일, SNS 예약) |
| **Growth ₩100만** | n8n + CrewAI 에이전트 2~3개 + Dify 지식 베이스 | 에이전트 기반 보조 (Phase 1 수준) |
| **Premium ₩150만** | Full Stack (CrewAI + LangGraph + n8n + Dify + MCP) | 점진적 자율화 파이프라인 (Phase 1→2 전환 포함) |

---

## 추가 리서치 필요 시
- [ ] OpenFang 아키텍처 deep dive (에이전트 OS 구조)
- [ ] CrewAI examples에서 비즈니스 템플릿 분석
- [ ] n8n 한국 비즈니스 도구 통합 가능성 (카카오, 네이버 등)
- [ ] Dify self-hosted 배포 비용 산정
