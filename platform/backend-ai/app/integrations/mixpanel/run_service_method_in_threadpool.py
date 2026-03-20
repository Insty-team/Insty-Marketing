## Mixpanel 사용하는 Service코드를 비동기로 처리한다면, 해당 헬퍼는 불필요해짐.
## 다만, 현재는 모든 Service코드를 비동기로 처리하기에는 공수가 너무 많이 들어가므로 임시로 사용하는 헬퍼 메서드

from __future__ import annotations
from typing import Any, Callable
from starlette.concurrency import run_in_threadpool
from app.core.db import get_db_session

async def run_with_service_in_threadpool(
    service_factory: Callable[[Any], Any],     # db -> service
    service_call: Callable[[Any], Any],        # lambda service: service.method(args)
):
    def _work():
        db = get_db_session()
        try:
            service = service_factory(db)
            return service_call(service)
        finally:
            db.close()
    return await run_in_threadpool(_work)