import re

def clean_gpt_text(text: str, take_first_line: bool = True) -> str:  # GPT 응답 텍스트 정제 (따옴표 제거, 첫 줄만 추출)
    cleaned = text.strip()

    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]

    cleaned = re.sub(r'\\"', '"', cleaned)

    if take_first_line:
        cleaned = cleaned.splitlines()[0].strip()

    return cleaned


def enforce_html_breaks(text: str) -> str:  # 줄바꿈(\n)을 <br>로 변환하여 HTML에서 줄바꿈 처리
    text = re.sub(r'\n{2,}', '<br><br>', text)
    text = re.sub(r'\n', '<br>', text)
    return text


def process_gpt_response(text: str, for_html: bool = False, take_first_line: bool = False) -> str:
    cleaned = text.strip()

    if cleaned.startswith('"""') and cleaned.endswith('"""'):
        cleaned = cleaned[3:-3].strip()
    elif cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()

    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    cleaned = re.sub(r'\\"', '"', cleaned)

    if take_first_line:
        cleaned = cleaned.splitlines()[0].strip()

    if for_html:
        cleaned = enforce_html_breaks(cleaned)

    return cleaned