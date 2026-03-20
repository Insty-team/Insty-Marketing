from sqlalchemy.orm import Session
from app.models.video import VideoSpeechTextTable, VideoCourse
import datetime

class VideoSpeechTextRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(  # 음성 인식 텍스트 레코드 생성
        self,
        video_id: int,
        speech_text_url: str,
        model_version: str,
        language_code: str
    ) -> VideoSpeechTextTable:
        now = datetime.datetime.utcnow()
        new_entry = VideoSpeechTextTable(
            video_id=video_id,
            speech_text_url=speech_text_url,
            model_version=model_version,
            language_code=language_code,
            created_at=now,
            updated_at=now
        )
        self.db.add(new_entry)
        self.db.commit()
        self.db.refresh(new_entry)
        return new_entry

    def get_by_video_id(self, video_id: int) -> list[VideoSpeechTextTable]:  # 영상 ID로 음성 인식 목록 조회
        return (
            self.db.query(VideoSpeechTextTable)
            .filter(VideoSpeechTextTable.video_id == video_id)
            .order_by(VideoSpeechTextTable.created_at.desc())
            .all()
        )
        
    def delete_by_video_id(self, video_id: int) -> bool:
        row = (
            self.db.query(VideoSpeechTextTable)
            .filter(VideoSpeechTextTable.video_id == video_id, VideoSpeechTextTable.is_deleted == False)
            .first()
        )
        if row:
            row.is_deleted = True
            self.db.commit()
            return True
        return False

    def delete_by_user_id(self, user_id: int) -> tuple[list[int], int]:
        # 1. 먼저 삭제 대상 video_id 조회 (is_deleted == False인 것들만)
        video_ids_to_delete = (
            self.db.query(VideoSpeechTextTable.video_id)
            .join(VideoCourse, VideoCourse.id == VideoSpeechTextTable.video_id)
            .filter(
                VideoCourse.user_id == user_id,
                VideoSpeechTextTable.is_deleted == False
            )
            .distinct()
            .all()
        )
        video_ids = [v[0] for v in video_ids_to_delete]

        # 2. video_course 하위 모든 video_speech_texts 삭제 (상태 관계 없이)
        subquery = (
            self.db.query(VideoCourse.id)
            .filter(VideoCourse.user_id == user_id)
            .subquery()
        )

        deleted_count = (
            self.db.query(VideoSpeechTextTable)
            .filter(VideoSpeechTextTable.video_id.in_(subquery))
            .update(
                {
                    VideoSpeechTextTable.is_deleted: True,
                    VideoSpeechTextTable.updated_at: datetime.datetime.utcnow()
                },
                synchronize_session=False
            )
        )

        return video_ids, deleted_count