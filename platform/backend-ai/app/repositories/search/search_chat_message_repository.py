from sqlalchemy.orm import Session
from app.models.search import SearchCourseMessage
from app.models.search import SearchCourseResultLog


class SearchCourseMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        sender_type: str,
        message_text: str,
        has_recommendation: bool
    ) -> SearchCourseMessage:
        new_message = SearchCourseMessage(
            user_id=user_id,
            sender_type=sender_type,
            message_text=message_text,
            has_recommendation=has_recommendation
        )
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        return new_message

    def get_by_user(self, user_id: int) -> list[SearchCourseMessage]:
        return (
            self.db.query(SearchCourseMessage)
            .filter(SearchCourseMessage.user_id == user_id)
            .order_by(SearchCourseMessage.created_at.desc())
            .all()
        )
        
    def get_max_order(self, user_id: int) -> int:
        result = (
            self.db.query(SearchCourseMessage.message_order)
            .filter(SearchCourseMessage.user_id == user_id)
            .order_by(SearchCourseMessage.message_order.desc())
            .first()
        )
        return result[0] if result else 0
    
    def update_has_recommendation(self, message_id: int, has_recommendation: bool) -> None:
        message = self.db.query(SearchCourseMessage).filter(SearchCourseMessage.id == message_id).first()
        if message:
            message.has_recommendation = has_recommendation
            self.db.commit()
            self.db.refresh(message)
            

    def get_message_history_with_courses(self, user_id: int) -> list[dict]:
        messages = (
            self.db.query(SearchCourseMessage)
            .filter(SearchCourseMessage.user_id == user_id)
            .order_by(SearchCourseMessage.created_at.asc())
            .all()
        )

        result = []

        for message in messages:
            base_data = {
                "message_id": message.id,
                "sender": message.sender_type,
                "created_at": message.created_at,
            }

            if message.sender_type == "user":
                result.append({
                    **base_data,
                    "content": message.message_text,
                })

            elif message.sender_type == "assistant":
                # 성공한 추천인 경우 → course_ids 포함
                if message.has_recommendation:
                    target_user_message_id = message.id - 1
                    result_logs = (
                        self.db.query(SearchCourseResultLog)
                        .filter(SearchCourseResultLog.message_id == target_user_message_id)
                        .order_by(SearchCourseResultLog.rank.asc())
                        .all()
                    )
                    course_ids = [log.course_id for log in result_logs]

                    result.append({
                        **base_data,
                        "content": message.message_text,
                        "course_ids": course_ids
                    })
                else:
                    # 실패한 추천도 챗봇 메시지로 포함
                    result.append({
                        **base_data,
                        "content": message.message_text
                        # course_ids 없음
                    })

        return result
    
    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(SearchCourseMessage)
            .filter(SearchCourseMessage.user_id == user_id)
            .delete(synchronize_session=False)
        )


