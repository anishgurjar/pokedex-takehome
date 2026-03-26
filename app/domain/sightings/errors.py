class SightingDomainError(ValueError):
    """Base class for sighting business-rule violations."""


class SightingAlreadyConfirmedError(SightingDomainError):
    """Raised when a sighting has already been confirmed."""


class SelfConfirmationError(SightingDomainError):
    """Raised when a ranger attempts to confirm their own sighting."""
