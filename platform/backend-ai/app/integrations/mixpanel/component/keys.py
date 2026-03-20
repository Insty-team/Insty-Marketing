## 이벤트 공통 필드 키와 outcome 값 상수의 단일 출처

# 이벤트 공통 프로퍼티 키
FIELD_TOKEN = "token"
FIELD_DISTINCT_ID = "distinct_id"
FIELD_TIMESTAMP_MILLIS = "time"
FIELD_TRACK_OUTCOME = "track_outcome"

# 성공, 실패 값
OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_FAILURE = "FAILURE"

# Request 컨텍스트로부터 자동 주입되는 필드
FIELD_ENDPOINT = "endpoint"
FIELD_HTTP_METHOD = "http_method"