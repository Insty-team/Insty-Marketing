# 기술 결정 기록 (ADR)
> 주요 기술 선택과 그 이유를 기록. 나중에 "왜 이렇게 했지?" 할 때 참조.

## ADR-001: 브라우저 MCP로 Playwright 선택
- **날짜**: 2026-02-28
- **결정**: Puppeteer 대신 Playwright MCP 사용
- **이유**: 접근성 트리 기반으로 토큰 절감, 도구 25+개로 풍부, Microsoft 공식 유지보수
- **대안**: Puppeteer MCP (스크린샷 기반, 도구 ~15개)

## ADR-002: Knowledge Graph MCP 선택 (메모리 서버)
- **날짜**: 2026-02-28
- **결정**: Anthropic 공식 @modelcontextprotocol/server-memory 사용
- **이유**: 의존성 최소, 무료, JSONL 기반으로 가볍고 간단
- **대안**: memory-mcp (Haiku 비용 발생), mcp-memory-service (벡터DB, 설치 복잡)

## ADR-003: 프로젝트 지식을 docs/ (git)에 저장
- **날짜**: 2026-02-28
- **결정**: 프로젝트 지식은 `docs/`에 저장, `memory/`는 머신별 환경 포인터만
- **이유**: 멀티 머신 작업 시 git push/pull로 지식 동기화 필요
- **대안**: `~/.claude/projects/.../memory/`에 전부 저장 (로컬 전용, 동기화 불가)

<!-- 템플릿:
## ADR-NNN: [제목]
- **날짜**: YYYY-MM-DD
- **결정**:
- **이유**:
- **대안**:
-->
