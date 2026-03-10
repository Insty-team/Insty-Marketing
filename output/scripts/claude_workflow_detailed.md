dho# Claude로 콘텐츠 자동화 파이프라인 만든 이야기 (상세 버전)

> 포맷: Talking Head 또는 긴 영상 (3-5분) / YouTube Shorts or 카루셀로도 가능
> 타겟: AI solopreneur, 1인 창업가, 콘텐츠 크리에이터
> 용도: YouTube 영상, 블로그, 또는 여러 Reels로 분할 가능

---

## INTRO (0-20s)

As a solopreneur, content is everything. But creating it? That's the bottleneck.

I was spending 5 hours a week just on content PLANNING — not even creating. Finding good YouTube videos in my niche, watching them, taking notes, writing Reels scripts, crafting captions...

So I asked myself: what if I could automate the entire thing?

I sat down with Claude Code for one session. And I built a system that now generates 10 ready-to-film Reels scripts every single week. Automatically. For free.

Let me walk you through exactly how it works.

---

## PART 1: THE PROBLEM (20s-1min)

Here's what my content workflow looked like before:

1. **Finding content** — Manually browsing YouTube, searching for trending topics in the AI solopreneur space. 30-40 minutes.
2. **Watching videos** — Sitting through 10-20 minute videos to find the 2-3 golden nuggets. 1-2 hours.
3. **Writing scripts** — Condensing a 15-minute video into a 45-second Reels script with a strong hook, clear structure, and good CTA. 30 minutes per script.
4. **Captions and hashtags** — Writing engaging captions, researching relevant hashtags. 15 minutes per post.

That's roughly 5 hours a week for about 5-7 Reels. And I haven't even filmed or edited anything yet.

For a solopreneur building a product, running marketing, AND doing sales — that's unsustainable.

---

## PART 2: THE SOLUTION — WHAT I BUILT (1min-2min30s)

I built a Python pipeline that runs inside Docker. Here's each stage:

### Stage 1: Smart YouTube Discovery

The system searches YouTube using keywords I've pre-validated for my niche. Not random keywords — these are generated from my brand persona document and tested against YouTube's API to make sure they actually return quality results.

Each video gets filtered:
- Minimum 5,000 views (proven interest)
- 4-40 minutes long (enough substance to extract from)
- Published within the last 6 months (fresh content)

Then scored on a weighted formula:
- 40% view count
- 30% likes
- 20% comments
- 10% recency

Only the top-scoring videos move forward.

### Stage 2: Automatic Transcript Extraction

For each qualifying video, the system pulls the full transcript with timestamps. No API key needed — it uses an open-source library.

I never watch the video. The transcript is all the AI needs.

### Stage 3: AI Script Generation

This is where the magic happens. The transcript gets fed into Gemini AI with a carefully crafted prompt. The prompt tells the AI exactly what to extract and how to structure it.

I have 5 different script formats:

**Talking Head (for camera-facing Reels):**
- **Tutorial** — Hook → Why it matters → Step-by-step How → Summary → CTA
- **Tips** — Hook → 3 actionable tips with examples → CTA
- **Celebrity Lessons** — Hook → Who this person is → The key insight → How to apply it → CTA

**Numbered (for text overlay + B-roll + music Reels):**
- **Numbered Tips** — Bold hook → 4-7 short punchy tips on screen → CTA
- **Numbered Lessons** — Bold hook → 3-5 key lessons on screen → CTA

The numbered format is a game-changer. I don't need to be on camera — just film myself working, walking, or coding, add the text overlay and background music. Production time drops from 1 hour to 15 minutes.

### Stage 4: Storage and Organization

Every script automatically saves to:
- **Notion database** — with status tracking, relevance scores, source video links, and CTA keywords
- **CSV backup** — date-stamped, just in case

I open Notion on Monday, and my content calendar for the week is already filled.

### Stage 5: Docker Deployment

The whole pipeline is containerized in Docker. I can run it on any machine — my Ubuntu workstation, a Windows laptop, or a cloud server.

One command: `docker compose run --rm pipeline weekly`

That generates scripts across all 5 formats. Or I can set it to cron mode and it runs automatically 3 times a week.

---

## PART 3: THE NUMBERS (2min30s-3min)

Let me break down what this actually saves me:

| Before (Manual) | After (Automated) |
|---|---|
| 5 hours/week on content planning | ~5 minutes to review generated scripts |
| 5-7 scripts/week | 10 scripts/week |
| 1 format (talking head only) | 5 formats (talking + text overlay) |
| Inconsistent quality | Structured, proven format every time |

**Monthly cost: $0**

- YouTube Data API: free tier (10,000 units/day, I use ~300)
- Gemini AI: free tier (500 requests/day)
- Notion API: free
- youtube-transcript-api: open source
- Docker: free

The only "cost" was my Claude Code subscription, which I was already paying for. And I built the entire pipeline in a single Claude session.

---

## PART 4: WHAT THIS REALLY MEANS (3min-3min45s)

This isn't just about saving time on content. It's about a fundamental shift in how solopreneurs should think about repetitive work.

Every time you find yourself doing the same task more than twice:
1. Document the steps
2. Build a system
3. Let AI handle the execution

I didn't write a single line of code myself. I described what I wanted to Claude, it built it, tested it, fixed bugs, and deployed it.

That's the real unlock. **You don't need to be a developer to build developer-level automations.** You need to understand your problem clearly enough to describe it.

---

## CTA (3min45s-4min)

If you're a solopreneur spending hours on tasks that could be automated — you're leaving money on the table.

I'm going to keep sharing exactly how I'm building my business with AI. The real workflows, the real tools, the real results.

Follow if that's what you're here for. And comment 'PIPELINE' below — I'll share the technical details and the actual codebase so you can build your own version.

---

## Caption

I was spending 5+ hours every week just PLANNING content.

Not creating. Not filming. Just... planning.

So I built a full automation pipeline with Claude Code. In one session.

Here's what it does, step by step:

**YouTube Discovery**
→ Searches with pre-validated keywords
→ Filters: 5K+ views, 4-40min, last 6 months
→ Scores by engagement (views 40%, likes 30%, comments 20%, recency 10%)

**Transcript Extraction**
→ Pulls full subtitles with timestamps
→ Zero manual video watching

**AI Script Generation**
→ Gemini transforms transcripts into ready-to-film scripts
→ 5 formats: 3 talking head + 2 text overlay
→ Each script includes: hook, structure, caption, hashtags, CTA

**Auto Storage**
→ Notion database (status, scores, source links)
→ CSV backup

**Docker Deployment**
→ One command: `docker compose run --rm pipeline weekly`
→ Or set to cron: auto-runs 3x/week

Results:
- 10 scripts/week (up from 5-7)
- 5 hours saved every single week
- Monthly cost: $0 (all free tier APIs)

The numbered text overlay format means I don't even need to be on camera for half my Reels. Film B-roll, add text + music, done in 15 minutes.

This is what AI-native business actually looks like.

Not "I asked ChatGPT to write a caption."
It's "I built a system that runs my content operation while I sleep."

Comment 'PIPELINE' for the full breakdown and codebase!

## Hashtags

#AIautomation #ClaudeAI #ContentPipeline #Solopreneur #BuildInPublic #AIworkflow #ContentStrategy #InstagramReels #ProductivitySystem #AIsolopreneur #WorkSmarter #NoCode #PythonAutomation #NotionSetup #DockerDeploy

## CTA Keyword

PIPELINE

---

## 분할 활용 가이드

이 상세 스크립트를 여러 콘텐츠로 분할 가능:

| # | 분할 콘텐츠 | 소스 파트 | 포맷 |
|---|---|---|---|
| 1 | "5시간 → 5분으로 줄인 방법" | Intro + Part 1 | Reels (Talking Head) |
| 2 | "내 자동화 파이프라인 5단계" | Part 2 전체 | Reels (Numbered) |
| 3 | "$0으로 주 10개 콘텐츠 만드는 법" | Part 3 | Reels (Talking Head) |
| 4 | "코드 1줄 안 짜고 자동화 만든 비결" | Part 4 | Reels (Talking Head) |
| 5 | "풀 튜토리얼" | 전체 | YouTube Long-form |
| 6 | "Before vs After 비교" | Part 3 테이블 | 카루셀 |
