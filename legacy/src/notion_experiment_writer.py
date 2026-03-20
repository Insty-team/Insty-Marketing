"""실험 파이프라인 전용 Notion DB 연동.

기존 notion_writer.py와 별도로, 레퍼런스 카드 DB와 프로덕션 가이드 DB를 관리한다.
"""

import json
import logging
from typing import Optional

from notion_client import Client
from notion_client.errors import APIResponseError

from config.settings import NOTION_TOKEN, NOTION_REFERENCE_DB_ID, NOTION_GUIDE_DB_ID

logger = logging.getLogger(__name__)


def _get_client() -> Client:
    """Notion 클라이언트 생성."""
    if not NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN이 설정되지 않았습니다.")
    return Client(auth=NOTION_TOKEN)


# ============================================================
# 레퍼런스 카드 DB
# ============================================================

# 메모리 내 중복 추적 (세션당)
_saved_video_ids: set[str] = set()


def check_reference_duplicate(video_id: str) -> bool:
    """레퍼런스 DB에서 video_id 중복 체크 (세션 내 메모리 기반)."""
    return video_id in _saved_video_ids


def save_reference(video: dict, analysis: dict) -> Optional[str]:
    """레퍼런스 카드를 Notion에 저장.

    Args:
        video: shorts_discovery에서 반환된 영상 딕셔너리
        analysis: reference_analyzer에서 반환된 분석 결과

    Returns:
        생성된 Notion 페이지 ID 또는 None
    """
    if not NOTION_REFERENCE_DB_ID:
        logger.warning("NOTION_REFERENCE_DB_ID 미설정 — 레퍼런스 저장 건너뜀")
        return None

    vid = video["video_id"]
    if check_reference_duplicate(vid):
        logger.info(f"중복 레퍼런스 건너뜀: {vid}")
        return None

    notion = _get_client()
    _saved_video_ids.add(vid)

    # 안전하게 engagement rate 계산
    views = max(video.get("views", 1), 1)
    engagement_rate = round(
        (video.get("likes", 0) + video.get("comments", 0)) / views * 100, 2
    )

    properties = {
        "Title": {"title": [{"text": {"content": video["title"][:100]}}]},
        "Status": {"select": {"name": "Analyzed"}},
        "Platform": {"select": {"name": "YouTube Shorts"}},
        "URL": {"url": video.get("url", "")},
        "Channel": {"rich_text": [{"text": {"content": video.get("channel", "")}}]},
        "Views": {"number": video.get("views", 0)},
        "Engagement Rate": {"number": engagement_rate},
        "Hook Type": {"select": {"name": analysis.get("hook_type", "unknown")[:100]}},
        "Video Format": {"select": {"name": analysis.get("video_format", "unknown")[:100]}},
        "Content Framework": {"select": {"name": analysis.get("content_framework", "unknown")[:100]}},
        "Length (sec)": {"number": video.get("duration_seconds", 0)},
        "Cut Frequency": {"rich_text": [{"text": {"content": analysis.get("cut_frequency", "")}}]},
        "CTA Type": {"rich_text": [{"text": {"content": analysis.get("cta_type", "")}}]},
        "Score": {"number": round(video.get("score", 0), 1)},
        "Keyword": {"rich_text": [{"text": {"content": video.get("keyword", "")}}]},
    }

    # 분석 상세 내용을 page body blocks로
    children = _analysis_to_blocks(analysis)

    try:
        page = notion.pages.create(
            parent={"database_id": NOTION_REFERENCE_DB_ID},
            properties=properties,
            children=children,
        )
        page_id = page["id"]
        logger.info(f"레퍼런스 저장 완료: {video['title'][:50]} → {page_id}")
        return page_id
    except APIResponseError as e:
        logger.error(f"레퍼런스 저장 실패: {e}")
        return None


def _analysis_to_blocks(analysis: dict) -> list[dict]:
    """분석 결과를 Notion block 리스트로 변환 (한국어)."""
    blocks = []

    # 핵심 요약
    summary = analysis.get("content_summary_ko", "")
    if summary:
        _add_section(blocks, "핵심 요약", summary)

    # 잘 된 이유
    why = analysis.get("why_it_works_ko", "")
    if why:
        _add_section(blocks, "이 영상이 잘 된 이유", why)

    # Hook 분석
    _add_section(blocks, "Hook 분석", (
        f"유형: {analysis.get('hook_type', '?')}\n"
        f"내용: {analysis.get('hook_text_ko', analysis.get('hook_text', '?'))}\n"
        f"분석: {analysis.get('hook_analysis_ko', analysis.get('hook_analysis', '?'))}"
    ))

    # 구조 분석
    breakdown = analysis.get("structure_breakdown", [])
    if breakdown:
        _add_heading(blocks, "구조 분석")
        for seg in breakdown:
            if isinstance(seg, dict):
                content = seg.get("content_ko", seg.get("content", ""))
                text = (
                    f"[{seg.get('timestamp', '?')}] "
                    f"{seg.get('element', '?')}: "
                    f"{content} "
                    f"(visual: {seg.get('visual_type', '?')})"
                )
                _add_bullet(blocks, text)

    # 핵심 패턴
    patterns = analysis.get("key_patterns_ko", analysis.get("key_patterns", []))
    if patterns:
        _add_section(blocks, "핵심 패턴", "\n".join(f"• {p}" for p in patterns))

    # Engagement Triggers
    triggers = analysis.get("engagement_triggers", [])
    if triggers:
        _add_section(blocks, "Engagement Triggers", ", ".join(triggers))

    # Faceless 분석
    is_faceless = analysis.get("is_faceless", False)
    faceless_type = analysis.get("faceless_type", "unknown")
    faceless_prod = analysis.get("faceless_production_ko", "")
    tools = analysis.get("suggested_tools_ko", "")

    faceless_text = f"Faceless 여부: {'YES' if is_faceless else 'NO'}"
    faceless_text += f"\n유형: {faceless_type}"
    if faceless_prod:
        faceless_text += f"\n제작 방식: {faceless_prod}"
    if tools:
        faceless_text += f"\n추천 도구: {tools}"
    est_time = analysis.get("estimated_production_time_minutes", "")
    if est_time:
        faceless_text += f"\n예상 제작 시간: {est_time}분"
    _add_section(blocks, "Faceless 제작 분석", faceless_text)

    # 우리가 배울 점
    lessons = analysis.get("lessons_for_us_ko", "")
    if lessons:
        _add_section(blocks, "우리가 배울 점", lessons)

    # 재현 가능성
    _add_section(blocks, "재현 가능성", (
        f"점수: {analysis.get('replicability_score', '?')}/10\n"
        f"노트: {analysis.get('replicability_notes_ko', analysis.get('replicability_notes', '?'))}"
    ))

    return blocks


# ============================================================
# 프로덕션 가이드 DB
# ============================================================

def save_production_guide(
    guide: dict,
    source_video: dict,
    reference_video: dict,
) -> Optional[str]:
    """프로덕션 가이드를 Notion에 저장.

    Args:
        guide: production_guide_generator에서 반환된 가이드
        source_video: 소스 콘텐츠 메타데이터
        reference_video: 레퍼런스 영상 메타데이터

    Returns:
        생성된 Notion 페이지 ID 또는 None
    """
    if not NOTION_GUIDE_DB_ID:
        logger.warning("NOTION_GUIDE_DB_ID 미설정 — 가이드 저장 건너뜀")
        return None

    notion = _get_client()

    title = guide.get("title_ko", source_video.get("title", "제목 없음"))[:100]

    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Status": {"select": {"name": "Ready to Shoot"}},
        "Reference URL": {"url": reference_video.get("url", "")},
        "Source URL": {"url": source_video.get("url", "")},
        "Hook Type": {"rich_text": [{"text": {"content": guide.get("hook_recommendation", {}).get("type", "")}}]},
        "Target Length": {"number": guide.get("target_length_seconds", 0)},
        "Difficulty": {"select": {"name": guide.get("difficulty", "medium")}},
    }

    children = _guide_to_blocks(guide)

    try:
        page = notion.pages.create(
            parent={"database_id": NOTION_GUIDE_DB_ID},
            properties=properties,
            children=children,
        )
        page_id = page["id"]
        logger.info(f"가이드 저장 완료: {title} → {page_id}")
        return page_id
    except APIResponseError as e:
        logger.error(f"가이드 저장 실패: {e}")
        return None


def _guide_to_blocks(guide: dict) -> list[dict]:
    """프로덕션 가이드를 Notion block 리스트로 변환.

    영상 스크립트는 영어, 제작 방법은 한국어.
    """
    blocks = []

    # 영어 보이스오버 스크립트
    script = guide.get("script_en", guide.get("script_ko", {}))
    voiceover = script.get("voiceover_full", "")
    if voiceover:
        _add_section(blocks, "Voiceover Script (English)", voiceover)

    # 핵심 포인트
    points = script.get("talking_points", [])
    if points:
        _add_heading(blocks, "Talking Points")
        for p in points:
            _add_bullet(blocks, str(p))

    # Hook 추천
    hook = guide.get("hook_recommendation", {})
    if hook:
        hook_text = hook.get("text_en", hook.get("text_ko", "?"))
        hook_why = hook.get("효과_분석", hook.get("why_it_works", "?"))
        _add_section(blocks, "Hook 추천", (
            f"유형: {hook.get('type', '?')}\n"
            f"대사 (EN): {hook_text}\n"
            f"효과 분석: {hook_why}"
        ))

    # Shot Breakdown (초별 촬영 가이드)
    shots = guide.get("shot_breakdown", [])
    if shots:
        _add_heading(blocks, "촬영 가이드 (Shot by Shot)")
        for shot in shots:
            if isinstance(shot, dict):
                time_range = shot.get("time", "?")
                shot_type = shot.get("shot_type", "?")
                vo = shot.get("voiceover_en", shot.get("voiceover_ko", ""))
                text_ol = shot.get("text_overlay_en", shot.get("text_overlay_ko", ""))
                filming = shot.get("촬영_지시", shot.get("visual_instruction", ""))
                editing = shot.get("편집_지시", "")
                transition = shot.get("transition", "none")

                text = f"[{time_range}] {shot.get('type', '?').upper()}"
                text += f"\n  샷: {shot_type}"
                if vo:
                    text += f"\n  대사 (EN): \"{vo}\""
                if text_ol:
                    text += f"\n  자막 (EN): \"{text_ol}\""
                if filming:
                    text += f"\n  촬영: {filming}"
                if editing:
                    text += f"\n  편집: {editing}"
                if transition != "none":
                    text += f"\n  전환: {transition}"

                _add_numbered(blocks, text)

    # 편집 가이드 (한국어)
    edit = guide.get("편집_가이드", guide.get("editing_guide", {}))
    if edit:
        edit_text = f"컷 리듬: {edit.get('컷_리듬', edit.get('cut_rhythm', '?'))}"
        edit_text += f"\n자막 스타일: {edit.get('자막_스타일', edit.get('subtitle_style', '?'))}"
        edit_text += f"\n음악: {edit.get('배경음악', edit.get('music_suggestion', '?'))}"
        edit_text += f"\n색보정: {edit.get('색보정', edit.get('color_grade', '?'))}"

        zooms = edit.get("줌_포인트", edit.get("zoom_points", []))
        if zooms:
            edit_text += "\n\n줌 포인트:"
            for z in zooms:
                edit_text += f"\n  • {z}"

        _add_section(blocks, "편집 가이드", edit_text)

    # 플랫폼별 팁
    tips = guide.get("platform_tips", {})
    if tips:
        tip_text = ""
        if tips.get("youtube_shorts"):
            tip_text += f"YouTube Shorts: {tips['youtube_shorts']}\n"
        if tips.get("instagram_reels"):
            tip_text += f"Instagram Reels: {tips['instagram_reels']}"
        if tip_text:
            _add_section(blocks, "플랫폼 최적화", tip_text)

    # 영어 캡션 + 해시태그
    caption_en = guide.get("caption_en", "")
    if caption_en:
        _add_section(blocks, "Caption (English)", caption_en)

    hashtags_en = guide.get("hashtags_en", guide.get("hashtags", []))
    if hashtags_en:
        _add_section(blocks, "Hashtags (English)", " ".join(str(h) for h in hashtags_en))

    # 한국어 캡션 + 해시태그
    caption_ko = guide.get("caption_ko", "")
    if caption_ko:
        _add_section(blocks, "캡션 (한국어)", caption_ko)

    hashtags_ko = guide.get("hashtags_ko", [])
    if hashtags_ko:
        _add_section(blocks, "해시태그 (한국어)", " ".join(str(h) for h in hashtags_ko))

    # Faceless 제작 가이드
    fp = guide.get("faceless_production", {})
    if fp:
        fp_text = f"음성: {fp.get('voice_method', '?')}"
        ai_tool = fp.get("ai_voice_tool", "")
        if ai_tool and ai_tool != "없음":
            fp_text += f" ({ai_tool})"
        visuals = fp.get("visual_sources", [])
        if visuals:
            fp_text += f"\n비주얼 소스: {', '.join(visuals)}"
        edit_tool = fp.get("editing_tool", "")
        if edit_tool:
            fp_text += f"\n편집 도구: {edit_tool}"
        est = fp.get("예상_제작시간", "")
        if est:
            fp_text += f"\n예상 제작 시간: {est}"
        _add_section(blocks, "Faceless 제작 가이드", fp_text)

        # 제작 순서
        steps = fp.get("제작_순서", [])
        if steps:
            _add_heading(blocks, "제작 순서")
            for step in steps:
                _add_numbered(blocks, str(step))

    # 준비물 체크리스트 (한국어)
    checklist = guide.get("촬영_체크리스트", guide.get("filming_checklist", []))
    if checklist:
        _add_heading(blocks, "준비물 체크리스트")
        for item in checklist:
            _add_todo(blocks, str(item))

    return blocks


# ============================================================
# 성과 추적
# ============================================================

def update_guide_performance(
    page_id: str,
    metrics: dict,
    snapshot_type: str = "24h",
) -> bool:
    """가이드 페이지에 성과 데이터 업데이트.

    Args:
        page_id: Notion 페이지 ID
        metrics: {"views": int, "likes": int, "comments": int, "saves": int}
        snapshot_type: "24h" | "48h" | "7d"
    """
    notion = _get_client()

    properties = {}
    prefix = f"Views ({snapshot_type})"
    properties[prefix] = {"number": metrics.get("views", 0)}

    if snapshot_type == "7d":
        properties["Likes (7d)"] = {"number": metrics.get("likes", 0)}
        properties["Comments (7d)"] = {"number": metrics.get("comments", 0)}
        properties["Status"] = {"select": {"name": "Tracked"}}

    try:
        notion.pages.update(page_id=page_id, properties=properties)
        logger.info(f"성과 업데이트 ({snapshot_type}): {page_id}")
        return True
    except APIResponseError as e:
        logger.error(f"성과 업데이트 실패: {e}")
        return False


def update_guide_status(page_id: str, status: str) -> bool:
    """가이드 페이지 상태 업데이트."""
    notion = _get_client()
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Status": {"select": {"name": status}}},
        )
        return True
    except APIResponseError as e:
        logger.error(f"상태 업데이트 실패: {e}")
        return False


def set_published_url(page_id: str, url: str) -> bool:
    """업로드 후 Published URL 설정."""
    notion = _get_client()
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Published URL": {"url": url},
                "Status": {"select": {"name": "Published"}},
            },
        )
        return True
    except APIResponseError as e:
        logger.error(f"Published URL 설정 실패: {e}")
        return False


# ============================================================
# Notion Block 헬퍼
# ============================================================

def _add_heading(blocks: list, text: str):
    blocks.append({
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
        },
    })


def _add_paragraph(blocks: list, text: str):
    for i in range(0, len(text), 2000):
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text[i:i + 2000]}}],
            },
        })


def _add_section(blocks: list, heading: str, body: str):
    _add_heading(blocks, heading)
    _add_paragraph(blocks, body)


def _add_bullet(blocks: list, text: str):
    blocks.append({
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
        },
    })


def _add_numbered(blocks: list, text: str):
    blocks.append({
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
        },
    })


def _add_todo(blocks: list, text: str):
    blocks.append({
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "checked": False,
        },
    })
