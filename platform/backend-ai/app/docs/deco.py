def op(id: str, *, tags: list[str] | None = None):
    def _wrap(func):
        setattr(func, "__operation_id__", id)
        if tags:
            setattr(func, "__tags__", tags)
        return func
    return _wrap
