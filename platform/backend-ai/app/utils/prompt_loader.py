from jinja2 import Environment, FileSystemLoader
from app.core.config import get_settings

settings = get_settings()

# 언어별 지시 메시지
LANGUAGE_INSTRUCTIONS = {
    "en": "**중요: 모든 출력은 반드시 영어로 작성해야 합니다.**",
    "ko": "**중요: 모든 출력은 반드시 한국어로 작성해야 합니다.**"
}

# 언어별 설정 값
LANGUAGE_CONFIG = {
    "en": {
        "language_name": "영어",
        "price_description": "`price`는 영상의 난이도, 길이, 내용의 깊이 등을 고려해 **적절한 유료 가격**(예: `\"$29\"`, `\"$99\"`, `\"$199\"` 등)을 **USD 형식 문자열로** 작성해 주세요. `\"Free\"` 또는 `\"$0\"`은 절대 사용하지 마세요.",
    },
    "ko": {
        "language_name": "한국어",
        "price_description": "`price`는 영상의 난이도, 길이, 내용의 깊이 등을 고려해 **적절한 유료 가격**(예: `\"29,000원\"`, `\"99,000원\"`, `\"199,000원\"` 등)을 **원화 형식 문자열로** 작성해 주세요. `\"무료\"` 또는 `\"0원\"`은 절대 사용하지 마세요.",
    }
}

def load_prompt(
    template_name: str, 
    context: dict = None, 
    output_language: str = None
) -> str:
    # 언어 설정 (파라미터 > 설정 > 기본값)
    if output_language is None:
        output_language = getattr(settings, 'DEFAULT_OUTPUT_LANGUAGE', 'en')
    
    # 기본 컨텍스트 준비
    if context is None:
        context = {}
    
    # 언어 변수 자동 주입
    prompt_context = {
        **context,
        "output_language": output_language,
        "language_instruction": LANGUAGE_INSTRUCTIONS.get(output_language, LANGUAGE_INSTRUCTIONS["en"]),
        **LANGUAGE_CONFIG.get(output_language, LANGUAGE_CONFIG["en"])
    }
    
    env = Environment(
        loader=FileSystemLoader(f"{settings.base_dir}/app/prompts"),
        autoescape=False
    )
    template = env.get_template(template_name)
    return template.render(prompt_context)
