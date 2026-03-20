import redis
import json

redis_client = redis.Redis(host="redis", port=6379, db=2)

def publish_video_task_status(
    video_id: int,
    step: str,
    progress: int,
    status: str = "PROCESSING",
    reason: str | None = None, 
    ttl_seconds: int = 3600,
    prefix: str = "task"
):
    message = {
        "video_id": video_id,
        "step": step,
        "progress": progress,
        "status": status,
    }

    if reason:
        message["reason"] = reason  # 실패 사유 포함

    redis_key = f"video:{prefix}:{video_id}"

    # Redis에 상태 저장 (TTL 포함)
    redis_client.set(redis_key, json.dumps(message), ex=ttl_seconds)

    # Pub/Sub으로 상태 발행
    redis_client.publish("video_task_updates", json.dumps(message))
