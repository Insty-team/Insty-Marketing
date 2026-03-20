from sqlalchemy.orm import Session
from datetime import datetime

from app.models.course import PurchaseAssistantUsage


class PurchaseAssistantUsageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, course_id: int) -> PurchaseAssistantUsage:
        new_usage = PurchaseAssistantUsage(
            user_id=user_id,
            course_id=course_id,
            usage_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(new_usage)
        self.db.commit()
        self.db.refresh(new_usage)
        return new_usage

    def get_by_user_and_course(self, user_id: int, course_id: int) -> PurchaseAssistantUsage | None:
        return (
            self.db.query(PurchaseAssistantUsage)
            .filter(
                PurchaseAssistantUsage.user_id == user_id,
                PurchaseAssistantUsage.course_id == course_id
            )
            .first()
        )

    def increment_usage(self, user_id: int, course_id: int) -> PurchaseAssistantUsage:
        usage = self.get_by_user_and_course(user_id, course_id)
        if usage is None:
            return self.create(user_id, course_id)

        usage.usage_count += 1
        usage.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(usage)
        return usage
    
    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(PurchaseAssistantUsage)
            .filter(PurchaseAssistantUsage.user_id == user_id)
            .delete(synchronize_session=False)
        )
