import boto3
import mimetypes
import tempfile
import json
import time
import uuid
import os
from urllib.parse import urlparse, unquote
from pathlib import Path
from botocore.exceptions import ClientError
from app.core.config import get_settings

settings = get_settings()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws.access_key_id,
    aws_secret_access_key=settings.aws.secret_access_key,
    region_name=settings.aws.region_name,
)


def upload_file_to_s3(local_path: str, s3_key: str, content_type: str = None, bucket_name: str = None) -> str:
    bucket = bucket_name or settings.aws.bucket_name

    if content_type is None:
        content_type, _ = mimetypes.guess_type(local_path)

    s3_client.upload_file(
        Filename=local_path,
        Bucket=bucket,
        Key=s3_key,
        ExtraArgs={"ContentType": content_type or "application/octet-stream"}
    )

    return f"https://{bucket}.s3.{settings.aws.region_name}.amazonaws.com/{s3_key}"


def download_file_from_s3(s3_url: str) -> str:
    parsed = urlparse(s3_url)
    bucket = parsed.netloc.split(".")[0]
    key = parsed.path.lstrip("/")
    ext = Path(key).suffix or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        s3_client.download_fileobj(bucket, key, tmp)
        return tmp.name


def delete_file_from_s3(s3_url: str):
    parsed = urlparse(s3_url)
    bucket = parsed.netloc.split(".")[0]
    key = parsed.path.lstrip("/")
    s3_client.delete_object(Bucket=bucket, Key=key)


def generate_cloudfront_url(s3_key: str) -> str:
    base_url = settings.aws.cloudfront_domain.rstrip("/")
    return f"{base_url}/{s3_key.lstrip('/')}"


def ensure_bucket_exists(bucket_name: str):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": settings.aws.region_name},
            )
        elif error_code == 403:
            raise PermissionError(f"S3 버킷 접근 권한 없음: {bucket_name}")
        else:
            raise


def extract_s3_key_safe(msg: dict) -> str:
    try:
        body = json.loads(msg["Body"])
        sns_message = json.loads(body["Message"])
        record = sns_message["Records"][0]
        return unquote(record["s3"]["object"]["key"])
    except Exception:
        return "UNKNOWN"


def save_failed_message_to_s3(message: dict, reason: str, bucket_name: str = None):
    bucket = bucket_name or f"{settings.aws.bucket_name}-failed-messages"
    ensure_bucket_exists(bucket)

    s3_key = f"failed_messages/{uuid.uuid4()}.json"
    data = {
        "reason": reason,
        "timestamp": time.time(),
        "message_id": message.get("MessageId"),
        "topic_arn": json.loads(message.get("Body", "{}")).get("TopicArn", "UNKNOWN"),
        "s3_key": extract_s3_key_safe(message),
        "raw_message": message
    }

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp_file:
        json.dump(data, tmp_file, ensure_ascii=False, indent=2)
        tmp_file_path = tmp_file.name

    upload_file_to_s3(tmp_file_path, s3_key, content_type="application/json", bucket_name=bucket)
    os.remove(tmp_file_path)