# Insty AI Agent Team — OpenClaw 기반 자율 운영 시스템 설계서

> **목표**: Samwoo 없이도 Sales & Marketing 파이프라인이 24/7 자율 운영되어 **월 10명 유료 계약** 달성
> **전략**: 소상공인이 이미 모여있는 곳에서, 그들이 이해하는 언어로, 시각적 결과물을 보여준다
> **프레임워크**: OpenClaw (Multi-Agent Gateway)
> **소통 채널**: Slack `#insty` 단일 채널
> **작성일**: 2026-03-18

---

## 1. 왜 OpenClaw인가

| 기준 | OpenClaw | CrewAI | AutoGen | LangGraph |
|------|----------|--------|---------|-----------|
| 멀티 에이전트 격리 | Agent별 독립 workspace, auth, session | Role 기반 | Conversation 기반 | Graph 기반 |
| 채널 통합 | Slack, Telegram, Discord 네이티브 지원 | 별도 구현 필요 | 별도 구현 필요 | 별도 구현 필요 |
| 24/7 운영 | Gateway 데몬 + VPS | 별도 스케줄러 필요 | 별도 스케줄러 필요 | 별도 스케줄러 필요 |
| Agent간 통신 | ACP + shared memory 내장 | 내장 | 내장 | State 공유 |
| 외부 런타임 연동 | Claude Code, Codex, Gemini CLI 지원 | 제한적 | 제한적 | 제한적 |
| 프로덕션 성숙도 | GitHub 150K+ stars, 활발한 생태계 | 성숙 | 성숙 | 성숙 |

**결론**: OpenClaw는 멀티 채널 라우팅 + Agent 격리 + ACP 통신이 내장되어 있어, Slack 기반 자율 Agent 팀을 구축하기에 가장 적합.

---

## 2. 세일즈 전략 요약

> 상세 전략 및 가격 구조는 [BUSINESS_PLAN.md](./BUSINESS_PLAN.md) 참조

**핵심**: 콜드 아웃바운드 X. 고객이 이미 모여있는 곳에서 인바운드로 유입.

| 채널 | Agent | 역할 |
|------|-------|------|
| **숏폼 영상** (YouTube/Instagram) | Video Planner + Renderer | Before/After 공감 영상 |
| **커뮤니티** (네이버 카페/카카오 OC) | Community | 정보성 글 → "저요!" |
| **미끼 상품** (PDF/템플릿) | Lead Magnet | 무료 도구 → 연락처 수집 |
| **모니터링** (전 채널) | Monitor | Warm Lead 감지 |
| **육성** (DM/메시지) | Nurture | 상담 요청까지 육성 |

**금지 용어**: AI OS, 자동화, SaaS, 에이전트, 솔루션, 플랫폼
**필수 프레이밍**: "24시간 매니저", "알아서 해주는", "사장님 대신", "하루 천 원"

---

## 3. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        VPS (Always-On)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  OpenClaw Gateway                         │  │
│  │                                                           │  │
│  │  ┌─────────┐                    ┌──────────────┐         │  │
│  │  │   PM    │   sessions_send    │ Video Planner │         │  │
│  │  │ (총괄)  │◄──────────────────►│ (영상 기획)   │         │  │
│  │  │ Claude  │   sessions_send    ├──────────────┤         │  │
│  │  │ Opus    │◄──────────────────►│Video Renderer │         │  │
│  │  │         │   sessions_send    │ (영상 제작)   │         │  │
│  │  │         │◄──────────────────►├──────────────┤         │  │
│  │  │         │   sessions_send    │  Community    │         │  │
│  │  │         │◄──────────────────►│ (커뮤니티)    │         │  │
│  │  │         │   sessions_send    ├──────────────┤         │  │
│  │  │         │◄──────────────────►│ Lead Magnet   │         │  │
│  │  │         │   sessions_send    │ (미끼 상품)   │         │  │
│  │  │         │◄──────────────────►├──────────────┤         │  │
│  │  │         │   sessions_send    │  Nurture      │         │  │
│  │  │         │◄──────────────────►│ (리드 육성)   │         │  │
│  │  │         │   sessions_send    ├──────────────┤         │  │
│  │  │         │◄──────────────────►│  Monitor      │         │  │
│  │  │         │                    │ (반응 감시)   │         │  │
│  │  └────┬────┘                    └──────────────┘         │  │
│  │       │                                                   │  │
│  └───────┼───────────────────────────────────────────────────┘  │
│          │                                                      │
│  ┌───────▼───────┐  ┌────────────┐  ┌──────────────────────┐   │
│  │  Slack Channel │  │  외부 채널  │  │  Shared Workspace    │   │
│  │  #insty        │  │  YouTube   │  │  /workspace/shared/  │   │
│  │                │  │  Instagram │  │  ├─ GOALS.md         │   │
│  │                │  │  Naver Cafe│  │  ├─ STATUS.md        │   │
│  │                │  │  Kakao OC  │  │  ├─ DECISIONS.md     │   │
│  └───────────────┘  │  Gmail     │  │  ├─ leads/            │   │
│                      └────────────┘  │  ├─ content/          │   │
│                                      │  └─ reports/          │   │
│                                      └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent 정의

### 4.1 PM Agent (총괄 코디네이터)

| 항목 | 설정 |
|------|------|
| **ID** | `pm` |
| **Model** | `anthropic/claude-opus-4-6` |
| **역할** | 전체 파이프라인 총괄, 태스크 분배, 결과 종합, 의사결정 |
| **Slack** | `#insty` — Samwoo 메시지 수신 → 적절한 Agent에 라우팅 |

**핵심 책임**:
- Samwoo의 `#insty` 메시지를 수신하여 적절한 Agent에 위임
- 매일 08:00 — 전체 팀 스탠드업 실행 (각 Agent에게 상태 요청)
- 3채널 파이프라인 흐름 관리: 영상/커뮤니티/미끼 → Monitor → Nurture → 상담
- 주간 성과 보고서 생성 및 `#insty` 공유
- 긴급 상황 시 `#insty`에 @samwoo 멘션
- `GOALS.md`, `STATUS.md`, `DECISIONS.md` 유지보수

**SOUL.md (페르소나)**:
```markdown
You are the PM of Insty's Sales & Marketing team.
Your mission: achieve 10 paid contracts per month through warm inbound leads.
You coordinate 6 specialist agents. You NEVER do specialist work yourself.
You delegate, track, aggregate, and escalate.

Our strategy is INBOUND ONLY — no cold emails, no cold calls.
We attract leads through: (1) short-form videos, (2) community engagement, (3) free lead magnets.
When Monitor detects a warm lead (comment, DM, download), immediately route to Nurture.
When a lead requests consultation, immediately @samwoo in #insty.

All communication happens in #insty.
Daily standup at 08:00 KST. Weekly report every Monday 09:00 KST.
Language: Korean for Slack, English for shared docs.
```

---

### 4.2 Video Planner Agent (숏폼 영상 기획)

| 항목 | 설정 |
|------|------|
| **ID** | `video-planner` |
| **Model** | `google/gemini-2.0-flash` (트렌드 리서치) + `openai/gpt-4o` (스크립트) |
| **역할** | 소상공인 Pain Point 기반 숏폼 영상 기획 |
| **Slack** | `#insty` |

**채널 1: 숏폼 영상** — 가장 폭발적인 유입 채널

**핵심 책임**:
- 주 3~5회 — 업종별 pain point 기반 영상 주제 선정
- 트렌드 리서치: "아프니까 사장이다" 카페, 자영업 커뮤니티, 네이버 검색 키워드
- **Before/After 구조** 스크립트 작성:
  - Before: 바쁜 점심에 예약 전화 받느라 주문 밀리는 사장님
  - After: AI가 전화 대신 받고 카톡으로 예약 확정하는 화면
- **절대 금지 용어**: "AI OS", "자동화 시스템", "SaaS", "에이전트"
- **필수 용어**: "24시간 일하는 매니저", "사장님 퇴근 후에도 알아서", "월 3만원으로"
- 산출물을 `content/videos/scripts/YYYY-MM-DD.json`에 저장
- 완료 시 Video Renderer에 `sessions_send`

**산출물 스키마**:
```json
{
  "topic": "바쁜 점심시간, 예약 전화 놓치지 않는 법",
  "industry": "네일샵",
  "hook": "사장님, 아직도 예약 전화 직접 받으세요?",
  "script": "Before/After 풀 스크립트...",
  "tts_text": "TTS용 텍스트 (말투 최적화)...",
  "image_prompts": [
    "Illustration: stressed nail salon owner juggling phone calls during busy hours",
    "Illustration: calm salon owner checking phone — AI handled all bookings automatically"
  ],
  "cta": "프로필 링크에서 무료 체험 →",
  "subtitle_segments": [
    { "text": "사장님, 아직도", "duration_hint": "1.5s" },
    { "text": "예약 전화 직접 받으세요?", "duration_hint": "2s" },
    { "text": "이렇게 바꿔보세요", "duration_hint": "1.5s" }
  ],
  "hashtags": ["#소상공인", "#네일샵", "#예약관리", "#자영업꿀팁"],
  "platform": ["youtube_shorts", "instagram_reels"]
}
```

**SOUL.md**:
```markdown
You plan short-form videos for small business owners.
You NEVER use tech jargon. You speak the language of 사장님s.

FORBIDDEN WORDS: AI OS, 자동화, SaaS, 에이전트, 시스템, 솔루션, 플랫폼
REQUIRED FRAMING: "24시간 매니저", "알아서 해주는", "사장님 대신", "월 3만원"

Each video is a Before/After story:
- Before: a specific pain moment every 사장님 has experienced
- After: the magical "oh, this exists?" moment
- Hook in first 3 seconds — ask a question they MUST answer "yes" to
- Max 60 seconds. End with simple CTA (프로필 링크).
- Tone: 동네 언니/오빠가 꿀팁 알려주는 느낌

Image style: warm illustration, NOT corporate. Think 카카오프렌즈 감성.
```

**도구 허용**: `exec`(웹 검색), `read`, `write`(content/videos/scripts)
**도구 차단**: `sessions_spawn`, `edit`, Gmail 접근

---

### 4.3 Video Renderer Agent (영상 제작)

| 항목 | 설정 |
|------|------|
| **ID** | `video-renderer` |
| **Model** | `anthropic/claude-haiku-4-5` (경량 — 실행 중심) |
| **역할** | Planner 산출물을 받아 API 호출 + 영상 합성 |
| **Slack** | `#insty` |

**핵심 책임**:
- Video Planner 산출물 수신 후 자동 실행
- 제작 파이프라인:
  1. **TTS 생성**: ElevenLabs API (`with_timestamps`) → 음성.mp3 + 타임스탬프.json
  2. **자막 생성**: 타임스탬프.json → ASS 자막 파일 (단어별 싱크, 스타일링)
  3. **이미지 생성**: DALL-E 3 API → 장면별 일러스트.png
  4. **영상 합성**: ffmpeg — 일러스트 + 음성 + ASS 자막 → 최종.mp4
- 결과물을 `content/videos/output/YYYY-MM-DD/`에 저장
- PM에게 완료 보고

**자막 스타일** (ASS 포맷):
```
┌─────────────────────┐
│                     │
│   [Before/After     │
│    일러스트 이미지]   │
│                     │
│   ┌───────────────┐ │
│   │ 사장님, 아직도 │ │
│   │ 예약 전화     │ │
│   │ 직접 받으세요? │ │
│   └───────────────┘ │
│                     │
└─────────────────────┘
```
- 화면 하단~중앙, 2~3줄씩 음성 타이밍에 맞춰 표시
- Bold + 외곽선(Outline=2) + 가독성 우선

**도구 허용**: `exec`(TTS API, DALL-E API, ffmpeg), `read`, `write`(content/videos)
**도구 차단**: `sessions_spawn`, `edit`, Gmail 접근

---

### 4.4 Community Agent (커뮤니티 침투)

| 항목 | 설정 |
|------|------|
| **ID** | `community` |
| **Model** | `anthropic/claude-sonnet-4-6` (자연스러운 한국어 + 맥락 이해) |
| **역할** | 자영업 커뮤니티에서 정보성 글로 신뢰 구축 → Warm Lead 발굴 |
| **Slack** | `#insty` |

**채널 2: 커뮤니티 침투** — 가장 전환율 높은 채널

**타겟 커뮤니티**:

| 커뮤니티 | 규모 | 접근법 |
|---------|------|--------|
| 네이버 카페 "아프니까 사장이다" | 100만+ 회원 | 정보성 글 |
| 네이버 카페 "자영업의 모든것" | 수십만 회원 | 경험담 공유 |
| 카카오톡 오픈채팅 (업종별) | 지역별 수백명 | 실시간 도움 |
| 네이버 카페 (업종별: 네일, 카페 등) | 업종별 수만명 | 전문 조언 |

**핵심 책임**:
- 매일 — 타겟 커뮤니티 인기 글/고민 글 수집 + 트렌드 분석
- 주 3~5회 — **정보성 글 초안 작성** (Samwoo가 검토 후 직접 게시)
- 댓글/반응 모니터링 → "저요!", "어떻게 하는 건가요?" 감지
- Warm Lead 정보를 `leads/warm/YYYY-MM-DD.json`에 기록
- PM에게 Hot Lead 즉시 보고

**글 작성 원칙 — 대놓고 홍보 = 강퇴**:
```markdown
✅ 좋은 예:
"요즘 노쇼 때문에 스트레스받아서, 예약 확인 문자 자동으로 쏘는 세팅을
해봤는데 노쇼가 반으로 줄었어요. 혹시 필요하신 분 계시면 설정하는 방법
공유해 드릴게요."
→ 댓글: "저요!", "어떻게 하나요?"
→ 이들이 가장 확실한 잠재 고객 (Warm Lead)

❌ 나쁜 예:
"AI 예약 관리 시스템 Insty를 소개합니다! 지금 가입하세요!"
→ 즉시 강퇴 + 신고
```

**산출물 스키마**:
```json
{
  "type": "community_post",
  "platform": "naver_cafe",
  "cafe_name": "아프니까 사장이다",
  "category": "경험공유",
  "title": "노쇼 절반으로 줄인 후기 (예약 확인 자동화)",
  "body": "글 본문...",
  "pain_point": "노쇼",
  "industry": "네일샵",
  "hook_for_replies": "필요하신 분 계시면 설정 방법 공유해 드릴게요",
  "expected_warm_leads": 5
}
```

**SOUL.md**:
```markdown
You write community posts that feel like genuine 사장님 경험담.
You are NOT selling. You are a fellow business owner sharing helpful tips.
NEVER mention Insty, AI OS, or any product name in posts.
NEVER use promotional language. You will get banned immediately.

Your posts should:
1. Start with a relatable pain point ("저도 노쇼 때문에...")
2. Share a specific, practical solution you "tried"
3. End with an open offer to share more details
4. Be written in casual 반말 or friendly 존댓말 matching the cafe's tone

Goal: generate "저요!" comments. These are your warm leads.
When you detect interest, prepare a DM template for Samwoo to send.
```

**도구 허용**: `exec`(웹 크롤링 스크립트), `read`, `write`(content/community, leads/warm)
**도구 차단**: `sessions_spawn`, `edit`, Gmail 접근

---

### 4.5 Lead Magnet Agent (무료 미끼 상품)

| 항목 | 설정 |
|------|------|
| **ID** | `lead-magnet` |
| **Model** | `anthropic/claude-sonnet-4-6` (콘텐츠 품질 중요) |
| **역할** | 소상공인의 작은 문제를 해결하는 무료 도구/템플릿 제작 |
| **Slack** | `#insty` |

**채널 3: 미끼 상품** — 연락처 수집 + 신뢰 구축

**핵심 아이디어**: 처음부터 전체 시스템을 팔면 허들이 높다. 작은 무료 도구로 "아, 이거 편하네" 체험을 시키고, 자연스럽게 "전체 자동화도 됩니다"로 연결.

**미끼 상품 라인업**:

| 미끼 상품 | 업종 | 포맷 | 배포 채널 |
|----------|------|------|----------|
| 컴플레인 응대 카톡 매뉴얼 | 식당/카페 | PDF | 커뮤니티, 숏폼 |
| 엑셀 초간단 원가 계산기 | 베이커리 | Excel | 커뮤니티 |
| 예약 노쇼 방지 문자 템플릿 | 네일샵/뷰티 | Notion | 숏폼 CTA |
| 인스타 홍보 캡션 100개 모음 | 전 업종 | PDF | 커뮤니티, 숏폼 |
| 월 매출 자동 정산 시트 | 전 업종 | Google Sheet | 커뮤니티 |

**핵심 책임**:
- 월 2~3회 — 업종별 미끼 상품 신규 제작 또는 업데이트
- Community Agent/Video Planner와 협업하여 배포 전략 수립
- 다운로드 시 연락처(이메일 또는 카톡) 수집 → `leads/magnet/`에 기록
- PM에게 다운로드 현황 보고

**연결 시나리오**:
```
무료 템플릿 다운로드
  → 3일 후: "템플릿 잘 쓰고 계신가요? 혹시 불편한 점 있으면 말씀해주세요"
  → 7일 후: "이런 귀찮은 작업들을 아예 100% 자동화해주는 서비스가 있는데,
             초기 세팅을 도와드리고 있습니다. 관심 있으시면 편하게 연락주세요"
  → 이 시퀀스는 Nurture Agent가 담당
```

**SOUL.md**:
```markdown
You create free tools and templates that solve one small, specific problem
for small business owners. Each lead magnet must:
1. Solve a real, daily pain point (not theoretical)
2. Be immediately usable without explanation
3. Make the user think "와, 이거 편하다"
4. Naturally lead to wanting more automation

Quality matters — if the free thing is bad, they won't trust the paid service.
Format: PDF, Excel, Google Sheet, Notion template.
Language: Korean, casual and practical.
NEVER include Insty branding prominently — subtle footer only.
```

**도구 허용**: `exec`(문서 생성 스크립트), `read`, `write`(content/lead-magnets)
**도구 차단**: `sessions_spawn`, `edit`, Gmail 접근

---

### 4.6 Nurture Agent (리드 육성)

| 항목 | 설정 |
|------|------|
| **ID** | `nurture` |
| **Model** | `anthropic/claude-sonnet-4-6` (개인화된 메시지 품질) |
| **역할** | Warm Lead를 상담 요청까지 육성하는 메시지 작성 |
| **Slack** | `#insty` |

**모든 채널의 Warm Lead가 여기로 모인다.**

```
숏폼 댓글 "이거 어떻게 하나요?" ──┐
커뮤니티 "저요!" 댓글 ────────────┤──→ Nurture Agent ──→ Samwoo 상담
미끼 상품 다운로드 ───────────────┘
```

**핵심 책임**:
- Monitor Agent로부터 Warm Lead 수신 → 맥락 파악
- **리드 소스별 맞춤 메시지** 초안 작성:
  - 숏폼 댓글 → DM: "영상 봐주셔서 감사해요! 혹시 OO업종이신가요? 상황에 맞는 세팅 방법 알려드릴게요"
  - 커뮤니티 "저요!" → DM: "안녕하세요! 글에서 말씀드린 세팅 방법인데요, [간단 가이드]. 혹시 더 궁금한 거 있으시면 편하게 물어보세요"
  - 미끼 다운로드 → 후속 메시지 시퀀스 (3일/7일/14일)
- 리드 상태 관리: `leads/nurturing/` (상태: contacted / engaged / consultation_requested / converted)
- 상담 요청 감지 시 **즉시 PM에게 보고 → @samwoo 멘션**

**메시지 톤 가이드**:
```markdown
✅ "사장님, 글 잘 봤어요! 저도 처음에 세팅 헤맸는데, 혹시 어떤 업종이신지 알려주시면
   딱 맞는 방법 알려드릴게요 😊"

❌ "안녕하세요, Insty AI 솔루션입니다. 귀사의 업무 자동화를 위한 상담을 제안드립니다."
```

**육성 시퀀스 (미끼 다운로드 기준)**:
```
Day 0:  다운로드 감사 + 사용법 팁 1개
Day 3:  "잘 쓰고 계신가요?" + 활용 팁 추가
Day 7:  "이런 것도 자동화 가능한데, 관심 있으시면 무료로 보여드릴게요"
Day 14: "이번 주에 무료 세팅 이벤트 하고 있어요" (마지막 넛지)
```

**SOUL.md**:
```markdown
You nurture warm leads into consultation requests.
You write messages as if you're a helpful friend, not a salesperson.

RULES:
- Match the tone of how the lead first engaged (casual reply → casual DM)
- NEVER push too hard. One gentle nudge per touchpoint.
- Always provide value first, ask for nothing initially.
- Personalize: mention their industry, their specific pain point.
- When they ask "how much?" or "can you set this up?" → that's consultation-ready.
  Immediately flag to PM for @samwoo handoff.

Your job ends when the lead requests a consultation.
Samwoo handles the actual sales conversation.
```

**도구 허용**: `read`, `write`(leads/nurturing, content/messages), `exec`(메시지 발송 스크립트)
**도구 차단**: `sessions_spawn`, `edit`

---

### 4.7 Monitor Agent (반응 감시)

| 항목 | 설정 |
|------|------|
| **ID** | `monitor` |
| **Model** | `anthropic/claude-haiku-4-5` (경량, 비용 최소화) |
| **역할** | 모든 채널의 반응을 감시하고 Warm Lead를 감지 |
| **Slack** | `#insty` |

**이전**: Gmail만 감시
**현재**: 모든 인바운드 채널 감시

**핵심 책임**:
- **15분 간격** 모니터링:

| 채널 | 감시 대상 | Warm Lead 신호 |
|------|----------|---------------|
| YouTube | 숏폼 댓글 | "이거 어떻게 하나요?", "우리 가게도 되나요?" |
| Instagram | 릴스 댓글 + DM | "문의드려요", "비용이 얼마예요?" |
| Naver Cafe | 게시글 댓글 | "저요!", "방법 알려주세요" |
| Kakao OC | 오픈채팅 언급 | 직접 문의 |
| Gmail | instyhelp@gmail.com | 이메일 답장 |

- Warm Lead 감지 시 즉시:
  1. `leads/warm/YYYY-MM-DD.json`에 기록 (소스, 내용, 업종 추정)
  2. Nurture Agent에 `sessions_send` → 맞춤 응답 초안 요청
  3. Hot Lead (직접 상담 요청)인 경우 `#insty`에 @samwoo 멘션

- 채널별 성과 메트릭 수집:
  - 영상 조회수, 댓글 수, 프로필 클릭 수
  - 커뮤니티 글 조회수, 댓글 수
  - 미끼 상품 다운로드 수

**도구 허용**: `exec`(API 크롤링 스크립트), `read`, `write`(leads/warm, reports/metrics)
**도구 차단**: `sessions_spawn`, `edit`, 발송 권한 없음

---

## 5. OpenClaw Gateway 설정

```json5
// ~/.openclaw/config.json5
{
  // === Agent 정의 ===
  agents: {
    list: [
      {
        id: "pm",
        workspace: "~/.openclaw/workspaces/pm",
        model: "anthropic/claude-opus-4-6",
        sandbox: { mode: "all", scope: "agent" },
        tools: {
          allow: ["read", "write", "edit", "exec", "sessions_send"],
          deny: ["sessions_spawn"]
        }
      },
      {
        id: "video-planner",
        workspace: "~/.openclaw/workspaces/video-planner",
        model: "google/gemini-2.0-flash",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      },
      {
        id: "video-renderer",
        workspace: "~/.openclaw/workspaces/video-renderer",
        model: "anthropic/claude-haiku-4-5",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      },
      {
        id: "community",
        workspace: "~/.openclaw/workspaces/community",
        model: "anthropic/claude-sonnet-4-6",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      },
      {
        id: "lead-magnet",
        workspace: "~/.openclaw/workspaces/lead-magnet",
        model: "anthropic/claude-sonnet-4-6",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      },
      {
        id: "nurture",
        workspace: "~/.openclaw/workspaces/nurture",
        model: "anthropic/claude-sonnet-4-6",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      },
      {
        id: "monitor",
        workspace: "~/.openclaw/workspaces/monitor",
        model: "anthropic/claude-haiku-4-5",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["sessions_spawn", "edit"]
        }
      }
    ]
  },

  // === Agent간 통신 허용 ===
  tools: {
    agentToAgent: {
      enabled: true,
      allowlist: [
        { from: "pm", to: "*" },                          // PM은 모든 Agent에 메시지 가능
        { from: "video-planner", to: "pm" },               // 기획 완료 보고
        { from: "video-planner", to: "video-renderer" },   // 렌더링 트리거
        { from: "video-renderer", to: "pm" },              // 제작 완료 보고
        { from: "community", to: "pm" },                   // Warm Lead 보고
        { from: "lead-magnet", to: "pm" },                 // 미끼 상품 완료 보고
        { from: "monitor", to: "pm" },                     // 리드 감지 보고
        { from: "monitor", to: "nurture" },                // Warm Lead → 육성 트리거
        { from: "nurture", to: "pm" }                      // 상담 요청 감지 → 에스컬레이션
      ]
    }
  },

  // === Slack 채널 바인딩 — 단일 채널 ===
  bindings: [
    {
      agentId: "pm",
      match: { channel: "slack", peer: { kind: "channel", id: "#insty" } }
    },
    {
      agentId: "pm",
      match: { channel: "slack", peer: { kind: "direct", id: "samwoo" } }
    }
  ],

  // === 스케줄러 (cron 기반 자동 실행) ===
  schedules: [
    // 일간
    { agentId: "pm",             cron: "0 8 * * *",      task: "Daily standup: request status from all agents, compile report to #insty" },
    { agentId: "community",      cron: "0 9 * * *",      task: "Scan target communities for trending pain points and engagement opportunities" },
    { agentId: "monitor",        cron: "*/15 * * * *",   task: "Check all channels (YouTube, Instagram, Naver, Kakao, Gmail) for new warm leads" },
    { agentId: "pm",             cron: "0 18 * * *",     task: "Evening standup: compile daily metrics and post summary to #insty" },

    // 주간
    { agentId: "video-planner",  cron: "0 10 * * 1,3,5", task: "Research pain points and create Before/After video script for target industry" },
    { agentId: "community",      cron: "0 11 * * 2,4",   task: "Draft community posts based on trending pain points" },
    { agentId: "lead-magnet",    cron: "0 10 * * 2",     task: "Create or update one lead magnet template for target industry" },
    { agentId: "pm",             cron: "0 9 * * 1",      task: "Generate weekly performance report with channel-by-channel metrics" },

    // 육성 시퀀스 (매일)
    { agentId: "nurture",        cron: "0 10 * * *",     task: "Process nurture sequences: send Day 3/7/14 follow-ups for active leads" }
  ]
}
```

---

## 6. Shared Workspace 구조

```
/workspace/shared/
├── GOALS.md                    # 팀 OKR (월 10명 계약 목표)
├── STATUS.md                   # 실시간 파이프라인 상태
├── DECISIONS.md                # 의사결정 로그 (append-only)
│
├── leads/                      # 리드 데이터
│   ├── warm/                   # Monitor가 감지한 Warm Lead
│   │   └── 2026-03-18.json    #   {소스, 채널, 내용, 업종, 온도}
│   ├── magnet/                 # 미끼 상품 다운로드 리드
│   │   └── 2026-03-18.json    #   {이름, 연락처, 다운로드 항목}
│   ├── nurturing/              # 육성 중인 리드 (상태 관리)
│   │   └── lead-001.json      #   {상태, 시퀀스 단계, 다음 액션}
│   └── converted/              # 상담 요청 → Samwoo 핸드오프
│
├── content/                    # 콘텐츠 자산
│   ├── videos/
│   │   ├── scripts/            # Video Planner 산출물 (JSON)
│   │   └── output/             # Video Renderer 최종 영상 (MP4)
│   ├── community/
│   │   ├── posts/              # Community Agent 게시글 초안
│   │   └── responses/          # DM/댓글 응답 템플릿
│   ├── lead-magnets/
│   │   ├── templates/          # 미끼 상품 원본 (PDF, Excel 등)
│   │   └── landing/            # 다운로드 페이지 콘텐츠
│   └── messages/
│       └── nurture-sequences/  # 육성 메시지 시퀀스 템플릿
│
└── reports/
    ├── daily/                  # 일간 보고
    ├── weekly/                 # 주간 보고
    └── metrics/                # 채널별 성과 메트릭
```

---

## 7. 데이터 흐름 (파이프라인)

### 7.1 채널 1 — 숏폼 영상 파이프라인

```
              주 3~5회 (월/수/금 10:00)
                       │
          ┌────────────▼────────────┐
          │     Video Planner       │
          │  커뮤니티 Pain Point     │
          │  → Before/After 기획    │
          │  → 스크립트 + 프롬프트   │
          └────────────┬────────────┘
                       │ sessions_send → Video Renderer
          ┌────────────▼────────────┐
          │     Video Renderer      │
          │  TTS(+timestamps)       │
          │  → ASS 자막 생성        │
          │  → DALL-E 일러스트      │
          │  → ffmpeg 합성          │
          └────────────┬────────────┘
                       │ PM → Samwoo 검토 → 업로드
                       ▼
          YouTube Shorts / Instagram Reels
                       │
                       │ 댓글: "이거 어떻게 하나요?"
                       ▼
          ┌────────────────────────┐
          │  Monitor (15분 감시)    │ → Warm Lead 감지
          └────────────┬───────────┘
                       │ sessions_send → Nurture
                       ▼
          ┌────────────────────────┐
          │  Nurture Agent          │ → DM 초안 작성
          └────────────┬───────────┘
                       │ 상담 요청 시
                       ▼
              @samwoo → 직접 상담
```

### 7.2 채널 2 — 커뮤니티 파이프라인

```
              주 2~3회 (화/목 11:00)
                       │
          ┌────────────▼────────────┐
          │    Community Agent      │
          │  트렌딩 고민 수집        │
          │  → 정보성 글 초안 작성   │
          │  "노쇼 절반 줄인 후기"   │
          └────────────┬────────────┘
                       │ PM → Samwoo 검토 → 직접 게시
                       ▼
          네이버 카페 / 카카오 오픈채팅
                       │
                       │ 댓글: "저요!", "방법 알려주세요"
                       ▼
          ┌────────────────────────┐
          │  Monitor (15분 감시)    │ → Warm Lead 감지
          └────────────┬───────────┘
                       │ sessions_send → Nurture
                       ▼
          ┌────────────────────────┐
          │  Nurture Agent          │
          │  "안녕하세요! 세팅 방법  │
          │   알려드릴게요" DM 초안  │
          └────────────┬───────────┘
                       │ 상담 요청 시
                       ▼
              @samwoo → 무료 상담/데모
```

### 7.3 채널 3 — 미끼 상품 파이프라인

```
              월 2~3회 (화 10:00)
                       │
          ┌────────────▼────────────┐
          │   Lead Magnet Agent     │
          │  업종별 무료 도구 제작    │
          │  "컴플레인 응대 매뉴얼"  │
          │  "노쇼 방지 문자 템플릿"  │
          └────────────┬────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
      커뮤니티 글에서 배포    숏폼 CTA로 배포
      "무료로 드릴게요"       "프로필 링크"
                       │
                       ▼ 다운로드 (연락처 수집)
          ┌────────────────────────┐
          │  Monitor               │ → 다운로드 감지
          └────────────┬───────────┘
                       │ sessions_send → Nurture
                       ▼
          ┌────────────────────────┐
          │  Nurture Agent          │
          │  Day 0: 감사 + 사용팁   │
          │  Day 3: "잘 쓰고 계세요?" │
          │  Day 7: "전체 자동화도   │
          │         가능합니다"     │
          │  Day 14: 마지막 넛지     │
          └────────────┬───────────┘
                       │ "비용이 얼마예요?"
                       ▼
              @samwoo → 세팅 상담
```

### 7.4 전체 퍼널 요약

```
       ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
       │  숏폼 영상   │   │  커뮤니티    │   │  미끼 상품   │
       │  (인지/공감)  │   │  (신뢰/발견) │   │  (체험/연결) │
       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
              │                 │                  │
              └────────┬────────┴──────────────────┘
                       │
              ┌────────▼────────┐
              │    Monitor      │  ← 모든 채널 반응 감시
              │  (Warm Lead     │
              │   감지 & 분류)  │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │    Nurture      │  ← 맞춤 메시지로 육성
              │  (관계 구축 →   │
              │   상담 요청 유도)│
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   @samwoo       │  ← 사람이 클로징
              │  (상담 → 계약)  │
              └─────────────────┘
```

---

## 8. Slack 채널 설계

### 단일 채널: `#insty`

| 구분 | 설명 |
|------|------|
| **채널** | `#insty` — 모든 운영이 이루어지는 단일 채널 |
| **라우팅** | Samwoo 메시지 → PM Agent 수신 → 적절한 Agent에 위임 |
| **보고** | 모든 Agent 결과가 PM을 통해 `#insty`에 보고 |
| **긴급 알림** | @samwoo 멘션으로 구분 (상담 요청, 에러, 장애) |

**Samwoo 개입 포인트** (최소화):

| 개입 | 빈도 | 행동 |
|------|------|------|
| 숏폼 검토 → 업로드 | 주 3~5회 | 영상 확인 후 YouTube/Instagram 업로드 |
| 커뮤니티 글 검토 → 게시 | 주 2~3회 | 초안 확인 후 직접 게시 (계정 보호) |
| Warm Lead 상담 | 발생 시 | @samwoo 멘션 → DM/전화 상담 |
| 주간 보고 검토 | 주 1회 | 전략 조정 |

**사용 예시**:
```
[Video Renderer]: 영상 완료 — "네일샵 사장님, 예약 전화 이제 그만 받으세요"
  → Samwoo: 확인 → YouTube + Instagram 업로드

[Community Agent]: 커뮤니티 글 초안 — "노쇼 절반으로 줄인 후기 (네일샵)"
  → Samwoo: 수정 → "아프니까 사장이다" 카페에 직접 게시

[Monitor]: 🔥 @samwoo Warm Lead 감지!
  채널: 네이버 카페 댓글 / 업종: 베이커리 / 내용: "저도 이거 해보고 싶어요!"
  → Nurture Agent가 DM 초안 작성 중...

[Nurture]: DM 초안 준비:
  "안녕하세요! 베이커리 하시는군요 😊 말씀하신 주문 자동화 세팅 방법인데요..."
  → Samwoo: 확인 → DM 발송
```

---

## 9. 비용 추정 (월간)

| 항목 | 비용 | 비고 |
|------|------|------|
| **VPS** | $10~20/월 | DigitalOcean Droplet (2 vCPU, 4GB) |
| **Claude Opus** (PM) | ~$30/월 | 조율 + 의사결정 |
| **Claude Sonnet** (Community, Lead Magnet, Nurture) | ~$25/월 | 콘텐츠 작성 + 육성 |
| **Claude Haiku** (Monitor, Video Renderer) | ~$5/월 | 감시 + 렌더링 |
| **Gemini Flash** (Video Planner) | ~$3/월 | 트렌드 리서치 |
| **OpenAI** (영상) | ~$20/월 | GPT-4o (스크립트) + DALL-E 3 |
| **ElevenLabs** (TTS) | $22/월 | 영상 내레이션 + 타임스탬프 |
| **합계** | **~$115~125/월** | **₩15~16만원** |

---

## 10. 안전장치 & 거버넌스

### 10.1 에스컬레이션 정책
```
Level 1: Agent가 자체 해결 (재시도, 대체 경로)
Level 2: PM Agent에게 보고 → PM이 다른 Agent에 재위임
Level 3: #insty에 @samwoo 멘션 → 사람 개입
```

**Level 3 트리거 조건**:
- Warm Lead 상담 요청 (Hot Lead)
- Agent 에러 3회 연속 실패
- 커뮤니티 글 게시 전 검토 필요 (항상)
- API 비용이 일일 한도 초과

### 10.2 무한 루프 방지
- Specialist Agent는 `sessions_spawn` 차단 → 재귀 위임 불가
- PM의 `sessions_send`에 max-depth 1 적용
- 각 Agent 실행에 타임아웃 설정 (5분, Video Renderer는 15분)

### 10.3 비용 제어
- 일일 API 호출 한도 설정 (Agent별)
- PM Agent가 매일 비용 집계 → 한도 80% 초과 시 알림
- Specialist Agent는 stateless 운영 → 불필요한 컨텍스트 누적 방지

### 10.4 커뮤니티 안전
- **커뮤니티 글은 반드시 Samwoo 검토 후 수동 게시** (강퇴 방지)
- 글 톤/내용 가이드라인 위반 시 PM이 차단
- 동일 카페에 하루 1건 이상 게시 금지
- 게시 후 24시간 내 반응 모니터링 필수

### 10.5 데이터 무결성
- `DECISIONS.md` — append-only (덮어쓰기 금지)
- 리드 데이터 — JSON Schema 검증
- 육성 시퀀스 — 중복 발송 방지 (상태 체크)
- 영상 스크립트 — 금지 용어 자동 필터링

---

## 11. 구현 로드맵

### Phase 1: 기반 구축 (1주)
- [ ] VPS 세팅 + OpenClaw Gateway 설치
- [ ] Slack 워크스페이스 + `#insty` 채널 생성
- [ ] Shared workspace 디렉토리 구조 생성
- [ ] PM Agent 설정 + Slack 바인딩 테스트
- [ ] 타겟 커뮤니티 가입 + 계정 준비 (네이버 카페, 카카오 OC)

### Phase 2: 숏폼 파이프라인 (1주)
- [ ] Video Planner Agent 구현 (Before/After 스크립트 생성)
- [ ] Video Renderer Agent 구현 (TTS + 자막 + 이미지 + ffmpeg)
- [ ] ElevenLabs `with_timestamps` + ASS 자막 파이프라인
- [ ] 첫 5개 영상 제작 + YouTube/Instagram 업로드
- [ ] Monitor Agent 구현 (YouTube/Instagram 댓글 감시)

### Phase 3: 커뮤니티 + 미끼 (1주)
- [ ] Community Agent 구현 (카페 트렌드 수집 + 글 초안)
- [ ] Lead Magnet Agent 구현 (첫 3개 미끼 상품 제작)
- [ ] 미끼 상품 랜딩페이지 + 다운로드 트래킹
- [ ] 커뮤니티 첫 게시 + 반응 모니터링

### Phase 4: 육성 파이프라인 (3~5일)
- [ ] Nurture Agent 구현 (리드별 맞춤 메시지 + 시퀀스)
- [ ] Monitor ↔ Nurture `sessions_send` 통신 테스트
- [ ] 육성 시퀀스 Day 0/3/7/14 메시지 템플릿 세팅
- [ ] 에스컬레이션 정책 적용 (상담 요청 → @samwoo)

### Phase 5: 자동화 & 최적화 (지속)
- [ ] 숏폼 성과 기반 주제/톤 A/B 테스트
- [ ] 커뮤니티 글 유형별 전환율 분석
- [ ] 미끼 상품 다운로드 → 상담 전환율 추적
- [ ] 채널별 CAC(고객 획득 비용) 비교 → 고효율 채널 집중
- [ ] 새 업종/커뮤니티 타겟 확장

---

## 12. 성공 지표 (KPI)

### 콘텐츠 지표

| 지표 | 목표 | 측정 주기 |
|------|------|----------|
| 숏폼 영상 제작 | 주 3~5개 | 주간 |
| 영상 평균 조회수 | 1,000+ | 주간 |
| 커뮤니티 글 게시 | 주 2~3건 | 주간 |
| 미끼 상품 다운로드 | 월 50+ | 월간 |

### 리드 지표

| 지표 | 목표 | 측정 주기 |
|------|------|----------|
| Warm Lead 유입 | 주 10~15건 | 주간 |
| Lead → 상담 전환율 | 30%+ | 주간 |
| 상담 → 계약 전환율 | 30%+ | 월간 |

### 비즈니스 지표

| 지표 | 현재 | 목표 | 측정 주기 |
|------|------|------|----------|
| 상담 건수 | - | 월 30~40건 | 월간 |
| **유료 계약** | **0** | **월 10명** | **월간** |
| 채널별 CAC | - | 측정 시작 | 월간 |
| Samwoo 개입 시간 | 높음 | **주 5~7시간** | 주간 |

> **참고**: Samwoo 개입 시간이 이전 설계(주 2~3시간)보다 늘어남.
> 인바운드는 콘텐츠 검토 + 수동 게시 + 상담이 필요하기 때문.
> 하지만 이 시간은 **직접적으로 매출을 만드는 활동**이므로 가치가 다름.

---

## 13. 참고 자료

- [OpenClaw 공식 문서 — Multi-Agent Routing](https://docs.openclaw.ai/concepts/multi-agent)
- [OpenClaw ACP Agents 설정](https://docs.openclaw.ai/tools/acp-agents)
- [Multi-Agent Team Use Case (GitHub)](https://github.com/hesamsheikh/awesome-openclaw-usecases/blob/main/usecases/multi-agent-team.md)
- [OpenClaw Multi-Agent Coordination & Governance](https://lumadock.com/tutorials/openclaw-multi-agent-coordination-governance)
- [ElevenLabs Timestamps API](https://elevenlabs.io/docs/api-reference/text-to-speech#with-timestamps)
