from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


ALLOWED_TRANSITIONS = {
    CampaignStatus.DRAFT: {CampaignStatus.ACTIVE},
    CampaignStatus.ACTIVE: {CampaignStatus.COMPLETED},
    CampaignStatus.COMPLETED: {CampaignStatus.ARCHIVED},
    CampaignStatus.ARCHIVED: set(),
}


class CampaignDomainError(ValueError):
    """Base class for campaign business-rule violations."""


class InvalidCampaignTransition(CampaignDomainError):
    """Raised when a campaign transition is not allowed."""


class InactiveCampaignError(CampaignDomainError):
    """Raised when a non-active campaign is used for new sightings."""


class CampaignLockedError(CampaignDomainError):
    """Raised when completed or archived campaigns should not be mutated."""


@dataclass
class Campaign:
    id: str
    name: str
    description: str
    region: str
    start_date: date
    end_date: date
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        id: str,
        name: str,
        description: str,
        region: str,
        start_date: date,
        end_date: date,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Campaign":
        cls._ensure_date_window(start_date, end_date)
        now = created_at or datetime.now(UTC)
        return cls(
            id=id,
            name=name,
            description=description,
            region=region,
            start_date=start_date,
            end_date=end_date,
            status=CampaignStatus.DRAFT,
            created_at=now,
            updated_at=updated_at or now,
        )

    def transition_to(self, requested: CampaignStatus) -> None:
        if requested not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidCampaignTransition(
                f"Cannot transition campaign from {self.status.value}"
                f" to {requested.value}"
            )
        self.status = requested
        self.touch()

    def update_details(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        region: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> None:
        self.assert_mutable()
        candidate = replace(
            self,
            name=self.name if name is None else name,
            description=self.description if description is None else description,
            region=self.region if region is None else region,
            start_date=self.start_date if start_date is None else start_date,
            end_date=self.end_date if end_date is None else end_date,
        )
        self._ensure_date_window(candidate.start_date, candidate.end_date)
        self.name = candidate.name
        self.description = candidate.description
        self.region = candidate.region
        self.start_date = candidate.start_date
        self.end_date = candidate.end_date
        self.touch()

    def assert_accepts_sightings(self) -> None:
        if self.status is not CampaignStatus.ACTIVE:
            raise InactiveCampaignError("Only active campaigns can accept sightings")

    def assert_mutable(self) -> None:
        if self.status in {CampaignStatus.COMPLETED, CampaignStatus.ARCHIVED}:
            raise CampaignLockedError(
                "Completed or archived campaigns cannot be updated"
            )

    def assert_sightings_unlocked(self) -> None:
        if self.status in {CampaignStatus.COMPLETED, CampaignStatus.ARCHIVED}:
            raise CampaignLockedError("Sightings in completed campaigns are locked")

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _ensure_date_window(start_date: date, end_date: date) -> None:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
