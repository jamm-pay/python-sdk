from typing import Optional, Dict

# Statuses that mean "no such record", so a lookup returns None rather than raising.
#
# Only 404. The Node SDK also maps connect's InvalidArgument and PermissionDenied to
# null, but it can see the connect code per call site; this SDK sees an HTTP status, and
# both of those statuses are overloaded here:
#
#   403 - the platform_authn middleware returns it for "platform is not authorized to
#         act on behalf of this merchant", for platform-only endpoints, and for
#         platform-managed merchants. Those are authorization failures. Reporting them
#         as absence would tell a platform integrator "this merchant has no such
#         customer" when the truth is "you have no access to this merchant at all".
#   400 - the REST gateway returns it for a malformed body or a buf-validate rejection.
#         Swallowing that turns a rejected request into a silent "no such record", so an
#         integration doing `if get(email) is None: create(...)` creates a duplicate.
#
# A record that exists but is invisible to these credentials therefore raises rather
# than returning None. That is the safe direction: a caller can inspect an ApiError, but
# cannot recover information from a None that should have been an error.
NOT_FOUND_CODES = (404,)


class ApiError(Exception):
    """Legacy API error wrapper.

    Updated to align with enhanced client-side `ApiError` so downstream code can rely
    on attributes: message, code, status, error_type, details, response_headers, response_body.
    """

    def __init__(
        self,
        message: str = "",
        code: Optional[int] = None,
        status: Optional[int] = None,
        error_type: Optional[str] = None,
        details: Optional[Dict] = None,
        response_headers: Optional[Dict] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message  # ensure attribute exists
        self.code = code if code is not None else status
        self.status = status if status is not None else code
        self.error_type = error_type
        self.details = details or {}
        self.response_headers = response_headers
        self.response_body = response_body

    @classmethod
    def from_error(cls, error: Exception) -> "ApiError":
        """Convert arbitrary error into ApiError preserving rich fields when available."""
        if isinstance(error, cls):
            return error
        # If it's the newer client ApiError, just wrap its attributes
        code = getattr(error, "code", getattr(error, "status", None))
        status = getattr(error, "status", getattr(error, "code", None))
        message = getattr(error, "message", str(error))
        error_type = getattr(error, "error_type", None)
        details = getattr(error, "details", {}) or {}
        response_headers = getattr(error, "response_headers", None)
        response_body = getattr(error, "response_body", None)

        # Fallback inference from message if code/status missing
        msg_lower = message.lower()
        if code is None or status is None:
            if "404" in msg_lower or "not found" in msg_lower:
                code = code or 404
                status = status or 404
            elif "500" in msg_lower or "internal" in msg_lower:
                code = code or 500
                status = status or 500

        return cls(
            message=message,
            code=code,
            status=status,
            error_type=error_type,
            details=details,
            response_headers=response_headers,
            response_body=response_body,
        )
