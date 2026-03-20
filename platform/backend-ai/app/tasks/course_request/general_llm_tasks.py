import logging
import json
from celery import shared_task
from app.core.db import get_db_session
from app.repositories.course.course_request_repository import CourseRequestRepository
from app.core.config import get_settings
from openai import OpenAI
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)
settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def run_llm_generation_task(
    self,
    *,
    package_status_id: int,
    field_values: dict,
    task_type: str,  # e.g., "summary", "section_plan", "script", "checklist"
):
    db = get_db_session()

    TASK_CONFIG = {
        "summary": {
            "prompt_file": "summary_course_request_prompt.j2",
            "task_column": "summary_status",
            "user_message": "요약 정보를 생성해줘."
        },
        "section_plan": {
            "prompt_file": "section_plan_prompt.j2",
            "task_column": "section_plan_status",
            "user_message": "섹션 계획을 생성해줘."
        },
        "script": {
            "prompt_file": "script_generation_prompt.j2",
            "task_column": "script_status",
            "user_message": "스크립트를 작성해줘."
        },
        "checklist": {
            "prompt_file": "production_checklist_prompt.j2",
            "task_column": "checklist_status",
            "user_message": "제작 체크리스트를 생성해줘."
        },
    }

    try:
        if task_type not in TASK_CONFIG:
            raise ValueError(f"지원되지 않는 task_type입니다: {task_type}")

        config = TASK_CONFIG[task_type]
        repo = CourseRequestRepository(db)

        # 상태 업데이트: PROCESSING
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column=config["task_column"],
            new_status="PROCESSING"
        )
        db.commit()

        prompt = load_prompt(config["prompt_file"], {"fields": field_values})

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": config["user_message"]}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=1000
        )

        raw = response.choices[0].message.content.strip()
        
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"[{task_type}] 결과 JSON 파싱 실패: {raw}")


        # 상태 업데이트: COMPLETED
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column=config["task_column"],
            new_status="COMPLETED"
        )
        db.commit()

        return {
            "task": task_type,
            "status": "COMPLETED",
            "output": parsed
        }

    except Exception as e:
        logger.error(f"[{task_type.capitalize()} Task Error] {e}", exc_info=True)
        try:
            repo.update_package_task_status(
                package_status_id=package_status_id,
                task_column=config["task_column"],
                new_status="FAILED"
            )
            db.commit()
        except Exception as inner:
            logger.error(f"[{task_type.capitalize()} Task] FAILED 상태 업데이트 실패: {inner}", exc_info=True)
            db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()
