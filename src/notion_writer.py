"""Notion SDK를 이용한 Content Pipeline DB 저장."""

import json
import logging
from typing import Optional

from notion_client import Client
from notion_client.errors import APIResponseError

from config.settings import NOTION_TOKEN, NOTION_DB_ID

logger = logging.getLogger(__name__)


def get_notion_client() -> Client:
    """Notion 클라이언트 생성."""
    if not NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN이 설정되지 않았습니다.")
    return Client(auth=NOTION_TOKEN)


def check_duplicate(video_id: str) -> bool:
    """video_id 기준 중복 체크."""
    if not NOTION_DB_ID:
        logger.warning("NOTION_DB_ID 미설정 — 중복 체크 건너뜀")
        return False

    notion = get_notion_client()
    try:
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={
                "property": "YouTube URL",
                "url": {"contains": video_id},
            },
        )
        return len(results.get("results", [])) > 0
    except APIResponseError as e:
        logger.error(f"Notion 중복 체크 실패: {e}")
        return False


def _script_to_blocks(script: dict) -> list[dict]:
    """스크립트 딕셔너리를 Notion block 리스트로 변환.

    각 섹션을 heading_3 + paragraph 블록으로 분리하여
    rich_text 2000자 제한을 우회한다.
    """
    blocks = []

    # 섹션 순서
    section_order = [
        "hook", "why", "how",
        "tip1", "tip2", "tip3",
        "lesson", "application",
        "summary", "cta",
    ]

    for key in section_order:
        if key not in script:
            continue

        section = script[key]
        text = section.get("text", "")
        dur = section.get("duration", "")
        ts = section.get("source_timestamp", "")

        header = f"{key.upper()} ({dur})"
        if ts:
            header += f" [Source: {ts}]"

        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": header}}],
            },
        })

        # paragraph 텍스트도 2000자 제한이 있으므로 분할
        for i in range(0, len(text), 2000):
            chunk = text[i:i + 2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}],
                },
            })

    # Caption
    caption = script.get("caption", "")
    if caption:
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Caption"}}],
            },
        })
        for i in range(0, len(caption), 2000):
            chunk = caption[i:i + 2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}],
                },
            })

    # Hashtags
    hashtags = script.get("hashtags", "")
    if hashtags:
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Hashtags"}}],
            },
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": hashtags[:2000]}}],
            },
        })

    # CTA Keyword
    cta_kw = script.get("cta_keyword", "")
    if cta_kw:
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "CTA Keyword"}}],
            },
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": cta_kw}}],
            },
        })

    return blocks


def save_video(video: dict, script: Optional[dict] = None) -> Optional[str]:
    """영상 정보를 Notion DB에 저장.

    Args:
        video: youtube_discovery에서 반환된 영상 딕셔너리
        script: script_generator에서 반환된 스크립트 딕셔너리

    Returns:
        생성된 Notion 페이지 ID 또는 None
    """
    if not NOTION_DB_ID:
        logger.warning("NOTION_DB_ID 미설정 — Notion 저장 건너뜀")
        return None

    # 중복 체크
    if check_duplicate(video["video_id"]):
        logger.info(f"중복 영상 건너뜀: {video['video_id']}")
        return None

    notion = get_notion_client()

    properties = {
        "Title": {"title": [{"text": {"content": video["title"][:100]}}]},
        "Status": {"select": {"name": "Discovered" if not script else "Script Ready"}},
        "YouTube URL": {"url": video["url"]},
        "Channel": {"rich_text": [{"text": {"content": video["channel"]}}]},
        "Views": {"number": video["views"]},
        "Likes": {"number": video["likes"]},
        "Relevance Score": {"number": round(video.get("score", 0), 1)},
        "Keyword": {"rich_text": [{"text": {"content": video.get("keyword", "")}}]},
    }

    # CTA Keyword를 property에도 저장 (짧은 텍스트)
    if script and script.get("cta_keyword"):
        properties["CTA Keyword"] = {
            "rich_text": [{"text": {"content": script["cta_keyword"][:200]}}]
        }

    create_args = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
    }

    # 스크립트는 page body blocks로 저장 (2000자 제한 우회)
    if script:
        create_args["children"] = _script_to_blocks(script)

    try:
        page = notion.pages.create(**create_args)
        page_id = page["id"]
        logger.info(f"Notion 저장 완료: {video['title'][:50]} → {page_id}")
        return page_id
    except APIResponseError as e:
        logger.error(f"Notion 저장 실패: {e}")
        return None


def update_status(page_id: str, status: str) -> bool:
    """Notion 페이지 상태 업데이트."""
    notion = get_notion_client()
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Status": {"select": {"name": status}}},
        )
        return True
    except APIResponseError as e:
        logger.error(f"상태 업데이트 실패: {e}")
        return False
