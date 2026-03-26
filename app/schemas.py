from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# --- Trainer ---


class TrainerCreate(BaseModel):
    name: str
    email: str


class TrainerResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    created_at: datetime


# --- Ranger ---


class RangerCreate(BaseModel):
    name: str
    email: str
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


# --- Generic ---


class MessageResponse(BaseModel):
    detail: str
