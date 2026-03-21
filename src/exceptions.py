# --- CUSTOM EXCEPTIONS ---
class TutorExceptionError(Exception):
    """The base blueprint for all custom errors in our app."""

    def __init__(self, status_code: int, error_type: str, message: str, details: str = None):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.details = details


# Example of a specific error you can use anywhere in your code!
class DatabaseOfflineError(TutorExceptionError):
    def __init__(self, details: str = "Connection timed out."):
        super().__init__(
            status_code=503,
            error_type="DatabaseError",
            message="The university database is currently offline.",
            details=details,
        )
