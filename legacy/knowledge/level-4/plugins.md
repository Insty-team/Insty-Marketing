<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/plugins -->

# 플러그인 시스템

플러그인은 Skills, Agents, Hooks, MCP/LSP 서버를 **하나의 패키지로 묶어** 프로젝트와 팀 간에 공유할 수 있게 합니다.

## 독립형 vs 플러그인

| 구분 | 독립형 (`.claude/`) | 플러그인 (`.claude-plugin/`) |
|------|-------------------|---------------------------|
| 적합 | 개인 워크플로우, 빠른 실험 | 팀 공유, 커뮤니티 배포, 버전 관리, 프로젝트 간 재사용 |
| Skill 호출 | `/hello` | `/plugin-name:hello` |
| 네임스페이스 | 없음 | 플러그인명으로 격리 |

## 플러그인 디렉토리 구조

```
.claude-plugin/
  plugin.json          # 매니페스트 (필수)
skills/                # Skills
agents/                # 커스텀 서브에이전트
commands/              # 레거시 커맨드
hooks/                 # Hook 스크립트
.mcp.json              # MCP 서버 설정
.lsp.json              # LSP 서버 설정
settings.json          # 플러그인 설정
```

## plugin.json 매니페스트

```json
{
  "name": "my-awesome-plugin",
  "description": "코드 품질 향상을 위한 리뷰 + 테스트 도구 모음",
  "version": "1.0.0",
  "author": "Your Name",
  "homepage": "https://github.com/you/plugin",
  "repository": "https://github.com/you/plugin",
  "license": "MIT"
}
```

필수 필드: `name`, `description`, `version`

## Skills 패키징

```
skills/
  code-review/
    SKILL.md           # /my-awesome-plugin:code-review 로 호출
  test-gen/
    SKILL.md           # /my-awesome-plugin:test-gen 로 호출
```

폴더명이 Skill 식별자가 되며, 플러그인 네임스페이스가 접두사로 붙습니다.

## 테스트 및 배포

### 로컬 테스트

```bash
claude --plugin-dir ./my-plugin
```

### 설치 관리

```
/plugin                # 플러그인 목록, 설치, 제거 관리
```

### 마켓플레이스 제출

1. 문서화 완료
2. 시맨틱 버전 관리
3. 커뮤니티 테스트
4. Claude.ai 또는 Console에 제출

## 기존 설정 마이그레이션

독립형 `.claude/` 설정을 플러그인으로 전환:

1. `.claude-plugin/plugin.json` 생성
2. 파일을 플러그인 구조로 재배치
3. 적절한 매니페스트 작성

---

**최종 수정**: 2026년 2월 28일
