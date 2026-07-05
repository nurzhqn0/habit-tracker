class DomainError(Exception):
    """Base class for all domain-level errors."""


class NotFoundError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class ConflictError(DomainError):
    pass
