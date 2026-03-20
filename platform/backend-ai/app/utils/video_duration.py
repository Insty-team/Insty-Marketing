import json
import subprocess

class VideoDurationError(Exception):
    pass

def get_video_duration_seconds(file_path: str) -> float:
    try:
        # ffprobe 출력 포맷을 JSON으로 받아서 format.duration 읽기
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-print_format", "json",
                "-show_format",
                file_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        info = json.loads(result.stdout or "{}")
        duration_str = (info.get("format") or {}).get("duration")
        if not duration_str:
            raise VideoDurationError("ffprobe에서 duration을 찾지 못했습니다.")
        return float(duration_str)
    except subprocess.CalledProcessError as e:
        raise VideoDurationError(f"ffprobe 실행 실패: {e.stderr.strip()}") from e
    except Exception as e:
        raise VideoDurationError(str(e)) from e


def validate_video_length(file_path: str, max_seconds: int = 120) -> tuple[bool, float]:
    seconds = get_video_duration_seconds(file_path)
    return (seconds <= max_seconds, seconds)
