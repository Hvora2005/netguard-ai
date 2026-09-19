class AppError(Exception):
    """Raised for expected, user-facing failures (bad input, unsupported files, etc).

    Route handlers catch this and translate it into a clean HTTP error instead of
    letting a raw traceback leak to the client.
    """

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
