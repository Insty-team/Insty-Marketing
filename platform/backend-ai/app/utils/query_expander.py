# 파일: /app/utils/query_expander.py

from __future__ import annotations

import json
from typing import List

from openai import OpenAI
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.utils.prompt_loader import load_prompt

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)

def expand_queries(
    user_query: str,
    *,
    model: str = "gpt-4o-mini",
    n: int = 5,
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> List[str]:
    try:
        system_prompt = load_prompt("query_expander_system_prompt.j2", context={})
        user_prompt = load_prompt("query_expander_user_prompt.j2", context={"q": user_query})

        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)

        seen, cleaned = set(), []
        for q in data.get("queries", []):
            cq = " ".join(q.split()).strip()
            key = cq.lower()
            if cq and key not in seen:
                seen.add(key)
                cleaned.append(cq)
            if len(cleaned) >= n:
                break

        return cleaned

    except Exception as e:
        raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
