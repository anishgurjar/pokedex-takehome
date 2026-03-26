class CampaignDomainError(ValueError):
    """Base class for campaign business-rule violations."""


class InvalidCampaignTransition(CampaignDomainError):
    """Raised when a campaign transition is not allowed."""


class InactiveCampaignError(CampaignDomainError):
    """Raised when a non-active campaign is used for new sightings."""


class CampaignLockedError(CampaignDomainError):
    """Raised when completed or archived campaigns should not be mutated."""
