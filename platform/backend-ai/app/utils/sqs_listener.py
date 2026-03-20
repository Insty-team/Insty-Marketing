from urllib.parse import unquote_plus, quote
from uuid import UUID
import boto3
import json
import time
import logging
import threading
from typing import Optional
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.services.video.video_transcription_service import VideoTranscriptionService
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.core.config import get_settings
from app.utils.s3_utils import save_failed_message_to_s3, extract_s3_key_safe as extract_s3_key

logger = logging.getLogger(__name__)

settings = get_settings()
QUEUE_URL = settings.SQS_QUEUE_URL
EXPECTED_TOPIC_ARN = settings.EXPECTED_TOPIC_ARN
MAX_RETRY = 3  # 최대 재시도 횟수


def start_sqs_listener():
    logger.info("SQS 리스너 루프 시작됨")

    sqs = boto3.client(
        "sqs",
        aws_access_key_id=settings.aws.access_key_id,
        aws_secret_access_key=settings.aws.secret_access_key,
        region_name=settings.aws.region_name,
    )

    def handle_message_thread(msg):
        message_id = msg.get("MessageId")
        s3_key = extract_s3_key(msg)
        try:
            logger.info(f"[{message_id}] 처리 시작 - S3 파일: {s3_key}")

            result = file_added_message_handler(msg)

            if result is True:
                logger.info(f"[{message_id}] 처리 완료 - S3 파일: {s3_key}")
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
            else:
                logger.warning(f"[{message_id}] 처리 실패 또는 불완전 - S3 파일: {s3_key}. 메시지 삭제")
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

        except Exception as e:
            logger.exception(f"[{message_id}] 처리 중 예외 발생 - S3 파일: {s3_key}: {e}")

            receive_count = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", "1"))

            if receive_count >= MAX_RETRY:
                logger.warning(f"[{message_id}] 재시도 {receive_count}회 초과 - 실패 메시지 S3 저장 및 삭제")
                try:
                    save_failed_message_to_s3(msg, reason=str(e))
                except Exception as s3err:
                    logger.error(f"S3에 실패 메시지 저장 실패: {s3err}")
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
            else:
                logger.info(f"[{message_id}] 재시도 {receive_count}회 - 메시지 유지 (다시 시도 예정)")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                AttributeNames=["All"]  # 재시도 횟수 확인에 필요
            )

            messages = response.get("Messages", [])

            if messages:
                logger.info(f"SQS로부터 {len(messages)}건의 메시지 수신")

            for msg in messages:
                threading.Thread(target=handle_message_thread, args=(msg,), daemon=True).start()

        except Exception as e:
            logger.exception("SQS 폴링 실패: %s", str(e))

        time.sleep(1)


def file_added_message_handler(msg) -> Optional[bool]:
    db: Session = SessionLocal()
    try:
        body = json.loads(msg["Body"])

        if body.get("TopicArn") != EXPECTED_TOPIC_ARN:
            return True  # 삭제

        sns_message = json.loads(body["Message"])
        record = sns_message["Records"][0]
        raw_s3_key = record["s3"]["object"]["key"]
        logger.info(f"raw_s3_key: {raw_s3_key}")

        s3_key = unquote_plus(raw_s3_key)
        
        parts = s3_key.split("/")
        if len(parts) < 5:
            raise APIException(ErrorCode.INVALID_INPUT, details=[f"Unexpected S3 key format: {s3_key}"])
        
        video_uuid = UUID(parts[3])

        repo = VideoCourseRepository(db)
        video = repo.get_video_by_uuid(video_uuid)
        if not video:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=[f"Video not found for s3key: {s3_key}"])

        file_url = f"https://{settings.aws.bucket_name}.s3.{settings.aws.region_name}.amazonaws.com/{s3_key}"

        service = VideoTranscriptionService()
        service.transcribe_from_url_async(file_url, video.id)

        return True  # 처리 완료 후 삭제

    except json.JSONDecodeError:
        raise APIException(ErrorCode.BAD_REQUEST_BODY, details=["Invalid JSON format in SQS message"])
    except KeyError as e:
        raise APIException(ErrorCode.INVALID_INPUT, details=[f"Missing key in SQS message: {e}"])
    except APIException:
        raise
    except Exception as e:
        raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
    finally:
        db.close()