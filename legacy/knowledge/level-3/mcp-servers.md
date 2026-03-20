<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/mcp-servers -->

# MCP 서버 연결 | Claude Code 플레이북

## MCP란 무엇인가

MCP(Model Context Protocol)는 Claude Code가 외부 도구, 데이터베이스, API와 표준화된 방식으로 통신할 수 있게 해주는 오픈소스 프로토콜입니다. MCP 서버를 연결하면 Claude Code의 기본 능력을 크게 확장할 수 있습니다.

기본적으로 Claude Code는 파일 시스템, 터미널, 웹 검색 정도만 다룰 수 있습니다. MCP 서버를 연결하면:

- **데이터베이스** — PostgreSQL, MySQL, SQLite 직접 쿼리
- **외부 서비스** — GitHub, Slack, Sentry, Notion, Jira 연동
- **로컬 도구** — 브라우저 자동화, 이미지 처리, 파일 변환
- **커스텀 도구** — 직접 만든 내부 시스템 연결

이 모든 것이 Claude와 자연어 대화로 이루어집니다.

## MCP 서버 설치

MCP 서버는 세 가지 전송 방식을 지원합니다:

### HTTP 원격 서버 (권장)

클라우드 기반 서비스 연결에 권장됩니다:

```
# 기본 구문
claude mcp add --transport http <서버명> <URL>

# 예시: Notion 연결
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Bearer 토큰 인증
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### SSE 원격 서버

```
claude mcp add --transport sse asana https://mcp.asana.com/sse
```

**SSE 지원 중단 예정**: SSE 전송은 deprecated입니다. 가능하면 HTTP 서버를 사용하세요.

### stdio 로컬 서버

로컬 프로세스로 실행되는 서버입니다:

```
# 기본 구문
claude mcp add [옵션] <서버명> -- <명령어> [인수...]

# 예시: Airtable 서버
claude mcp add --transport stdio --env AIRTABLE_API_KEY=YOUR_KEY airtable \
  -- npx -y airtable-mcp-server
```

**옵션 순서**: 모든 옵션(`--transport`, `--env`, `--scope`, `--header`)은 서버 이름 **앞에** 와야 합니다. `--`(이중 대시)는 서버 이름과 실행 명령을 구분합니다.

**Windows 사용자**: Windows(WSL 아닌)에서 `npx`를 사용하는 stdio 서버는 `cmd /c` 래퍼가 필요합니다:

```
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

## 설치 범위 (Scope)

| 범위 | 저장 위치 | 용도 |
|------|---------|------|
| `local` (기본) | `~/.claude.json` (프로젝트별) | 개인 서버, 민감한 자격증명 |
| `project` | `.mcp.json` (git 커밋 가능) | 팀 공유 서버 |
| `user` | `~/.claude.json` (전역) | 모든 프로젝트에서 쓰는 서버 |

```
# 프로젝트 범위로 추가 (팀 공유)
claude mcp add --transport http paypal --scope project https://mcp.paypal.com/mcp

# 사용자 범위로 추가 (전역)
claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com/anthropic
```

프로젝트 범위 서버는 `.mcp.json`에 저장되어 팀원과 공유됩니다. 보안을 위해 처음 사용 시 승인 프롬프트가 표시됩니다.

### `.mcp.json` 환경변수 확장

`.mcp.json`에서 환경변수를 사용할 수 있어, 팀 공유와 개인 자격증명을 분리할 수 있습니다:

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

`${VAR:-default}`로 기본값도 지정 가능합니다.

## 서버 관리

```
# 등록된 서버 목록
claude mcp list

# 특정 서버 상세 정보
claude mcp get <서버명>

# 서버 제거
claude mcp remove <서버명>

# Claude Desktop에서 가져오기 (macOS/WSL)
claude mcp add-from-claude-desktop

# JSON 설정으로 직접 추가
claude mcp add-json weather '{"type":"http","url":"https://api.weather.com/mcp"}'

# 세션 내에서 서버 상태 확인
/mcp
```

## OAuth 2.0 인증

많은 클라우드 MCP 서버는 OAuth 인증이 필요합니다:

1. 서버를 추가합니다:

```
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

2. Claude Code 세션에서 `/mcp` 커맨드를 실행하고 브라우저 로그인을 완료합니다.

인증 토큰은 안전하게 저장되며 자동 갱신됩니다. `/mcp` 메뉴에서 "Clear authentication"으로 접근 권한을 해제할 수 있습니다.

### 사전 구성된 OAuth 자격증명

자동 OAuth를 지원하지 않는 서버는 개발자 포털에서 앱을 등록한 후 자격증명을 제공합니다:

```
claude mcp add --transport http \
  --client-id your-client-id --client-secret --callback-port 8080 \
  my-server https://mcp.example.com/mcp
```

## 인기 MCP 서버

**제3자 서버 주의**: Anthropic이 모든 서버의 보안을 검증한 것은 아닙니다. 신뢰할 수 있는 서버만 설치하세요. 특히 외부 콘텐츠를 가져오는 서버는 프롬프트 인젝션 위험이 있습니다.

### GitHub

```
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
```

사용 예시:
- `> PR #456 리뷰하고 개선 제안해줘`
- `> 이번 스프린트 이슈 목록 가져와서 우선순위 분석해줘`

### Sentry (에러 모니터링)

```
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
# /mcp에서 인증
```

사용 예시:
- `> 지난 24시간 동안 가장 흔한 에러는?`
- `> 에러 ID abc123의 스택 트레이스 보여줘`

### PostgreSQL

```
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "postgresql://readonly:pass@prod.db.com:5432/analytics"
```

사용 예시:
- `> 이번 달 총 매출은?`
- `> 90일 동안 구매하지 않은 고객 찾아줘`

### 파일시스템

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/projects"
      ]
    }
  }
}
```

## MCP Resources (@멘션)

MCP 서버가 리소스를 노출하면 `@` 멘션으로 참조할 수 있습니다:

```
> @github:issue://123 분석해서 수정 제안해줘
> @postgres:schema://users 와 @docs:file://database/user-model 비교해줘
```

프롬프트에서 `@`를 입력하면 사용 가능한 리소스가 자동완성 메뉴에 표시됩니다.

## MCP 프롬프트 (커맨드)

MCP 서버가 프롬프트를 노출하면 슬래시 커맨드로 실행할 수 있습니다:

```
> /mcp__github__list_prs
> /mcp__github__pr_review 456
> /mcp__jira__create_issue "로그인 버그" high
```

`/`를 입력하면 사용 가능한 MCP 프롬프트가 다른 커맨드와 함께 표시됩니다.

## Tool Search (대규모 도구 관리)

MCP 서버가 많아지면 도구 정의가 컨텍스트 윈도우의 상당 부분을 차지할 수 있습니다. **Tool Search**는 모든 도구를 미리 로드하지 않고 필요할 때만 동적으로 검색합니다.

MCP 도구 설명이 컨텍스트의 10%를 초과하면 자동으로 활성화됩니다:

```
# 커스텀 임계값 (5%)
ENABLE_TOOL_SEARCH=auto:5 claude

# 항상 활성화
ENABLE_TOOL_SEARCH=true claude

# 비활성화
ENABLE_TOOL_SEARCH=false claude
```

## Claude Code를 MCP 서버로 사용

Claude Code 자체를 다른 애플리케이션의 MCP 서버로 사용할 수 있습니다:

```
claude mcp serve
```

Claude Desktop의 `claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"]
    }
  }
}
```

## 플러그인 제공 MCP 서버

플러그인은 MCP 서버를 번들할 수 있어, 플러그인 활성화 시 자동으로 도구가 제공됩니다. 플러그인 루트의 `.mcp.json` 또는 `plugin.json`에서 정의합니다:

```json
{
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

## 커스텀 MCP 서버 만들기

내부 시스템이나 커스텀 도구를 MCP 서버로 만들 수 있습니다.

### Node.js

```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  { name: 'my-custom-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'get_product_info',
      description: '상품 ID로 내부 DB에서 상품 정보를 조회합니다',
      inputSchema: {
        type: 'object',
        properties: {
          product_id: { type: 'string', description: '상품 ID' }
        },
        required: ['product_id']
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'get_product_info') {
    const { product_id } = request.params.arguments;
    const product = await fetchProductFromDB(product_id);
    return {
      content: [{ type: 'text', text: JSON.stringify(product) }]
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("my-python-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_analytics",
            description="내부 분석 시스템에서 데이터를 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string"},
                    "date_range": {"type": "string"}
                },
                "required": ["metric"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_analytics":
        result = await query_analytics_system(arguments)
        return [TextContent(type="text", text=str(result))]

async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0], streams[1],
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 관리형 MCP 구성 (Enterprise)

조직에서 MCP 서버를 중앙 제어할 수 있습니다:

### 방법 1: `managed-mcp.json` (배타적 제어)

시스템 경로에 배포하면 사용자는 정의된 서버만 사용할 수 있습니다:

| OS | 경로 |
|----|----|
| macOS | `/Library/Application Support/ClaudeCode/managed-mcp.json` |
| Linux | `/etc/claude-code/managed-mcp.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-mcp.json` |

### 방법 2: 허용/거부 목록 (정책 기반)

관리형 설정에서 `allowedMcpServers`와 `deniedMcpServers`로 서버를 제어합니다:

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverUrl": "https://mcp.company.com/*" }
  ],
  "deniedMcpServers": [
    { "serverUrl": "https://*.untrusted.com/*" }
  ]
}
```

서버 이름(`serverName`), 명령어(`serverCommand`), URL 패턴(`serverUrl`) 세 가지 방식으로 제한할 수 있으며, 거부 목록이 항상 우선합니다.

## 보안 고려사항

**MCP 서버 권한 관리**

- 읽기 전용 계정을 사용하거나 최소 권한 원칙을 적용하세요
- API 토큰은 환경변수로 관리하세요 (`.mcp.json`의 `${VAR}` 구문 활용)
- 민감한 설정 파일은 `.gitignore`에 추가하세요
- 출력 크기 제한: 기본 25,000 토큰 (`MAX_MCP_OUTPUT_TOKENS`로 조정)
- 시작 타임아웃: `MCP_TIMEOUT` 환경변수로 조정 (기본 60초)

---

**다음 챕터**: [멀티 모델 전략](/docs/level-3/multi-model-strategy)

**최종 수정**: 2026년 2월 28일
