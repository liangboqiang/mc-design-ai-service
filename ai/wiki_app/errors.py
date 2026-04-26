from __future__ import annotations


class WikiAppError(Exception):
    code = "WIKI_APP_ERROR"
    status_code = 400

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code

    def to_dict(self) -> dict:
        return {"code": self.code, "message": str(self)}


class ActionNotFound(WikiAppError):
    code = "ACTION_NOT_FOUND"


class MissingRequiredParam(WikiAppError):
    code = "MISSING_REQUIRED_PARAM"


class PublishNotAllowed(WikiAppError):
    code = "PUBLISH_NOT_ALLOWED"
