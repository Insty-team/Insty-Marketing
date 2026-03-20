# Round 4: 마이크로 도구 팩토리

> 작성일: 2026-03-20 (v1)
> 참고: [Round 3](./round3-execution-plan.md) | [Round 2](./round2-vision-connection.md) | [Round 1](./round1-time-income-design.md)
> 핵심 가설: Pain point를 대량 수집하고, 각각을 해결하는 마이크로 웹 도구를 자동 생성하면, 100개 중 5-10개가 살아남아 패시브 인컴을 만든다.

---

## 0. 왜 이 접근인가

Round 3의 3트랙 (한국 대행 + 글로벌 대행 + 콘텐츠)은 본질적으로 **Sam의 시간 = 돈** 구조다.
대행은 건당 수입이고, 콘텐츠는 쌓이지만 수익화까지 6개월 이상 걸린다.

마이크로 도구 팩토리는 다른 차원의 게임이다:

```
대행:    Sam 1시간 → 돈 1만원 (직접 비례)
도구:    Sam 2시간 → 도구 1개 → 0원 or 월 5만원 x 영원 (비선형)
```

AirFryerCalculator.com은 입력 필드 3개짜리 단일 페이지로 월 18,000 오가닉 방문자를 만든다.
TireSize.com은 타이어 사이즈 계산기 하나로 전체 트래픽의 1/3을 끌어온다.
이런 도구는 만든 뒤 거의 손대지 않아도 된다. **진정한 패시브 인컴**.

포인트는 빨리 만드는 게 아니다. **pain point를 해결하는 UX를 설계하는 것**이 핵심이다.
그리고 그 UX 설계마저 AI가 가설을 세우고, 시장이 검증한다. Sam은 감독만 하면 된다.

---

## 1. 마이크로 도구 팩토리 파이프라인 상세 설계

### Step 1: Pain Point 수집 (자동)

#### 수집 채널

| 채널 | 언어 | 수집 방법 | 비용 | 일일 수집 목표 |
|------|:----:|----------|:----:|:-------------:|
| Reddit | EN | Reddit API (무료, 100 req/min, 월 10,000건) | $0 | 30-50건 |
| Hacker News | EN | HN API (무료, 제한 없음) | $0 | 10-20건 |
| Twitter/X | EN/KR | X API Free (월 1,500 읽기) | $0 | 5-10건 |
| Quora | EN | RSS + 크롤링 | $0 | 10-15건 |
| Indie Hackers | EN | RSS Feed | $0 | 5-10건 |
| Product Hunt | EN | PH API (무료) | $0 | 5건 |
| 네이버 지식인 | KR | 네이버 검색 API (일 25,000건 무료) | $0 | 10-20건 |
| 디스콰이엇 | KR | RSS/크롤링 | $0 | 5건 |
| **합계** | | | **$0** | **80-135건/일** |

#### 수집 방식: 키워드 매칭이 아닌 AI 톤 분석

키워드 패턴 매칭은 구식이다. "I wish there was"에 걸리는 건 전체 pain point의 10%도 안 됨.

```
구식: 키워드 매칭 → "tired of", "I wish" 등 패턴에 맞는 것만 수집
     → 한계: "My air fryer keeps burning everything" 같은 건 못 잡음

현대: AI 톤 분석 → 글 전체를 읽고 "불편함/불만/갈증"이 있는지 판단
     → "My air fryer keeps burning everything" → pain point로 잡힘
     → "just spent 3 hours doing this manually" → pain point로 잡힘
     → 키워드 상관없이, 톤이 불만이면 수집
```

```python
# src/factory/collector.py

class PainPointCollector:
    """AI 기반 pain point 수집 - 톤 분석"""

    def analyze_post(self, post: RawPost) -> PainPoint | None:
        """키워드 아닌 AI가 글의 톤/맥락을 분석해서 pain point 여부 판단"""
        prompt = f"""
        다음 글을 읽고, 이 사람이 해결되지 않은 불편/불만/갈증을
        표현하고 있는지 판단해줘.

        글: {post.text}
        출처: {post.source} ({post.subreddit or post.channel})

        판단 기준:
        - 키워드가 아닌 전체 톤과 맥락으로 판단
        - "불평", "귀찮음", "시간 낭비", "더 나은 방법 없나" 등의 감정
        - 구체적 상황이 있으면 더 좋음
        - 너무 추상적인 불만 (예: "세상이 불공평해")은 제외
        - 소프트웨어/도구로 해결 가능한 문제만 포함

        JSON 응답:
        {{
          "is_pain_point": true/false,
          "confidence": 0.0-1.0,
          "extracted_pain": "한 줄 요약",
          "category": "finance/productivity/cooking/health/...",
          "target_audience": "누구의 문제인지",
          "solvable_with_tool": true/false
        }}
        """
        ...
```

이 방식이면 어떤 언어, 어떤 표현이든 AI가 "이 사람 불편해하고 있다"를 잡아냄. 수집량도 키워드 매칭 대비 3-5배 늘어남.

#### 수집 자동화 코드 구조

```python
# src/factory/collector.py (전체 구조)

class PainPointCollector:
    """멀티 채널 수집 + AI 톤 분석 통합"""

    def __init__(self):
        self.channels = [
            RedditCollector(),     # PRAW
            HNCollector(),         # HN API
            TwitterCollector(),    # tweepy
            NaverCollector(),      # 네이버 검색 API
        ]
        self.analyzer = ToneAnalyzer()  # AI 톤 분석

    def collect_and_analyze(self) -> list[PainPoint]:
        """수집 → AI 톤 분석 → 중복 제거"""
        raw_posts = []
        for channel in self.channels:
            raw_posts.extend(channel.collect())

        # AI가 각 글의 톤을 분석해서 pain point만 추출
        pain_points = []
        for post in raw_posts:
            result = self.analyzer.analyze_post(post)
            if result and result.confidence >= 0.7:
                pain_points.append(result)

        return self.deduplicate(pain_points)

    def deduplicate(self, points: list[PainPoint]) -> list[PainPoint]:
        """임베딩 + 코사인 유사도 0.85+ 병합"""
        ...
```

#### 데이터 저장 포맷

```json
{
  "id": "pp_20260320_reddit_001",
  "source": "reddit",
  "subreddit": "r/smallbusiness",
  "url": "https://reddit.com/r/smallbusiness/...",
  "raw_text": "I wish there was a simple tool to calculate...",
  "extracted_pain": "소상공인이 세금 계산을 수동으로 하는 고통",
  "category": "finance",
  "target_audience": "small_business_owner",
  "language": "en",
  "upvotes": 47,
  "comments": 23,
  "collected_at": "2026-03-20T09:00:00Z",
  "status": "raw"
}
```

#### 수집 스케줄

```
매일 06:00 UTC (한국 15:00): 크론잡 자동 실행
수집량 목표:
  - Week 1-4: 일 50건 (파이프라인 안정화)
  - Week 5+: 일 100건+
  - 월 3,000건+ 축적
```

---

### Step 2: 필터링 + 분류 (자동)

#### 필터링 파이프라인

```
수집 (100건/일)
  ↓
[1단계] 중복 제거 — 임베딩 유사도 0.85+ 병합 → 약 70건
  ↓
[2단계] 진짜/가짜 필터 — LLM 판별 → 약 40건
  ↓
[3단계] 경쟁 체크 — 기존 도구 검색 → 약 20건
  ↓
[4단계] 난이도 평가 — Claude가 만들 수 있는가? → 약 15건
  ↓
[5단계] 점수화 + 랭킹 → 상위 5건/일 = 후보
```

#### 진짜 vs 가짜 Pain Point 판별 기준

```python
FILTER_CRITERIA = {
    "real_signals": [
        "구체적 상황 묘사 (숫자, 빈도, 도구명 포함)",
        "댓글에서 공감/동의 (upvote 10+, 공감 댓글 3+)",
        "반복 등장 (다른 채널에서도 비슷한 pain)",
        "현재 대안이 불편함 (엑셀, 수작업, 비싼 유료 도구)",
        "특정 직업군/상황에 국한 (니치)",
    ],
    "fake_signals": [
        "너무 추상적 ('생산성을 높이고 싶어')",
        "이미 완벽한 무료 도구 존재 (Google Sheets로 충분)",
        "하드웨어/물리적 문제 (소프트웨어로 해결 불가)",
        "법적/규제 이슈 (도구로 해결 불가)",
        "작성자만의 극히 개인적 문제",
    ],
}
```

#### 점수화 공식

```
Priority Score = (시장 크기 x 0.35) + (해결 가능성 x 0.30) + (경쟁 부재 x 0.25) + (수익화 잠재력 x 0.10)

시장 크기 (1-10):
  - Reddit upvote 수, 유사 포스트 빈도, 검색량 (Google Trends)
  - 10 = 월 검색량 10,000+, 5 = 1,000-10,000, 1 = 100 미만

해결 가능성 (1-10):
  - 10 = HTML/JS만으로 가능 (계산기, 변환기)
  - 7 = API 1개 필요 (환율, 날씨)
  - 4 = 복잡한 로직 필요 (ML, 대량 데이터)
  - 1 = 불가능 (물리적 한계)

경쟁 부재 (1-10):
  - 10 = 구글 첫 페이지에 직접 해결 도구 없음
  - 7 = 있지만 UX 구림 or 유료
  - 4 = 괜찮은 무료 도구 존재
  - 1 = 완벽한 무료 도구 이미 존재

수익화 잠재력 (1-10):
  - 10 = 금융/보험 니치 (AdSense RPM $15-40)
  - 7 = B2B/생산성 (RPM $8-15)
  - 4 = 일반 (RPM $3-8)
  - 1 = 엔터테인먼트 (RPM $1-3)
```

#### 필터링 자동화 코드 구조

```python
# src/factory/filter.py

class PainPointFilter:
    """Gemini API로 pain point 필터링 + 점수화"""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def evaluate(self, pain: PainPoint) -> ScoredPainPoint:
        prompt = f"""
        다음 pain point를 평가해줘:
        원문: {pain.raw_text}
        출처: {pain.source} ({pain.subreddit})
        공감 지표: upvote {pain.upvotes}, 댓글 {pain.comments}

        아래 4가지 기준으로 1-10 점수를 매기고, 한 줄 근거를 달아줘:
        1. 시장 크기
        2. 해결 가능성 (단순 웹 도구로)
        3. 경쟁 부재
        4. 수익화 잠재력

        JSON으로 응답:
        {{"market_size": 7, "feasibility": 9, "competition_gap": 6, "monetization": 5, "tool_idea": "..."}}
        """
        response = self.model.generate_content(prompt)
        return self.parse_score(response, pain)
```

---

### Step 3: MVP 자동 생성 (자동)

#### 도구 유형 분류

| 유형 | 복잡도 | 생성 시간 | 예시 |
|------|:------:|:---------:|------|
| **계산기** | 낮음 | 30-60분 | 세금 계산기, BMI, 대출 이자, 에어프라이어 시간 |
| **변환기** | 낮음 | 30-60분 | 단위 변환, 파일 형식, 색상 코드, 시간대 |
| **생성기** | 중간 | 1-2시간 | 비밀번호, QR코드, 색상 팔레트, Lorem Ipsum |
| **분석기** | 중간 | 1-2시간 | SEO 점수, 가독성 검사, 이미지 메타데이터 |
| **체커** | 중간 | 1-2시간 | 도메인 가용성, SSL 상태, 이메일 유효성 |
| **비교기** | 높음 | 2-3시간 | 가격 비교, 스펙 비교, 서비스 비교 |
| **시뮬레이터** | 높음 | 2-3시간 | 복리 계산, 은퇴 시뮬레이션, A/B 테스트 |

#### 기술 스택 결정

**배포 플랫폼: Cloudflare Pages (Vercel 아님)**

Vercel Hobby 플랜은 상업적 사용을 명시적으로 금지한다 (광고, 어필리에이트 포함).
위반 시 계정 정지 리스크. Pro 플랜은 월 $20/user.

Cloudflare Pages는:
- 무료 티어에서 **상업적 사용 허용**
- **무제한 bandwidth** (Vercel은 100GB 제한)
- **무제한 요청**
- 빌드 500회/월 (충분)
- Workers 무료: 100,000 req/day
- 글로벌 CDN 자동 적용

```
결론: Cloudflare Pages = 도구 100개를 $0에 운영 가능
     Vercel Pro = 월 $20 (상업적 사용 시 필수)
     → Cloudflare Pages 선택
```

**도구 기술 스택:**

```
프론트엔드: HTML + Tailwind CSS + Vanilla JS (or Alpine.js)
  - Next.js는 과도함. 계산기에 프레임워크 불필요
  - 정적 파일 = Cloudflare Pages에 최적
  - 빌드 없음, 배포 즉시

대안 (복잡한 도구): Next.js (App Router) + Tailwind
  - 서버 컴포넌트 필요한 경우에만
  - Cloudflare Pages + Workers로 배포

공통:
  - 1페이지 구조 (SPA)
  - 반응형 (모바일 우선)
  - 다크모드 기본
  - Google Analytics (or Plausible) 내장
  - AdSense 슬롯 2-3개
  - 로그인 없음, 즉시 사용 가능
```

#### 자동 생성 프로세스 — UX 가설 다중 생성

핵심: **Sam이 UX를 판단하지 않는다. AI가 가설을 세우고, 시장이 고른다.**

```
[입력] scored_pain_point.json
  ↓
[1] Pain point 1개 → UX 가설 N개 자동 생성 (Claude API)
    같은 문제를 다른 방식으로 푸는 변형:

    예) "에어프라이어 온도 변환"
      UX-A: 입력 1개 (온도만) → 자동 변환
      UX-B: 입력 2개 (온도+시간) → 동시 변환
      UX-C: 음식 카테고리 선택 → 추천 온도/시간 표시
      UX-D: 슬라이더 UI → 실시간 변환
      UX-E: 오븐 vs 에어프라이어 비교표

    예) "프리랜서 시급 계산"
      UX-A: 연봉 목표 입력 → 필요 시급 역산
      UX-B: 생활비 항목별 입력 → 최소 시급 산출
      UX-C: 시급 입력 → 연간/월간 예상 수입 시뮬레이션
  ↓
[2] 각 UX 가설마다 독립 코드 생성 (Claude API)
    - index.html (Tailwind + 로직)
    - meta 태그 (SEO, 각 가설별 약간 다른 키워드)
    - analytics 스니펫 (가설별 이벤트 ID 구분)
    - AdSense 슬롯
  ↓
[3] 전부 배포
    - gh repo create micro-tools/{tool-name}-{variant} --public
    - wrangler pages deploy
    - 서브도메인: {tool-name}-a.instytools.com, {tool-name}-b.instytools.com ...
  ↓
[4] 2주 후 자동 판정
    - 각 UX 가설의 체류시간, 도구 사용률, 재방문율 비교
    - 승자 1개만 생존, 나머지 폐기
    - 승자의 서브도메인을 {tool-name}.instytools.com으로 통합
  ↓
[5] 품질 게이트
    - Lighthouse 90+ 미달 시 배포 차단
    - 모바일 렌더링 확인
    - 기능 테스트 (입력 → 출력)
```

**이 구조의 장점:**
- Sam의 UX 감각에 의존하지 않음
- 시장이 직접 "이 UX가 낫다"를 투표
- Pain point 1개에서 3-5배 더 많은 실험 가능
- A/B 테스트가 자동으로 내장됨

#### 자동 생성 코드 구조

```python
# src/factory/generator.py

class ToolGenerator:
    """Pain point를 받아서 웹 도구 코드를 생성"""

    def generate_variants(self, pain: ScoredPainPoint, n: int = 5) -> list[ToolProject]:
        """Pain point 1개 → UX 가설 N개 → 각각 코드 생성"""
        specs = self.create_specs(pain, n_variants=n)
        projects = []
        for spec in specs:
            code = self.generate_code(spec)
            project = ToolProject(
                name=spec.slug,
                files={
                    "index.html": code.html,
                    "robots.txt": self.robots_txt(),
                    "sitemap.xml": self.sitemap(spec),
                },
                metadata=spec,
            )
            projects.append(project)
        return projects

    def create_specs(self, pain: ScoredPainPoint, n_variants: int = 5) -> list[ToolSpec]:
        """Pain point 1개에서 UX 가설 N개를 생성"""
        prompt = f"""
        다음 pain point를 해결하는 무료 웹 도구를 {n_variants}가지 다른 UX로 설계해줘.
        같은 문제를 풀되, 입력 방식/출력 형태/인터랙션이 각각 달라야 함.

        Pain point: {pain.extracted_pain}
        타겟: {pain.target_audience}

        각 변형(variant)마다 JSON:
        {{
          "variant": "A",
          "name": "Air Fryer Time Converter",
          "slug": "air-fryer-converter-a",
          "ux_hypothesis": "온도 하나만 입력하면 자동 변환 - 최소 입력 가설",
          "tagline": "Convert oven temp to air fryer in one click",
          "description": "...(SEO용 150자)",
          "inputs": [{{"label": "Oven Temperature", "type": "number", "unit": "F"}}],
          "logic": "temp = oven_temp - 25; time = oven_time * 0.8",
          "output_format": "Temperature: {{temp}}F, Time: {{time}} minutes",
          "seo_keywords": ["air fryer converter", "oven to air fryer"],
          "category": "cooking"
        }}

        {n_variants}개 변형을 배열로 응답해줘.
        각 변형의 ux_hypothesis가 왜 이 UX가 유저에게 먹힐 수 있는지 한 줄로 설명.
        """
        ...
```

#### 도구당 비용 + 시간 추정 (UX 다중 가설 포함)

```
Pain point 1개 → UX 가설 3-5개 → 승자 1개 생존

생성 비용:
  Claude API (UX 가설 5개 + 코드 5벌):  $0.10-0.25/pain point
  Gemini API (필터링):                   $0 (무료 tier)
  Cloudflare Pages:                      $0
  도메인 (instytools.com):               $12/년 (서브도메인 무제한)
  ───────────────────────
  pain point 1개당 비용: 약 $0.10-0.25
  pain point 20개/월 x 5 변형 = 도구 100개/월 비용: 약 $2-5

생성 시간 (Sam 투입):
  파이프라인 구축:          20시간 (1회)
  주간 리뷰:               주 1시간 (결과 확인 + 승자 판정 확인)
  → 100개 UX 가설 배포 = Sam 약 4시간/월
  → 이후 자동: Sam 주 1시간 (리뷰만)
```

---

### Step 4: 배급 (반자동)

#### SEO (자동)

```html
<!-- 각 도구에 자동 삽입되는 메타 태그 -->
<title>{tool_name} - Free Online {category} Tool | Insty Tools</title>
<meta name="description" content="{tagline}. {description}">
<meta name="keywords" content="{seo_keywords}">
<link rel="canonical" href="https://{slug}.instytools.com">

<!-- Open Graph -->
<meta property="og:title" content="{tool_name}">
<meta property="og:description" content="{tagline}">
<meta property="og:image" content="/og-image.png">  <!-- 자동 생성 -->

<!-- Schema.org -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "{tool_name}",
  "description": "{description}",
  "applicationCategory": "{category}",
  "offers": { "@type": "Offer", "price": "0" }
}
</script>
```

#### 콘텐츠 연결 (반자동)

```
Sam의 유튜브/인스타 → 프로필 링크트리에 "Free Tools" 섹션
  ↓
instytools.com (랜딩) → 도구 디렉토리
  ↓
각 도구 → 하단에 "More free tools by Insty" + 상호 링크
```

#### 배급 채널 전략

| 채널 | 방법 | 빈도 | 주의 |
|------|------|:----:|------|
| Google SEO | 자동 (메타 태그 + sitemap) | 상시 | 핵심 채널. 3-6개월 후 효과 |
| Reddit | 관련 서브레딧에 "made this free tool" 포스트 | 주 2-3건 | 가치 먼저, 링크는 댓글에 |
| Twitter/X | "Just shipped: {도구명}" 트윗 | 도구 출시마다 | Build in public 태그 |
| Hacker News | Show HN 포스트 | 월 1-2건 엄선 | 개발자 도구만 |
| Product Hunt | 런칭 | 월 1건 엄선 | 가장 자신 있는 것만 |
| 인스타/유튜브 | 도구 소개 쇼츠 | 주 1편 | 엔터 + 유용함 조합 |

#### 상호 링크 구조

```
instytools.com (허브)
  ├── air-fryer-converter.instytools.com
  │     └── footer: "Try also: Oven Temp Calculator, Recipe Scaler"
  ├── tax-calculator.instytools.com
  │     └── footer: "Try also: Invoice Generator, Expense Tracker"
  └── password-generator.instytools.com
        └── footer: "Try also: Password Strength Checker, Hash Generator"
```

---

### Step 5: 반응 측정 + 판단 (자동)

#### 분석 세팅

```
각 도구에 자동 삽입:
  - Google Analytics 4 (gtag.js) — 무료
  - 이벤트 추적: 도구 사용 횟수, 입력 완료율, 공유 클릭

또는:
  - Plausible Analytics — 셀프 호스트 시 무료
  - 더 가볍고, 프라이버시 친화적
```

#### 자동 판단 로직

```python
# src/factory/evaluator.py

class ToolEvaluator:
    """2주 후 자동으로 도구 생존 여부 판단"""

    THRESHOLDS = {
        "survive": {
            "daily_visitors": 50,       # 일 방문자 50명+
            "avg_session": 30,          # 평균 체류 30초+
            "tool_usage_rate": 0.3,     # 방문자 중 30%가 실제 도구 사용
        },
        "promising": {
            "daily_visitors": 200,
            "avg_session": 60,
            "return_rate": 0.1,         # 10% 재방문
        },
        "hit": {
            "daily_visitors": 1000,
            "avg_session": 120,
            "return_rate": 0.2,
        },
    }

    def evaluate(self, tool_id: str, days: int = 14) -> Verdict:
        metrics = self.fetch_analytics(tool_id, days)

        if metrics.daily_visitors >= self.THRESHOLDS["hit"]["daily_visitors"]:
            return Verdict.HIT          # Sam이 직접 개선 + 수익화
        elif metrics.daily_visitors >= self.THRESHOLDS["promising"]["daily_visitors"]:
            return Verdict.PROMISING    # SEO 강화 + 콘텐츠 추가
        elif metrics.daily_visitors >= self.THRESHOLDS["survive"]["daily_visitors"]:
            return Verdict.SURVIVE      # 유지, 관찰
        else:
            return Verdict.ARCHIVE      # 서브도메인 해제, 코드 보관
```

#### 판정 후 액션

```
ARCHIVE (일 방문자 50 미만):
  - Cloudflare Pages에서 커스텀 도메인 해제
  - GitHub repo를 archived로 전환
  - 비용: $0 (코드는 보관, 호스팅만 해제)

SURVIVE (일 50-199):
  - 유지. 추가 투입 없음
  - SEO가 시간이 지나면서 자연 성장할 수 있음
  - 3개월 후 재평가

PROMISING (일 200-999):
  - AdSense 최적화 (광고 위치 조정)
  - 관련 도구 추가 (같은 니치)
  - 블로그 포스트 작성 (SEO 부스트)

HIT (일 1,000+):
  - Sam이 직접 개선 (UX, 기능 추가)
  - 유료 버전 검토 (프리미엄 기능)
  - 이메일 수집 시작
  - 어필리에이트 링크 추가
```

---

## 2. 수익화 모델

### 단계별 수익화

```
[Phase A] 도구 1-50개 (M2-4):
  └── Google AdSense만
      - 승인 기준: 양질의 콘텐츠 + 개인정보처리방침
      - 예상 RPM: $3-8 (니치에 따라)
      - 현실적 수입: 거의 $0 (트래픽 부족)

[Phase B] 도구 50-100개, 생존 도구 10-15개 (M5-8):
  └── AdSense + 어필리에이트
      - 관련 서비스/제품 추천 링크
      - 예: 세금 계산기 → 회계 소프트웨어 어필리에이트
      - 예: 이미지 변환기 → Canva 어필리에이트
      - 월 예상: 5-20만원

[Phase C] 히트 도구 발견 (M9-12):
  └── Freemium 전환
      - 기본 기능: 무료 (트래픽 유지)
      - 고급 기능: 일회성 $5-20
        - 대량 처리, 내보내기, API 접근, 광고 제거
      - 이메일 수집 → 뉴스레터 → 스폰서
      - 월 예상: 20-50만원

[Phase D] 히트 도구 키움 (M13-24):
  └── 구독 모델
      - Pro 플랜: $5-10/월
      - 팀 플랜: $20-50/월
      - 월 예상: 100-300만원
```

### AdSense 수익 현실적 계산

```
도구 100개 기준 (M8 시점):
  - 생존 도구: 15개 (생존율 15%)
  - 평균 일 방문자: 100명/도구
  - 총 일 방문자: 1,500명
  - 월 방문자: 45,000명
  - RPM (기대치): $5 (도구/유틸리티 니치)
  - 월 AdSense 수익: 45 x $5 = $225 (약 30만원)

도구 200개 기준 (M12 시점):
  - 생존 도구: 30개
  - 평균 일 방문자: 150명/도구
  - 총 일 방문자: 4,500명
  - 월 방문자: 135,000명
  - RPM: $5-8
  - 월 AdSense 수익: 135 x $6.5 = $878 (약 115만원)
  - + 어필리에이트: 약 15-30만원
  - 합계: 약 130-145만원
```

### 어필리에이트 프로그램 후보

| 카테고리 | 어필리에이트 | 커미션 |
|---------|------------|:------:|
| 회계/재무 | QuickBooks, FreshBooks | $5-30/가입 |
| 디자인 | Canva Pro, Figma | $10-36/가입 |
| 생산성 | Notion, Todoist | $5-15/가입 |
| 호스팅 | Cloudflare, Vercel | 가변 |
| AI 도구 | ChatGPT Plus, Midjourney | $5-20/가입 |
| 이메일 | ConvertKit, Mailchimp | 30% 반복 |

---

## 3. 핵심 인사이트: 이 어프로치는 모든 분야에 적용 가능

도구를 만드는 것이 포인트가 아니다. **pain point를 해결하는 UX를 설계하는 것**이 포인트다.
그리고 그 UX 설계마저 AI가 가설을 세우고, 시장이 검증한다.

```
전통 방식:
  사람이 문제 발견 → 사람이 UX 설계 → 사람이 코드 → 사람이 판단
  → 1개 만드는 데 1-2주, 실패하면 시간 낭비

팩토리 방식:
  AI가 문제 수집 → AI가 UX 가설 N개 → AI가 코드 → 시장이 판단
  → pain point 1개에서 5개 가설, 2주 후 승자만 생존
  → Sam은 감독만

이 구조는 도메인에 독립적이다:
  요리 pain point → 요리 UX 가설 5개 → 시장 검증
  금융 pain point → 금융 UX 가설 5개 → 시장 검증
  육아 pain point → 육아 UX 가설 5개 → 시장 검증

pain point 수집 채널만 바꾸면 어떤 분야든 같은 파이프라인이 돌아간다.
```

## 4. 분야별 확장성

> "Pain point만 잘 모으면 어떤 분야든 가능" -- 이 인사이트의 구체화.

### 업종별 pain point 채널 + 도구 예시

#### 소상공인 / 자영업자

**수집 채널**: 네이버 카페 (자영업 커뮤니티), r/smallbusiness, r/Entrepreneur, Facebook Groups (자영업자 모임)

| 도구 | 설명 | 난이도 |
|------|------|:------:|
| 인건비 계산기 | 시급/월급/4대보험 자동 계산 | 낮음 |
| 메뉴 가격 계산기 | 원가율 기반 메뉴 가격 산정 | 낮음 |
| 영업시간 수익 시뮬레이터 | 시간대별 예상 매출 | 중간 |
| 배달앱 수수료 비교기 | 배민/쿠팡이츠/요기요 수수료 비교 | 중간 |
| 간이과세 vs 일반과세 비교기 | 어떤 게 유리한지 자동 판단 | 낮음 |

#### 프리랜서 / 1인 사업자

**수집 채널**: r/freelance, Indie Hackers, 디스콰이엇, Twitter #freelance

| 도구 | 설명 | 난이도 |
|------|------|:------:|
| 시급 계산기 | 연봉 목표 → 필요 시급 역산 | 낮음 |
| 인보이스 생성기 | PDF 인보이스 즉시 생성 | 중간 |
| 프로젝트 견적기 | 시간 추정 → 견적서 자동 | 중간 |
| 세금 예상 계산기 | 분기별 예상 세금 | 낮음 |
| 계약서 체크리스트 | 빠진 조항 체크 | 낮음 |

#### 학생

**수집 채널**: r/college, r/studytips, 네이버 지식인, 에브리타임

| 도구 | 설명 | 난이도 |
|------|------|:------:|
| 학점 계산기 | GPA/학점 자동 계산 | 낮음 |
| 과제 마감 타이머 | 남은 시간 + 우선순위 표시 | 낮음 |
| 인용 포맷터 | APA/MLA/Chicago 자동 변환 | 중간 |
| 장학금 자격 체커 | 조건 입력 → 가능한 장학금 목록 | 높음 |
| 시험 점수 필요 계산기 | "A 받으려면 기말에 몇 점?" | 낮음 |

#### 직장인

**수집 채널**: r/cscareerquestions, 블라인드, LinkedIn, r/personalfinance

| 도구 | 설명 | 난이도 |
|------|------|:------:|
| 연봉 실수령액 계산기 | 세후 월급 자동 계산 | 낮음 |
| 퇴직금 계산기 | 근속 기간별 퇴직금 | 낮음 |
| 연차 관리 도구 | 남은 연차 + 소진 계획 | 낮음 |
| 출퇴근 비용 비교기 | 대중교통 vs 자차 vs 자전거 | 중간 |
| 연봉 협상 시뮬레이터 | 시장 데이터 기반 적정 연봉 | 중간 |

#### 부모 / 육아

**수집 채널**: r/parenting, r/Mommit, 맘카페, 육아 커뮤니티

| 도구 | 설명 | 난이도 |
|------|------|:------:|
| 이유식 스케줄러 | 월령별 이유식 시간표 | 낮음 |
| 기저귀 비용 계산기 | 브랜드별 월/연 비용 비교 | 낮음 |
| 수면 패턴 트래커 | 아기 수면 시간 기록 + 분석 | 중간 |
| 예방접종 체크리스트 | 월령별 접종 스케줄 | 낮음 |
| 아이 성장 곡선 체커 | WHO 성장 곡선 대비 현재 위치 | 중간 |

### 도메인별 확장

| 도메인 | RPM 기대치 | AI가 감지할 불만 톤 예시 | 비고 |
|--------|:---------:|--------------------------|------|
| 금융/보험 | $15-40 | 세금 계산 복잡, 보험료 비교 불편 | **최고 RPM** |
| 건강/피트니스 | $8-15 | 칼로리 계산 귀찮, 운동 루틴 짜기 어려움 | 경쟁 치열 |
| 교육 | $5-10 | 학점 관리 혼란, 과제 마감 스트레스 | 학생 트래픽 |
| 마케팅/SEO | $10-20 | SEO 점수 모름, 분석 도구 비쌈 | 높은 RPM |
| 요리 | $5-10 | 레시피 변환 실패, 재료 대체 모름 | 에어프라이어 성공 사례 |
| 개발자 도구 | $8-15 | JSON 깨짐, 정규식 안 됨 | 충성도 높음 |
| 부동산 | $15-30 | 전세 vs 매매 뭐가 유리한지 모름 | **고 RPM** |

### 언어별 확장 전략

```
Phase 1 (M2-6):   영어 도구만 (글로벌 트래픽, 높은 RPM)
Phase 2 (M7-12):  한국어 도구 추가 (한국 니치, 경쟁 적음)
Phase 3 (M13-24): 일본어 도구 (일본 RPM 높음, 한국과 문화 유사)
```

---

## 5. 기존 전략과 통합

### Round 3의 3트랙 + 팩토리 = 4트랙

```
기존 3트랙 (주 18시간):
  ├── 한국 대행:     화/목 20:00-22:00 + 토 09:00-13:00
  ├── 글로벌 대행:   금 20:00-22:00
  └── 콘텐츠:        월/수 20:00-22:00 + 일 09:00-13:00

새로운 팩토리 (추가 시간 최소):
  └── 자동 파이프라인: 크론잡 (Sam 투입 0)
      + 주간 리뷰:    일 12:00-13:00 (기존 시간 내)
```

#### 시간 배분 상세

```
팩토리 구축 기간 (M2, 1회성):
  - 파이프라인 코딩: 20시간 (주말 4회 x 5시간)
  - Sam의 기존 시간에서 할당 (콘텐츠 시간 일부 전용)

팩토리 운영 기간 (M3 이후):
  - 자동: 수집 + 필터링 + 생성 + 배포 (크론잡)
  - Sam: 주 1시간 리뷰 + 승인 (일요일 12:00-13:00)
  - 히트 도구 발견 시: 추가 2-3시간/주 (개선 작업)

→ 기존 주 18시간 + 팩토리 1-3시간 = 주 19-21시간
→ 정규직 직장인이 감당 가능한 범위
```

### 시너지 맵

```
대행 → 팩토리:
  고객이 "이런 거 있으면 좋겠다"고 말하는 순간
  → Pain point DB에 고신뢰 데이터 +1
  → 대행에서 발견한 pain은 검증 완료 상태 (가짜 아님)
  예: 대행 고객이 "리드 점수 매기기 귀찮다" → Lead Scoring Calculator 도구 생성

팩토리 → 콘텐츠:
  도구 출시할 때마다 쇼츠 1편 가능
  "I built a free tool that solves X" = 콘텐츠 소재 무한
  예: 쇼츠 "I built 50 free tools in 3 months - here's what happened"

콘텐츠 → 팩토리:
  쇼츠/유튜브 채널이 도구의 초기 트래픽 역할
  SEO 효과 나오기 전까지 콘텐츠 채널이 부스터
  댓글에서 새로운 pain point 발견 → 팩토리 입력

팩토리 → 대행:
  히트 도구가 리드 생성 역할
  "이 무료 도구 만든 사람인데, 더 깊은 자동화가 필요하시면 연락주세요"
  → 대행 고객 자연 유입

대행 + 팩토리 → Agent 마켓 (장기):
  대행에서 만든 솔루션 + 도구 DB = Agent 마켓플레이스의 초기 인벤토리
```

---

## 6. 수정된 월별 수익 시뮬레이션

> Round 3 대시보드에 **도구 팩토리** 열을 추가.

### Year 1 (36세)

| M | 정규직 | 한국 대행 | 글로벌 대행 | 콘텐츠 | 도구 팩토리 | **합산** | 도구 수 | 생존 도구 |
|:-:|:------:|:---------:|:-----------:|:------:|:-----------:|:--------:|:-------:|:---------:|
| 1 | 445 | 0 | 0 | 0 | 0 | **445** | 0 | 0 |
| 2 | 445 | 30 | 0 | 0 | 0 | **475** | 10 | 0 |
| 3 | 445 | 60 | 200 | 0 | 0 | **705** | 30 | 2 |
| 4 | 445 | 80 | 270 | 0 | 1 | **796** | 50 | 5 |
| 5 | 445 | 100 | 270 | 0 | 3 | **818** | 70 | 8 |
| 6 | 445 | 100 | 400 | 0 | 5 | **950** | 100 | 12 |
| 7 | 445 | 150 | 400 | 5 | 8 | **1,008** | 120 | 15 |
| 8 | 445 | 150 | 400 | 10 | 15 | **1,020** | 140 | 18 |
| 9 | 445 | 200 | 400 | 15 | 20 | **1,080** | 160 | 22 |
| 10 | 445 | 250 | 540 | 20 | 30 | **1,285** | 180 | 25 |
| 11 | 445 | 300 | 540 | 25 | 40 | **1,350** | 200 | 28 |
| 12 | 445 | 300 | 540 | 30 | 50 | **1,365** | 200 | 30 |

> 도구 팩토리 M12 수익: 약 50만원 (AdSense 30만 + 어필리에이트 20만)
> Y1 도구 수입 누적: 약 172만원 (미미하지만 자산은 쌓이는 중)

### Year 2 (37세)

| M | 정규직 | 대행 합산 | 콘텐츠 | 커뮤니티 | 도구 팩토리 | **합산** | 생존 도구 | 히트 도구 |
|:-:|:------:|:---------:|:------:|:--------:|:-----------:|:--------:|:---------:|:---------:|
| 13 | 445 | 840 | 40 | 0 | 60 | **1,385** | 32 | 0 |
| 15 | 445 | 890 | 60 | 50 | 80 | **1,525** | 35 | 1 |
| 18 | 445 | 1,070 | 100 | 150 | 120 | **1,885** | 40 | 2 |
| 21 | 445 | 1,070 | 200 | 300 | 200 | **2,215** | 45 | 2 |
| 24 | 445 | 1,200 | 300 | 450 | 300 | **2,695** | 50 | 3 |

> M18에 히트 도구 1-2개 발견 가정: Freemium 전환으로 월 50-100만 추가
> M24 도구 팩토리 수익: 약 300만원 (AdSense 100만 + 어필리에이트 50만 + Freemium 150만)

### Year 3-5 (38-40세)

| 시점 | 대행 | 커뮤니티 | 콘텐츠 | 도구 팩토리 | **합산** | 히트 도구 |
|:----:|:----:|:--------:|:------:|:-----------:|:--------:|:---------:|
| M30 | 700 | 800 | 550 | 500 | **2,550** (+정규직) | 3-4 |
| M36 | 500 | 1,000 | 750 | 800 | **3,050** (퇴사 후) | 4-5 |
| M48 | 300 | 1,200 | 900 | 1,500 | **3,900** | 6-8 |
| M60 | 200 | 1,500 | 1,000 | 2,500 | **5,200** | 10+ |

> **핵심**: 도구 팩토리는 Year 1에 미미하지만, Year 3부터 대행 수입을 추월.
> Year 5에는 전체 수입의 약 48%를 차지 = **진정한 패시브 인컴**.

### 노동 vs 패시브 (수정 버전)

```
M1:   ████████████████████  노동 100%  패시브 0%
M7:   █████████████████░░░  노동 85%   패시브 15%   ← 도구 + 콘텐츠
M12:  ██████████████░░░░░░  노동 70%   패시브 30%   ← 도구 수입 시작
M18:  ██████████░░░░░░░░░░  노동 55%   패시브 45%   ← 히트 도구 발견
M24:  ████████░░░░░░░░░░░░  노동 40%   패시브 60%   ← 도구 팩토리 효과
M36:  █████░░░░░░░░░░░░░░░  노동 25%   패시브 75%
M48:  ███░░░░░░░░░░░░░░░░░  노동 15%   패시브 85%   ← 진정한 자유
```

> Round 3 대비 패시브 전환이 6-12개월 빨라짐.

---

## 7. 리스크 + 대응

### 리스크 1: 도구 품질이 너무 낮아서 브랜드 이미지 하락

```
현실성: 중간
심각도: 높음

대응:
  - 모든 도구에 "Beta" 배지 (기대치 관리)
  - 품질 게이트: Lighthouse 90+ 미달 시 배포 차단
  - 브랜드 분리: "Insty Tools" =/= "Insty" 메인 브랜드
    → 도구가 잘 되면 Insty 브랜드로 통합
    → 안 되면 조용히 폐기
  - 사용자 피드백 버튼 필수 (개선 루프)
```

### 리스크 2: Cloudflare 무료 티어 한도

```
현실성: 낮음
심각도: 낮음

Cloudflare Pages 무료 한도:
  - bandwidth: 무제한
  - 요청: 무제한
  - 빌드: 500회/월 (도구 100개면 충분)
  - Workers: 100,000 req/day (충분)

한도 도달 시나리오:
  - 빌드 500회 초과: 도구 업데이트를 모아서 배치
  - Workers 초과: 히트 도구만 Workers 사용, 나머지는 정적
  - 정말 트래픽 폭발 시: Pro 플랜 $20/월 (수익이 그 이상이면 OK)
```

### 리스크 3: 스팸으로 인식

```
현실성: 중간
심각도: 높음

구글 스팸 리스크:
  - 저품질 도구 대량 생산 → 구글이 인덱스 제외
  - 대응: 도구마다 유니크 콘텐츠 (설명, FAQ, 사용법)
  - 대응: 도구별 독립 서브도메인 (연쇄 타격 방지)
  - 대응: 생존 판정 후 ARCHIVE 도구는 noindex 처리

Reddit 스팸 리스크:
  - 같은 계정으로 도구 반복 홍보 → 밴
  - 대응: 주 2-3건만, 먼저 커뮤니티에 가치를 주고, 도구는 자연스럽게
  - 대응: "I made this" 포스트는 해당 니치에만, 범용 서브레딧 금지
```

### 리스크 4: API 비용이 예상보다 높음

```
현실성: 낮음
심각도: 낮음

예상 월 비용 (M6 기준):
  - Claude API (코드 생성): $5-10/월 (도구 20개/월)
  - Gemini API (필터링): $0 (무료 tier)
  - Reddit API: $0 (무료 tier, 비상업적 수집)
  - Cloudflare: $0
  - 도메인: $1/월 ($12/년)
  - Analytics: $0
  ─────────────
  총: $6-11/월 (약 1만원)

비용이 올라가는 시나리오:
  - Claude API 대량 사용: Gemini 2.0 Flash로 대체 (무료)
  - Reddit 상업적 사용 감지: HN, Quora 등 대안 채널 비중 올리기
```

### 리스크 5: 유지보수 부담

```
현실성: 높음 (가장 현실적인 리스크)
심각도: 중간

도구 100개의 유지보수:
  - 정적 HTML: 부서질 게 없음 (외부 API 미사용)
  - Tailwind CDN: 메이저 버전 변경 시 일괄 업데이트
  - 히트 도구만 유지보수 (5-10개)
  - 나머지는 "works or dies" 방침

대응:
  - 설계 원칙: 외부 의존성 최소화 (API 호출 도구 최소)
  - 순수 클라이언트 사이드 계산 = 서버 유지보수 0
  - 히트 도구만 Sam이 직접 관리 (주 2-3시간)
  - 나머지 도구는 방치 OK (정적 사이트이므로)
```

### 리스크 6: 100개 만들어도 히트작 0개

```
현실성: 낮음 (과거 데이터 기반)
심각도: 높음

마이크로 SaaS 데이터:
  - 1,000개 분석 결과: 18%가 $1,000-5,000 MRR 달성
  - 70%는 의미 있는 수입 없음
  - 우리 기대: 100개 중 5-10% 생존 = 5-10개

히트작 0개일 때:
  - 잃는 것: 파이프라인 구축 20시간 + 운영 1시간/주
  - 얻는 것: 수집된 pain point DB (대행 영업에 활용 가능)
  - 얻는 것: 100개 도구 포트폴리오 (개발자 브랜딩)
  - 최악의 경우에도 "시간만 잃음" — 금전적 손실 약 0
```

---

## 8. 이 접근이 왜 "노동=돈"을 깨는지

### 대행의 한계

```
Sam의 시급: 약 5만원 (한국 대행) / $50-100 (글로벌 대행)
주 18시간 x 5만원 = 주 90만원 = 월 360만원

이게 한계. 시급을 올려도 천장이 있다:
  - 시급 10만원 x 주 18시간 = 월 720만원
  - 시급 30만원 x 주 18시간 = 월 2,160만원

시급이 아무리 올라도 18시간이라는 천장은 못 깬다.
"시간 판매" 모델의 본질적 한계.
```

### 도구 팩토리의 수학

```
도구 100개 중 히트작 5개:
  - 히트작 A: 일 1,000 방문자 x AdSense $8 RPM = 월 $240
  - 히트작 B: 일 500 방문자 x Freemium 전환 2% x $10 = 월 $300
  - 히트작 C: 일 2,000 방문자 x AdSense $15 RPM (금융) = 월 $900
  - 히트작 D: 일 300 방문자 x 어필리에이트 3% = 월 $180
  - 히트작 E: 일 800 방문자 x AdSense $5 = 월 $120

  합계: $1,740/월 (약 230만원)

Sam의 추가 투입: 주 3시간 (히트작 관리)
시급 환산: 230만원 / 12시간 = 약 19만원/시간

하지만 진짜 포인트는:
  - Sam이 자는 동안에도 도구가 돈을 번다
  - 도구 수가 늘수록 히트 확률이 올라간다
  - 히트작 1개를 키우면 그것만으로 월 수백만원
  - 이게 100번째 도구에서 나올 수도, 10번째에서 나올 수도 있다
```

### 패시브 인컴의 복리 효과

```
M6:   생존 도구 12개 → 월 5만원 (웃기지만, 시작)
M12:  생존 도구 30개 → 월 50만원 (도구가 일하는 중)
M18:  히트 2개 포함  → 월 120만원 (Sam 안 해도 들어옴)
M24:  히트 3개 + Freemium → 월 300만원 (대행 줄여도 됨)
M36:  히트 5개 + 구독자  → 월 800만원 (정규직 월급 초과)
M48:  히트 8개 + 성장    → 월 1,500만원 (대행 없어도 됨)

핵심: 도구는 누적된다. 삭제되지 않는다. 시간이 지나면 SEO가 올라간다.
"시간을 팔지 않는 수입"이 월 1,500만원이면, 그게 경제적 자유다.
```

### 왜 이게 가능한 시대인가

```
2020년: 도구 1개 만드는 데 1-2주 (개발자만 가능)
2024년: 도구 1개 만드는 데 1-2일 (AI 코딩 보조)
2026년: 도구 1개 만드는 데 1-2시간 (Claude Code가 전부 해줌)

생산 비용이 0에 수렴하면, "많이 쏘고 살아남는 것만 키우기" 전략이 합리적.
이전에는 100개를 만드는 비용이 너무 컸다.
지금은 100개를 만드는 비용이 $5 + Sam의 25시간이다.

이건 venture capital의 포트폴리오 전략과 같다:
  VC: 100개 투자 → 10개 생존 → 1-2개가 전체 수익의 90%
  Sam: 100개 도구 → 10개 생존 → 2-3개가 전체 수익의 80%
```

---

## 9. 구체적 첫 도구 후보 10개

> 파이프라인 구축 전에 수동으로 먼저 만들어볼 후보.

| # | 도구 이름 | Pain Point | 타겟 | 난이도 | RPM 예상 |
|:-:|----------|-----------|------|:------:|:--------:|
| 1 | Freelance Rate Calculator | "내 시급을 얼마로 해야 하지?" | 프리랜서 | 낮음 | $8-12 |
| 2 | Air Fryer Time Converter | "오븐 레시피를 에어프라이어에 맞게" | 요리 | 낮음 | $5-8 |
| 3 | Korean Tax Calculator | "실수령액이 얼마지?" | 한국 직장인 | 낮음 | $10-20 |
| 4 | JSON Formatter | "이 JSON 읽을 수가 없어" | 개발자 | 낮음 | $8-12 |
| 5 | Color Palette Generator | "이 이미지에서 색상 추출하고 싶어" | 디자이너 | 중간 | $5-8 |
| 6 | Rent vs Buy Calculator | "월세 vs 전세 vs 매매 뭐가 유리?" | 한국 직장인 | 중간 | $15-25 |
| 7 | Meeting Cost Calculator | "이 회의가 회사에 얼마나 비용인지" | 직장인 | 낮음 | $8-12 |
| 8 | Email Subject Line Tester | "내 이메일 제목이 좋은지 모르겠어" | 마케터 | 중간 | $10-15 |
| 9 | Password Strength Checker | "내 비밀번호가 안전한지" | 일반인 | 낮음 | $3-5 |
| 10 | Markdown to HTML Converter | "마크다운을 HTML로 바꾸고 싶어" | 개발자/블로거 | 낮음 | $5-8 |

**첫 주 목표**: 이 중 3개를 선택, 각각 UX 가설 3개씩 만들어서 Cloudflare Pages에 배포 (총 9개). 파이프라인 구축 전에 "다중 UX 가설 → 시장 검증" 사이클을 수동으로 검증.

---

## 10. 실행 타임라인

### M2 (4주간)

| 주 | 할 일 | 시간 | 산출물 |
|:--:|------|:----:|--------|
| W1 | 수동으로 도구 3개 생성 + 배포 | 6h | 도구 3개 live |
| W2 | Pain Point 수집기 v0.1 (Reddit + HN) | 5h | collector.py |
| W3 | 필터링 + 점수화 모듈 | 5h | filter.py |
| W4 | 자동 생성 + 배포 모듈 | 5h | generator.py + deployer.py |

**M2 종료 시**: 파이프라인 v0.1 작동, 도구 10개 배포

### M3-4

```
- 파이프라인 자동 운영 시작 (크론잡)
- 주 10-15개 도구 자동 생성
- Sam: 주 1시간 리뷰 + 승인
- M4 종료 시: 도구 50개
```

### M5-6

```
- AdSense 신청 + 승인
- 어필리에이트 프로그램 가입
- 첫 수익 발생 시작
- M6 종료 시: 도구 100개, 생존 12개
```

### M7-12

```
- 도구 생성 속도 유지 (월 20개)
- 히트 도구 발견 시 Sam이 직접 개선
- SEO 효과가 서서히 나타남
- M12 종료 시: 도구 200개, 생존 30개, 월 수익 약 50만원
```

---

## 11. 이게 현실적인가?

Sam은 정규직 직장인이다. 주 18시간이 전부다.

```
질문: 기존 3트랙 + 팩토리 = 감당 가능한가?

답:
  - 팩토리 구축: M2에 주말 시간을 콘텐츠 대신 팩토리에 투입 (1회성)
  - 팩토리 운영: 크론잡 = Sam 투입 0. 주 1시간 리뷰만.
  - 히트 발견 시: 대행 1건 줄이고 도구 개선에 투입 (ROI 더 높음)

핵심은 "자동화"다:
  - 수집: 자동
  - 필터링: 자동
  - 생성: 자동 (Claude API)
  - 배포: 자동 (Cloudflare)
  - 측정: 자동 (Analytics)
  - 판단: 자동 (evaluator.py)

Sam이 하는 것:
  1. 주 1회: 생성된 도구 리스트 훑어보고 "배포 승인" 클릭
  2. 월 1회: 히트 도구 개선 (있으면)
  3. 분기 1회: 파이프라인 점검 + 개선

이건 "추가 일"이 아니라 "투자"다.
20시간 한 번 투입하면, 이후 거의 자동으로 자산이 쌓인다.
```

### 최악의 시나리오

```
6개월 후 도구 100개, 히트작 0개:
  잃은 것: 파이프라인 구축 20시간 + 운영 24시간 = 44시간
  얻은 것:
    - Pain point DB 3,000건+ (대행 영업 자산)
    - 도구 100개 포트폴리오 (개발자 브랜딩)
    - 자동화 파이프라인 경험 (콘텐츠 소재)
    - "100개 도구 만든 사람" = 차별화된 스토리

  금전적 손실: 약 $50 (API 비용)

최악이어도 괜찮다. 이건 리스크가 아니라 실험이다.
```

### 최선의 시나리오

```
6개월 후 히트작 2-3개:
  - 월 패시브 수입 100-200만원 추가
  - 이 수입은 Sam이 잠을 자도 들어옴
  - 12개월 후 히트작 키움: 월 300-500만원
  - 대행 의존도 급감 → 번아웃 리스크 감소

이게 되면 Round 3의 타임라인이 6-12개월 앞당겨진다.
```

---

## 12. 동기부여 마일스톤 (팩토리 추가)

```
□ 파이프라인 v0.1 작동           (M2 W4)
□ 첫 도구 10개 배포               (M2)
□ 도구 50개 돌파                  (M4)
□ AdSense 승인                   (M5)
□ 도구 100개 돌파                 (M6)
□ 첫 AdSense 수익 ($1)           (M5-6)
□ 도구 월 수익 10만원              (M7-8)
□ 히트 도구 첫 발견 (일 1,000+)    (M9-12)
□ 도구 월 수익 50만원              (M12)
□ 도구 월 수익 100만원             (M15-18)
□ Freemium 전환 첫 유료 결제       (M12-15)
□ 도구 월 수익 300만원             (M24)
□ 도구 수익이 대행 수익 추월        (M30-36)
□ 도구 월 수익 1,000만원           (M48)
```

---

> **Round 3의 질문**: "이번 주 토요일 9시에 파이프라인 v0.1을 만들었나?"
>
> **Round 4의 질문**: "이번 주에 도구 몇 개를 세상에 내보냈나?"
>
> 100개 중 99개가 죽어도, 1개가 살아남으면 그게 월급보다 큰 패시브 인컴이 된다.
> 도구는 누적된다. 시간은 Sam의 편이다. 많이 쏘고, 살아남는 것만 키워라.
