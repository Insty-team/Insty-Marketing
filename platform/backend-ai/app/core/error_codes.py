from enum import Enum

class ErrorCode(Enum):
    INVALID_INPUT = ("AI_COMMON_001", "입력 데이터가 유효하지 않습니다.", 400)
    UNAUTHORIZED = ("AI_COMMON_002", "인증이 필요합니다.", 401)
    FORBIDDEN = ("AI_COMMON_003", "해당 작업을 수행할 권한이 없습니다.", 403)
    RESOURCE_NOT_FOUND = ("AI_COMMON_004", "요청한 리소스를 찾을 수 없습니다.", 404)
    API_NOT_FOUND = ("AI_COMMON_005", "존재하지 않는 API입니다.", 404)
    CONFLICT = ("AI_COMMON_006", "리소스 충돌이 발생했습니다.", 409)
    PARAMETER_VALIDATION_ERROR = ("AI_COMMON_007", "파라미터 검증에 실패했습니다.", 422)
    BAD_REQUEST_BODY = ("AI_COMMON_008", "요청 형식이 잘못되었습니다.", 422)
    INVALID_TYPE_PARAMETER = ("AI_COMMON_009", "파라미터 타입이 유효하지 않습니다.", 422)
    INTERNAL_ERROR = ("AI_COMMON_010", "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", 500)
    DB_CONNECTION_FAILED = ("AI_COMMON_011", "데이터베이스 연결에 실패했습니다. 서버 상태를 확인해주세요.", 500)

    AUDIO_NO_SPEECH_DETECTED = ("AI_WHISPER_001", "음성이 감지되지 않았습니다. 노이즈 또는 음악일 수 있습니다.", 422)

    VIDEO_ENCODING_NOT_READY = ("AI_VIDEO_001", "비디오 인코딩이 아직 완료되지 않았습니다.", 400)
    FAILED_INVALID_VIDEO_LENGTH = ("AI_VIDEO_002", "비디오 길이가 유효하지 않습니다.", 400)
    FAILED_NOT_FOUND_VOICE = ("AI_VIDEO_003", "음성 데이터를 찾을 수 없습니다.", 400)
    ANALYSIS_NOT_READY = ("AI_VIDEO_004", "영상 분석이 아직 완료되지 않았습니다.", 400)
    ANALYSIS_FAILED = ("AI_VIDEO_005", "영상 분석에 실패한 상태입니다.", 400)
    NO_UPLOADED_VIDEOS = ("AI_VIDEO_006", "업로드된 영상이 없습니다.", 400)

    VECTOR_UPSERT_FAILED = ("AI_VECTOR_001", "강의 요청 벡터 저장에 실패했습니다. 다시 시도해주세요.", 500)
    NO_SIMILAR_REQUESTS_FOUND = ("AI_VECTOR_002", "업로드된 영상과 유사한 강의 요청이 없습니다.", 404)
    FAILED_TO_LOAD_REQUEST_DETAILS = ("AI_VECTOR_003", "추천 요청 정보를 불러오지 못했습니다. 관리자에게 문의해주세요.", 500)
    NO_VECTOR_MATCHES_FOUND = ("AI_VECTOR_004", "업로드된 영상에서 유사한 강의 요청 벡터를 찾지 못했습니다.",404)

    FINAL_RESULT_NOT_READY = ("AI_COURSE_REQUEST_001", "아직 모든 태스크가 완료되지 않아 결과를 조회할 수 없습니다.", 400)


    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
