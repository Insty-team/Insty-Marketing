"""검색 키워드 목록.

키워드는 src/keyword_generator.py로 페르소나 기반 자동 생성 후
src/keyword_validator.py로 YouTube 검증을 거쳐 여기 저장됨.
scripts/run_keyword_refresh.py로 갱신 (월 1회 수동 실행 권장).
"""

# 검증 완료된 키워드 (카테고리별)
# 형식: {"카테고리": ["keyword1", "keyword2", ...]}
KEYWORDS: dict[str, list[str]] = {
    "ai_consulting": [
        "AI consulting business solopreneur",
        "high ticket AI services freelancer",
        "AI strategy consultant business model",
        "sell AI services to businesses",
    ],
    "micro_saas": [
        "build micro SaaS with AI",
        "solo founder SaaS revenue",
        "micro SaaS side project income",
        "vibe coding SaaS MVP",
        "no code SaaS business",
    ],
    "productized_service": [
        "productized service business model",
        "DesignJoy business model breakdown",
        "unlimited service subscription business",
        "solo founder productized agency",
    ],
    "ai_agents": [
        "AI agents run my business",
        "AI agent automation business",
        "n8n AI agent workflow",
        "build AI agent team solopreneur",
        "AI employee replacement solopreneur",
    ],
    "solo_founder": [
        "solo founder million dollar exit",
        "one person business AI revenue",
        "solopreneur $10K MRR",
        "AI powered one person company",
    ],
    # === 1인 AI 비즈니스 시스템 (도구별 + 단계별) ===
    "ai_business_system": [
        # 전체 시스템 / 1인 운영
        "one person AI business full stack",
        "run entire business with AI tools",
        "solopreneur AI workflow idea to revenue",
        "AI powered one person business system",
        "build business operating system with AI",
        # AI 아이디어 발굴 + 시장조사
        "AI market research for solo founder",
        "use AI to validate business idea",
        "AI competitive analysis solopreneur",
    ],
    "ai_build_and_ship": [
        # 바이브코딩 / MVP 빌드 (도구 불문)
        "vibe coding build MVP fast",
        "build SaaS app with AI coding tools",
        "AI sub agents parallel development",
        # Claude Code
        "Claude Code build full app tutorial",
        "Claude Code sub agent workflow",
        "Claude Code one person business",
        # Cursor / Windsurf / Copilot
        "Cursor AI build app from scratch",
        "Windsurf AI coding solopreneur",
        "GitHub Copilot build MVP solo founder",
        # Replit Agent / Devin / 기타
        "Replit Agent build app no code",
        "Devin AI software engineer demo",
    ],
    "ai_content_marketing": [
        # AI 콘텐츠 파이프라인
        "AI content pipeline solopreneur",
        "automate content creation with AI",
        "AI write social media posts at scale",
        "Claude Code content automation workflow",
        # AI 마케팅 자동화
        "AI marketing automation one person business",
        "AI outreach pipeline B2B solopreneur",
        "AI cold email outreach tool",
        # GPT / ChatGPT 마케팅
        "ChatGPT content marketing workflow",
        "GPT-4 social media automation",
    ],
    "ai_sales_proposals": [
        # AI 세일즈 / 프로포절
        "AI write client proposal",
        "Claude Code sales proposal automation",
        "AI close deals solopreneur",
        "AI proposal generator freelancer",
        "land clients with AI tools solo founder",
    ],
    "multi_agent_orchestration": [
        # 멀티 에이전트 오케스트레이션 (프레임워크)
        "multi agent AI workflow tutorial",
        "CrewAI multi agent business automation",
        "AutoGen autonomous agent team tutorial",
        "LangGraph multi agent orchestration",
        "OpenAI Assistants API multi agent",
        # 노코드 에이전트 오케스트레이션
        "n8n AI agent workflow automation",
        "Make.com AI agent solopreneur",
    ],
}


def get_all_keywords() -> list[str]:
    """모든 카테고리의 키워드를 하나의 리스트로 반환."""
    return [kw for keywords in KEYWORDS.values() for kw in keywords]


def get_keywords_by_category(category: str) -> list[str]:
    """특정 카테고리의 키워드만 반환."""
    return KEYWORDS.get(category, [])


def get_categories() -> list[str]:
    """모든 카테고리 이름 반환."""
    return list(KEYWORDS.keys())
