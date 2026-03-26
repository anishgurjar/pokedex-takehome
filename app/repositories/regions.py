from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.domain.regions import RegionName
from app.models import AppUser, Pokemon, Sighting
from app.schemas import (
    RegionSummaryPokemonResponse,
    RegionSummaryRangerResponse,
    RegionSummaryResponse,
    RegionTimeOfDayBreakdownResponse,
    RegionWeatherBreakdownResponse,
)


class RegionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self, region: RegionName) -> RegionSummaryResponse:
        summary_row = self.db.execute(
            select(
                func.count(Sighting.id).label("total_sightings"),
                func.sum(case((Sighting.is_confirmed.is_(True), 1), else_=0)).label(
                    "confirmed_sightings"
                ),
                func.sum(case((Sighting.is_confirmed.is_(False), 1), else_=0)).label(
                    "unconfirmed_sightings"
                ),
                func.count(distinct(Sighting.pokemon_id)).label(
                    "unique_species_observed"
                ),
            ).where(Sighting.region == region.value)
        ).one()

        top_pokemon_rows = self.db.execute(
            select(
                Sighting.pokemon_id,
                Pokemon.name,
                func.count(Sighting.id).label("sightings_count"),
            )
            .join(Pokemon, Pokemon.id == Sighting.pokemon_id)
            .where(Sighting.region == region.value)
            .group_by(Sighting.pokemon_id, Pokemon.name)
            .order_by(func.count(Sighting.id).desc(), Sighting.pokemon_id.asc())
            .limit(5)
        ).all()

        top_ranger_rows = self.db.execute(
            select(
                Sighting.ranger_id,
                AppUser.display_name,
                func.count(Sighting.id).label("sightings_count"),
            )
            .join(AppUser, AppUser.id == Sighting.ranger_id)
            .where(Sighting.region == region.value)
            .group_by(Sighting.ranger_id, AppUser.display_name)
            .order_by(func.count(Sighting.id).desc(), AppUser.display_name.asc())
            .limit(5)
        ).all()

        weather_rows = self.db.execute(
            select(
                Sighting.weather,
                func.count(Sighting.id).label("sightings_count"),
            )
            .where(Sighting.region == region.value)
            .group_by(Sighting.weather)
            .order_by(func.count(Sighting.id).desc(), Sighting.weather.asc())
        ).all()

        time_of_day_rows = self.db.execute(
            select(
                Sighting.time_of_day,
                func.count(Sighting.id).label("sightings_count"),
            )
            .where(Sighting.region == region.value)
            .group_by(Sighting.time_of_day)
            .order_by(func.count(Sighting.id).desc(), Sighting.time_of_day.asc())
        ).all()

        return RegionSummaryResponse(
            region=region,
            total_sightings=summary_row.total_sightings or 0,
            confirmed_sightings=summary_row.confirmed_sightings or 0,
            unconfirmed_sightings=summary_row.unconfirmed_sightings or 0,
            unique_species_observed=summary_row.unique_species_observed or 0,
            top_pokemon=[
                RegionSummaryPokemonResponse(
                    pokemon_id=row.pokemon_id,
                    pokemon_name=row.name,
                    sightings_count=row.sightings_count,
                )
                for row in top_pokemon_rows
            ],
            top_rangers=[
                RegionSummaryRangerResponse(
                    ranger_id=row.ranger_id,
                    ranger_name=row.display_name,
                    sightings_count=row.sightings_count,
                )
                for row in top_ranger_rows
            ],
            weather_breakdown=[
                RegionWeatherBreakdownResponse(
                    weather=row.weather,
                    sightings_count=row.sightings_count,
                )
                for row in weather_rows
            ],
            time_of_day_breakdown=[
                RegionTimeOfDayBreakdownResponse(
                    time_of_day=row.time_of_day,
                    sightings_count=row.sightings_count,
                )
                for row in time_of_day_rows
            ],
        )
