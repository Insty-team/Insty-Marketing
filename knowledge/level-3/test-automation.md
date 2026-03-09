<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/test-automation -->

# 테스트 자동화 | Claude Code 플레이북

## 테스트 자동화

테스트 작성의 가장 큰 장벽은 "시작하기"와 "반복 작업"입니다. Claude Code는 이 두 가지를 해결합니다.

## TDD(테스트 주도 개발) 워크플로우

Claude Code와 TDD의 Red-Green-Refactor 사이클:

**테스트 먼저, 구현 나중**

```
# 1단계: Red — 실패하는 테스트 작성
> calculateDiscount 함수의 테스트를 먼저 작성해줘.
  다음 케이스를 포함:
  - 일반 할인 (10%)
  - VIP 할인 (20%)
  - 쿠폰 중복 적용
  - 최대 할인 한도 초과

# 2단계: Green — 최소 구현
> 테스트가 통과하도록 calculateDiscount를 구현해줘.
  가장 간단한 방식으로.

# 3단계: Refactor — 개선
> 테스트가 통과하는 상태에서 코드를 개선해줘.
  가독성과 유지보수성 중심으로.
```

## 기존 코드에 테스트 추가

```
> src/services/user.service.ts 에 대한 단위 테스트를 작성해줘.
  현재 테스트가 없으니 주요 기능부터 커버해줘.
  엣지 케이스도 포함해줘.

> src/api/orders.controller.ts 의 통합 테스트를 작성해줘.
  실제 HTTP 요청을 시뮬레이션해서.
```

## 테스트 커버리지 목표

```
> 현재 테스트 커버리지를 확인하고,
  80% 이상이 되도록 부족한 부분에 테스트를 추가해줘.
  비즈니스 로직 위주로 우선순위를 정해줘.
```

## 프레임워크별 패턴

### Jest (Node.js/TypeScript)

```
> Jest로 UserService 테스트를 작성해줘.
  외부 의존성(DB, API)은 모킹해줘.

> 이 테스트에 beforeEach로 공통 설정을 추출해줘.
```

```typescript
// Claude가 생성하는 Jest 테스트 예시
describe('UserService', () => {
  let service: UserService;
  let mockDb: jest.Mocked<Database>;

  beforeEach(() => {
    mockDb = createMockDatabase();
    service = new UserService(mockDb);
  });

  describe('findById', () => {
    it('존재하는 사용자를 반환한다', async () => {
      mockDb.users.findUnique.mockResolvedValue(mockUser);
      const result = await service.findById(1);
      expect(result).toEqual(mockUser);
    });

    it('존재하지 않는 사용자에 null을 반환한다', async () => {
      mockDb.users.findUnique.mockResolvedValue(null);
      const result = await service.findById(999);
      expect(result).toBeNull();
    });
  });
});
```

### Vitest

```
> Vitest로 마이그레이션해줘. Jest 테스트를 Vitest 호환으로 변환해줘.
```

### Pytest (Python)

```
> pytest로 payment_service.py 테스트를 작성해줘.
  fixture를 활용해서 테스트 데이터를 관리해줘.
```

```python
# Claude가 생성하는 Pytest 테스트 예시
import pytest
from services.payment import PaymentService

@pytest.fixture
def payment_service():
    return PaymentService(api_key="test_key")

@pytest.fixture
def sample_order():
    return {"amount": 10000, "currency": "KRW", "customer_id": "cust_123"}

class TestPaymentService:
    def test_process_payment_success(self, payment_service, sample_order):
        result = payment_service.process(sample_order)
        assert result.status == "success"
        assert result.amount == 10000

    def test_process_payment_insufficient_funds(self, payment_service):
        order = {"amount": 999999999, "currency": "KRW", "customer_id": "cust_broke"}
        with pytest.raises(InsufficientFundsError):
            payment_service.process(order)
```

### Playwright (E2E)

```
> Playwright로 로그인 → 대시보드 → 프로필 수정 E2E 테스트를 작성해줘.
```

```typescript
// Claude가 생성하는 Playwright 테스트 예시
import { test, expect } from '@playwright/test';

test('사용자 로그인 후 프로필 수정', async ({ page }) => {
  // 로그인
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // 대시보드 확인
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('대시보드');

  // 프로필 수정
  await page.click('a[href="/profile"]');
  await page.fill('[name="name"]', '새 이름');
  await page.click('button:text("저장")');

  // 성공 확인
  await expect(page.locator('.toast')).toContainText('저장되었습니다');
});
```

## 실패한 테스트 자동 수정

```
> npm test 실행 결과 3개 테스트가 실패했어.
  테스트 로직은 수정하지 말고, 소스 코드만 수정해서 통과시켜줘.
```

## Hook으로 테스트 자동 실행

파일 저장 시 관련 테스트를 자동으로 실행하는 Hook:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm test -- --findRelatedTests \"$(cat | jq -r '.tool_input.file_path')\" 2>&1 | tail -20"
          }
        ]
      }
    ]
  }
}
```

## 테스트 우선순위

무엇을 먼저 테스트할지:

1. **비즈니스 로직** — 핵심 도메인 함수, 계산 로직
2. **API 엔드포인트** — 요청/응답 계약, 상태 코드
3. **외부 서비스 연동** — 결제, 이메일, 알림 (모킹)
4. **엣지 케이스** — null, 빈 값, 경계값, 동시성

테스트하지 않아도 될 것:

- 프레임워크 자체 기능 (Express 라우팅 등)
- 단순 getter/setter
- 외부 라이브러리 동작

## 회귀 테스트

```
> 이 버그를 수정한 후, 같은 버그가 재발하지 않도록 회귀 테스트를 추가해줘.
```

## 체크리스트

- 새 기능 구현 시 테스트를 동시에 작성
- 버그 수정 후 회귀 테스트 추가
- 비즈니스 로직 우선 테스트
- 외부 의존성은 모킹
- CI에서 테스트 자동 실행

---

**이전**: [비용 최적화](/docs/level-3/cost-optimization)

**다음**: [CI/CD 통합](/docs/level-3/cicd-integration)

**최종 수정**: 2026년 2월 28일
