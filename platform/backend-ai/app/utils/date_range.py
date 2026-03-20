from datetime import datetime, timedelta, date

def get_start_date_by_relative(relative_str: str) -> date:
    now = datetime.now()
    mapping = {
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1m": timedelta(days=30),
        "1y": timedelta(days=365),
    }

    if relative_str not in mapping:
        raise ValueError(f"지원하지 않는 relativeDate 값입니다: {relative_str}")

    return (now - mapping[relative_str]).date()
