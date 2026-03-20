import base64
from pathlib import Path
import sys

from openai import OpenAI
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.utils.prompt_loader import load_prompt

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class VisionOCRService:
    def __init__(self):
        self.client = client

    def extract_text_from_image(self, image_path: str) -> str:
        try:
            image_bytes = Path(image_path).read_bytes()
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            prompt = load_prompt("vision_ocr_prompt.j2", context={})

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}"
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
                max_tokens=1024,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])