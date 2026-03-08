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
