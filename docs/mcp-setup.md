# MCP 서버 & Claude Code 설정 가이드
> 새 머신에서 환경 세팅 시 이 파일 참조.

## 글로벌 설정 (~/.claude/settings.json)

### MCP 서버 목록

#### 1. GitHub MCP
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "<GitHub PAT>"
  }
}
```
- 용도: issue/PR 생성·관리
- 토큰 발급: https://github.com/settings/tokens

#### 2. Sequential Thinking
```json
"sequential-thinking": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```
- 용도: 단계적 추론 보조

#### 3. Playwright (브라우저 자동화)
```json
"playwright": {
  "command": "<node_path>/npx",
  "args": ["-y", "@anthropic-ai/mcp-server-playwright", "--headless", "--browser", "chromium"]
}
```
- 용도: 웹페이지 접근, 스크린샷, DOM 탐색
- 참고: `<node_path>`는 머신의 Node.js 경로 (예: `~/.nvm/versions/node/v20.x.x/bin/npx`)

#### 4. Knowledge Graph Memory
```json
"memory": {
  "command": "<node_path>/npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"],
  "env": {
    "MEMORY_FILE_PATH": "<project_memory_dir>/knowledge-graph.jsonl"
  }
}
```
- 용도: 엔티티/관계/관찰 저장 (JSONL)
- MEMORY_FILE_PATH는 프로젝트별 로컬 경로

#### 5. Notion MCP
```json
"notion": {
  "command": "<node_path>/npx",
  "args": ["-y", "@notionhq/notion-mcp-server"],
  "env": {
    "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <NOTION_TOKEN>\",\"Notion-Version\":\"2022-06-28\"}"
  }
}
```
- 용도: Notion 페이지 읽기/쓰기
- 토큰 발급: https://www.notion.so/my-integrations

## 프로젝트 설정 (.claude/settings.json)

### 권한 (permissions)
- 파일 읽기/쓰기, 웹, git, 패키지 매니저 자동 허용
- `rm -rf /` 만 차단

### Hooks
- **PreCompact**: 컴팩션 전 핸드오버 문서 자동 생성 → `.claude/hooks/pre-compact.sh`
- **SessionStart**: 세션 시작 시 최근 컨텍스트 자동 로드 → `.claude/hooks/session-start.sh`

## 새 머신 세팅 체크리스트
1. [ ] Node.js 설치 (nvm 권장, v20+)
2. [ ] `~/.claude/settings.json`에 MCP 서버 추가 (위 JSON 참조, 토큰 교체)
3. [ ] repo clone: `git clone <repo-url>`
4. [ ] `.claude/hooks/*.sh`에 실행 권한: `chmod +x .claude/hooks/*.sh`
5. [ ] hooks 내 경로가 현재 머신과 맞는지 확인 (MEMORY_DIR 등)
6. [ ] GitHub CLI 설치: `~/bin/gh` 경로에 배치
