"""Exceptions for Intervals.icu API client."""


class IntervalsAPIError(RuntimeError):
    """Raised for any Intervals.icu API request failure."""

    def __init__(self, message: str, status_code: int | None = None, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
