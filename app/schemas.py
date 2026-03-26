from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# --- Trainer ---


class TrainerCreate(BaseModel):
    name: str
    email: EmailStr


class TrainerResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    created_at: datetime


# --- Ranger ---


class RangerCreate(BaseModel):
    name: str
    email: EmailStr
    specialization: str


class RangerResponse(BaseModel):
    id: str
    name: str
    email: str
    specialization: str
    status: str
    created_at: datetime


# --- User Lookup ---


class UserLookupResponse(BaseModel):
    id: str
    name: str
    role: Literal["trainer", "ranger"]


# --- Pokemon ---


class PokemonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type1: str
    type2: str | None
    generation: int
    is_legendary: bool
    is_mythical: bool
    is_baby: bool
    capture_rate: int
    evolution_chain_id: int | None


class PokemonSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type1: str
    type2: str | None
    generation: int


# --- Sighting ---


class SightingCreate(BaseModel):
    pokemon_id: int
    campaign_id: str | None = None
    region: str
    route: str
    date: datetime
    weather: Literal["sunny", "rainy", "snowy", "sandstorm", "foggy", "clear"]
    time_of_day: Literal["morning", "day", "night"]
    height: float
    weight: float
    is_shiny: bool = False
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class SightingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pokemon_id: int
    ranger_id: str
    campaign_id: str | None = None
    region: str
    route: str
    date: datetime
    weather: str
    time_of_day: str
    height: float
    weight: float
    is_shiny: bool
    notes: str | None
    is_confirmed: bool
    pokemon_name: str | None = None
    ranger_name: str | None = None


class SightingConfirmationResponse(BaseModel):
    sighting_id: str
    is_confirmed: bool
    confirmed_by_ranger_id: str | None = None
    confirmed_by_ranger_name: str | None = None
    confirmed_at: datetime | None = None


class SightingListParams(BaseModel):
    pokemon_id: int | None = None
    region: str | None = None
    weather: (
        Literal["sunny", "rainy", "snowy", "sandstorm", "foggy", "clear"] | None
    ) = None
    time_of_day: Literal["morning", "day", "night"] | None = None
    ranger_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None


class SightingListResponse(BaseModel):
    items: list[SightingResponse]
    total_count: int
    next_cursor: str | None


# --- Campaigns ---


CampaignStatus = Literal["draft", "active", "completed", "archived"]


class CampaignCreate(BaseModel):
    name: str
    description: str
    region: str
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "CampaignCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    region: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CampaignUpdate":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class CampaignTransitionRequest(BaseModel):
    to_status: CampaignStatus


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    region: str
    start_date: date
    end_date: date
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime


class CampaignContributorResponse(BaseModel):
    id: str
    name: str
    sightings_count: int


class CampaignSummaryResponse(BaseModel):
    campaign_id: str
    total_sightings: int
    unique_species_observed: int
    contributing_rangers: list[CampaignContributorResponse]
    observation_started_at: datetime | None
    observation_ended_at: datetime | None


# --- Generic ---


class MessageResponse(BaseModel):
    detail: str
