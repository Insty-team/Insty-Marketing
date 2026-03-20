import json
import logging
from typing import List, Dict

import requests
from celery import shared_task
from openai import OpenAI

from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.course.course_request_repository import CourseRequestRepository
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)
settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


def search_reference_api(func_name: str, query: str, limit: int = 5) -> List[Dict]:
    logger.info(f"[SearchReferenceAPI] func={func_name}, query={query}, limit={limit}")

    if not query:
        return []

    if func_name == "search_web":
        params = {
            "q": query,
            "num": max(1, min(limit, 10)),
            "engine": "google",
            "api_key": settings.serpapi.api_key,
        }
        try:
            resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json() or {}
            organic = data.get("organic_results", []) or []
            results = []
            for item in organic[:limit]:
                results.append(
                    {
                        "title": item.get("title") or "제목 없음",
                        "url": item.get("link") or "",
                        "type": "web",
                        "description": item.get("snippet") or "",
                    }
                )
            return results
        except Exception as e:
            logger.error(f"[SerpAPI Error] {e}", exc_info=True)
            return []

    if func_name == "search_wikipedia":
        try:
            search_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": max(1, min(limit, 10)),
                },
                timeout=15,
            )
            search_resp.raise_for_status()
            search_data = search_resp.json() or {}
            results = []
            for item in (search_data.get("query", {}) or {}).get("search", []) or []:
                title = item.get("title") or ""
                snippet = (item.get("snippet") or "").replace('<span class="searchmatch">', "").replace("</span>", "")
                page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else ""
                results.append(
                    {
                        "title": title or "제목 없음",
                        "url": page_url,
                        "type": "wiki",
                        "description": snippet,
                    }
                )
            return results
        except Exception as e:
            logger.error(f"[Wikipedia Error] {e}", exc_info=True)
            return []

    logger.warning(f"[SearchReferenceAPI] Unknown func_name={func_name}")
    return []


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_references_generation_task(
    self,
    *,
    package_status_id: int,
    field_values: dict,
):
    db = get_db_session()
    repo = CourseRequestRepository(db)

    try:
        # 상태: PROCESSING
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column="references_status",
            new_status="PROCESSING",
        )
        db.commit()

        base_prompt = load_prompt("references_prompt.j2", {"fields": field_values})
        system_prompt = (
            base_prompt
            + "\n\n중요: 오직 JSON 한 개만 반환하세요. 설명/서문/코드블록 표식 없이 순수 JSON만 출력하세요."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "참고자료를 생성해줘. (JSON만 반환)"},
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "최신 블로그, 뉴스, 튜토리얼 등의 웹 문서 검색",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "검색 키워드"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_wikipedia",
                    "description": "Wikipedia에서 기본 개념, 용어 정의 등을 검색",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "검색 키워드"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

        first = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=1200,
        )

        first_msg = first.choices[0].message
        logger.debug(f"[GPT First] tool_calls={getattr(first_msg, 'tool_calls', None)} content={first_msg.content}")

        augmented_messages = list(messages)
        augmented_messages.append(first_msg)

        tool_calls = getattr(first_msg, "tool_calls", None) or []
        aggregated_refs: List[Dict] = []

        for tc in tool_calls:
            if getattr(tc, "type", "") != "function":
                continue

            call_id = getattr(tc, "id", None)
            fn = getattr(tc, "function", None)
            fn_name = getattr(fn, "name", None)
            fn_args_str = getattr(fn, "arguments", "{}")

            try:
                fn_args = json.loads(fn_args_str) if fn_args_str else {}
            except json.JSONDecodeError:
                logger.error(f"[Tool Args Parse Error] {fn_args_str}")
                fn_args = {}

            query = (fn_args.get("query") or "").strip()
            limit = fn_args.get("limit", 5)

            search_results = search_reference_api(fn_name or "", query=query, limit=limit)

            aggregated_refs.extend(search_results)

            if call_id:
                augmented_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(search_results, ensure_ascii=False),
                    }
                )

        if aggregated_refs:
            augmented_messages.append(
                {
                    "role": "user",
                    "content": (
                        "위의 tool 결과들을 통합해 다음 형식의 JSON만 반환하세요. "
                        '```json\n{"references":[{"title":"","url":"","type":"wiki 또는 web","description":""}...]}\n``` '
                        "단, 코드블록과 추가 텍스트 없이 순수 JSON만 반환하세요. "
                        "최소 2개 이상의 항목을 포함하세요."
                    ),
                }
            )
        else:
            augmented_messages.append(
                {
                    "role": "user",
                    "content": (
                        "검색 결과가 없거나 충분하지 않습니다. "
                        "주어진 강의 정보로부터 합리적으로 추정되는 참고 링크를 2개 이상 구성하여 "
                        '다음 JSON 형식으로만 반환하세요: {"references":[...]}. '
                        "설명 없이 순수 JSON만 반환하세요."
                    ),
                }
            )

        final = client.chat.completions.create(
            model="gpt-4o",
            messages=augmented_messages,
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=1200,
        )

        final_msg = final.choices[0].message
        raw = (final_msg.content or "").strip()
        if not raw:
            raise ValueError("[references] GPT가 응답을 반환하지 않았습니다.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"[References JSON Parse Error] raw={raw}")
            parsed = {"references": aggregated_refs} if aggregated_refs else {"references": []}

        # 상태: COMPLETED
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column="references_status",
            new_status="COMPLETED",
        )
        db.commit()

        return {"task": "references", "status": "COMPLETED", "output": parsed}

    except Exception as e:
        logger.error(f"[References Task Error] {e}", exc_info=True)
        try:
            repo.update_package_task_status(
                package_status_id=package_status_id,
                task_column="references_status",
                new_status="FAILED",
            )
            db.commit()
        except Exception as inner:
            logger.error("[References Task] FAILED 상태 업데이트 중 오류", exc_info=True)
            db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()
