from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import AppUser, Pokemon, Sighting
from app.schemas import SightingCreate, SightingListParams, SightingResponse


@dataclass(frozen=True)
class DecodedSightingCursor:
    date: datetime
    id: str


@dataclass(frozen=True)
class SightingListResult:
    items: list[SightingResponse]
    total_count: int
    next_cursor: str | None


class InvalidCursorError(ValueError):
    """Raised when a cursor cannot be parsed."""


class SightingRepository:
    FILTER_COLUMNS = {
        "pokemon_id": Sighting.pokemon_id,
        "region": Sighting.region,
        "weather": Sighting.weather,
        "time_of_day": Sighting.time_of_day,
        "ranger_id": Sighting.ranger_id,
    }

    def __init__(self, db: Session):
        self.db = db

    def get_pokemon_name(self, pokemon_id: int) -> str | None:
        return self.db.execute(
            select(Pokemon.name).where(Pokemon.id == pokemon_id)
        ).scalar_one_or_none()

    def create(self, sighting: SightingCreate, *, ranger_id: str) -> Sighting:
        new_sighting = Sighting(
            pokemon_id=sighting.pokemon_id,
            ranger_id=ranger_id,
            region=sighting.region,
            route=sighting.route,
            date=sighting.date,
            weather=sighting.weather,
            time_of_day=sighting.time_of_day,
            height=sighting.height,
            weight=sighting.weight,
            is_shiny=sighting.is_shiny,
            notes=sighting.notes,
            latitude=sighting.latitude,
            longitude=sighting.longitude,
        )
        self.db.add(new_sighting)
        self.db.commit()
        self.db.refresh(new_sighting)
        return new_sighting

    def get_by_id(self, sighting_id: str) -> SightingResponse | None:
        row = self.db.execute(
            self._detail_statement().where(Sighting.id == sighting_id)
        ).one_or_none()
        if row is None:
            return None
        return self._to_response(*row)

    def get_raw_by_id(self, sighting_id: str) -> Sighting | None:
        return self.db.execute(
            select(Sighting).where(Sighting.id == sighting_id)
        ).scalar_one_or_none()

    def delete(self, sighting: Sighting) -> None:
        self.db.delete(sighting)
        self.db.commit()

    def list(self, params: SightingListParams) -> SightingListResult:
        filters = self._build_filters(params)
        cursor = self.decode_cursor(params.cursor) if params.cursor else None
        page_filters = list(filters)
        if cursor is not None:
            page_filters.append(
                or_(
                    Sighting.date < cursor.date,
                    and_(Sighting.date == cursor.date, Sighting.id < cursor.id),
                )
            )

        rows = self.db.execute(
            self._detail_statement()
            .where(*page_filters)
            .order_by(Sighting.date.desc(), Sighting.id.desc())
            .limit(params.limit + 1)
        ).all()
        page_rows = rows[: params.limit]
        next_cursor = None
        if len(rows) > params.limit:
            last_sighting = page_rows[-1][0]
            next_cursor = self.encode_cursor(last_sighting.date, last_sighting.id)

        total_count = self.db.execute(
            select(func.count()).select_from(Sighting).where(*filters)
        ).scalar_one()

        return SightingListResult(
            items=[self._to_response(*row) for row in page_rows],
            total_count=total_count,
            next_cursor=next_cursor,
        )

    def list_for_ranger(self, ranger_id: str) -> list[SightingResponse]:
        rows = self.db.execute(
            self._detail_statement()
            .where(Sighting.ranger_id == ranger_id)
            .order_by(Sighting.date.desc(), Sighting.id.desc())
        ).all()
        return [self._to_response(*row) for row in rows]

    @staticmethod
    def encode_cursor(date: datetime, sighting_id: str) -> str:
        payload = json.dumps({"date": date.isoformat(), "id": sighting_id})
        return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode_cursor(cursor: str) -> DecodedSightingCursor:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
            payload = json.loads(decoded)
            date = datetime.fromisoformat(payload["date"])
            sighting_id = payload["id"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidCursorError("Invalid cursor") from exc

        if not isinstance(sighting_id, str) or not sighting_id:
            raise InvalidCursorError("Invalid cursor")
        return DecodedSightingCursor(date=date, id=sighting_id)

    def _build_filters(self, params: SightingListParams) -> list:
        filters = []
        for field_name, column in self.FILTER_COLUMNS.items():
            value = getattr(params, field_name)
            if value is not None:
                filters.append(column == value)
        if params.date_from is not None:
            filters.append(Sighting.date >= params.date_from)
        if params.date_to is not None:
            filters.append(Sighting.date <= params.date_to)
        return filters

    @staticmethod
    def _detail_statement():
        return (
            select(Sighting, Pokemon.name, AppUser.display_name)
            .join(Pokemon, Pokemon.id == Sighting.pokemon_id)
            .join(AppUser, AppUser.id == Sighting.ranger_id)
        )

    @staticmethod
    def _to_response(
        sighting: Sighting, pokemon_name: str, ranger_name: str
    ) -> SightingResponse:
        response = SightingResponse.model_validate(sighting)
        response.pokemon_name = pokemon_name
        response.ranger_name = ranger_name
        return response
