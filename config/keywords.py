"""검색 키워드 목록.

키워드는 src/keyword_generator.py로 페르소나 기반 자동 생성 후
src/keyword_validator.py로 YouTube 검증을 거쳐 여기 저장됨.
scripts/run_keyword_refresh.py로 갱신 (월 1회 수동 실행 권장).
"""

# 검증 완료된 키워드 (카테고리별)
# 형식: {"카테고리": ["keyword1", "keyword2", ...]}
KEYWORDS: dict[str, list[str]] = {
    "ai_tools": [
        "Best AI tools solopreneurs",
        "Top AI content creation",
        "AI writing assistants compared",
        "Generative AI art tutorial",
        "AI video editing tools",
    ],
    "automation": [
        "Zapier workflow automation tips",
        "Make.com automation tutorial",
        "Automate small business tasks",
        "Freelance workflow automation setup",
        "AI email marketing automation",
    ],
    "business_strategy": [
        "AI strategy for small business",
        "Shopify CRO optimization AI",
        "HubSpot CRM automation guide",
        "AI business model innovation",
    ],
    "productivity": [
        "AI productivity hacks for work",
        "Time blocking for focus",
        "Digital workflow optimization AI",
        "AI for meeting summaries",
    ],
    "solopreneur": [
        "Solopreneur business growth strategies",
        "Freelance business scaling tips",
        "Build a solo online business",
        "Side project management AI",
        "Small team lead productivity",
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
