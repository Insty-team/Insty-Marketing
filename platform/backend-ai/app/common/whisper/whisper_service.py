import tempfile
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable
import openai
from pydub import AudioSegment
from langdetect import detect

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

MAX_API_FILE_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_DURATION_MS = 60 * 1000  # 1분


def _notify(cb: Optional[Callable[[str, int], None]], step: str, percent: int):
    if cb is None:
        return
    cb(step, percent)


class WhisperService:
    def __init__(self):
        settings = get_settings()
        openai.api_key = settings.openai.api_key
        self.model_name = "whisper-1"

    def transcribe_video(self, video_path: str, progress_callback: Optional[Callable[[str, int], None]] = None) -> dict:
        audio_path = self.extract_audio(video_path, progress_callback)
        try:
            return self.transcribe(audio_path, progress_callback)
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def extract_audio(self, video_path: str, progress_callback: Optional[Callable[[str, int], None]] = None) -> str:
        _notify(progress_callback, "오디오 추출 중", 30)

        ext = video_path.lower().split('.')[-1]
        if f".{ext}" not in [".mp4", ".mov", ".m4v", ".mp3", ".wav", ".flac"]:
            raise APIException(ErrorCode.BAD_REQUEST_BODY)

        try:
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "libmp3lame",
                "-y", temp_audio.name
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return temp_audio.name
        except Exception as e:
            print(f"[DEBUG] ffmpeg 실패: {str(e)}")
            raise APIException(
                ErrorCode.FAILED_NOT_FOUND_VOICE,
                details=["ffmpeg 처리 실패"]
            )

    def transcribe(self, audio_path: str, progress_callback: Optional[Callable[[str, int], None]] = None) -> dict:
        _notify(progress_callback, "오디오 분석 중", 40)

        try:
            file_size = os.path.getsize(audio_path)
        except Exception as e:
            print(f"[DEBUG] 오디오 파일 크기 조회 실패: {str(e)}")
            raise APIException(ErrorCode.BAD_REQUEST_BODY)

        if file_size <= MAX_API_FILE_SIZE:
            _notify(progress_callback, "AI가 파일을 분석 중", 50)

            try:
                result = self._transcribe_single_file(audio_path)
            except Exception as e:
                print(f"[DEBUG] Whisper 전사 실패: {str(e)}")
                raise APIException(ErrorCode.INTERNAL_ERROR)

            text = result["text"].strip()

            if not text or len(text.split()) < 2:
                raise APIException(ErrorCode.AUDIO_NO_SPEECH_DETECTED)

            _notify(progress_callback, "언어 감지 중", 80)

            try:
                language = detect(text)
                if not language or len(language) != 2:
                    raise ValueError()
            except Exception:
                raise APIException(ErrorCode.AUDIO_NO_SPEECH_DETECTED)

            _notify(progress_callback, "완료", 100)

            return {
                "text": text,
                "language_code": language,
                "model_version": self.model_name
            }

        # 긴 오디오 → 청크 분할 전사
        _notify(progress_callback, "청크 분할 중", 50)

        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            print(f"[DEBUG] 청크 분할 실패: {str(e)}")
            raise APIException(ErrorCode.BAD_REQUEST_BODY)

        chunks = [audio[i:i + CHUNK_DURATION_MS] for i in range(0, len(audio), CHUNK_DURATION_MS)]
        total_chunks = len(chunks)

        def process_chunk(idx_chunk):
            idx, chunk = idx_chunk
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                chunk.export(f.name, format="mp3", bitrate="64k")
                if os.path.getsize(f.name) > MAX_API_FILE_SIZE:
                    return ""
                try:
                    return self._transcribe_single_file(f.name)["text"].strip()
                except Exception:
                    return ""
                finally:
                    os.remove(f.name)

        texts = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for idx, text in enumerate(executor.map(process_chunk, enumerate(chunks))):
                texts.append(text)
                progress = 50 + int((idx + 1) / total_chunks * 70)
                _notify(progress_callback, f"청크 {idx + 1}/{total_chunks} 전사 중", progress)

        full_text = "\n".join([t for t in texts if t]).strip()

        if not full_text or len(full_text.split()) < 2:
            raise APIException(ErrorCode.AUDIO_NO_SPEECH_DETECTED)

        _notify(progress_callback, "언어 감지 중", 95)

        try:
            language = detect(full_text)
            if not language or len(language) != 2:
                raise ValueError()
        except Exception:
            raise APIException(ErrorCode.AUDIO_NO_SPEECH_DETECTED)

        _notify(progress_callback, "완료", 100)

        return {
            "text": full_text,
            "language_code": language,
            "model_version": self.model_name
        }

    def _transcribe_single_file(self, path: str) -> dict:
        try:
            with open(path, "rb") as f:
                response = openai.audio.transcriptions.create(
                    model=self.model_name,
                    file=f
                )
            return {"text": response.text}
        except Exception as e:
            print(f"[DEBUG] OpenAI Whisper API 실패: {str(e)}")
            raise APIException(ErrorCode.INTERNAL_ERROR)
