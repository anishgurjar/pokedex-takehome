from datetime import datetime

import pytest
from app.repositories.errors import InvalidCursorError
from app.repositories.sightings import SightingRepository
from app.schemas import SightingCreate, SightingListParams


class TestSightingRepository:
    def test_create_persists_assigned_id(
        self, db_session, repo_ranger_id, repo_pokemon_id
    ):
        repo = SightingRepository(db_session)
        payload = SightingCreate(
            pokemon_id=repo_pokemon_id,
            region="Kanto",
            route="Route 1",
            date=datetime.fromisoformat("2026-06-15T10:30:00"),
            weather="sunny",
            time_of_day="morning",
            height=0.4,
            weight=6.0,
            notes="note",
        )
        sighting_id = "custom-sighting-id-123"
        created = repo.create(
            payload, sighting_id=sighting_id, ranger_id=repo_ranger_id
        )

        assert created.id == sighting_id
        loaded = repo.get_by_id(sighting_id)
        assert loaded is not None
        assert loaded.ranger_id == repo_ranger_id
        assert loaded.pokemon_id == repo_pokemon_id

    def test_list_applies_filters_and_count(
        self, db_session, repo_ranger_id, repo_pokemon_id
    ):
        repo = SightingRepository(db_session)
        base = dict(
            region="Kanto",
            route="Route 1",
            weather="sunny",
            time_of_day="morning",
            height=1.0,
            weight=10.0,
            notes="n",
        )
        repo.create(
            SightingCreate(
                pokemon_id=repo_pokemon_id,
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                **base,
            ),
            sighting_id="s1",
            ranger_id=repo_ranger_id,
        )
        repo.create(
            SightingCreate(
                pokemon_id=repo_pokemon_id,
                date=datetime.fromisoformat("2025-06-16T10:30:00"),
                **base,
            ),
            sighting_id="s2",
            ranger_id=repo_ranger_id,
        )

        result = repo.list(
            SightingListParams(
                pokemon_id=repo_pokemon_id,
                region="Kanto",
                limit=10,
            )
        )
        assert result.total_count == 2
        assert len(result.items) == 2

    def test_decode_cursor_rejects_garbage(self):
        with pytest.raises(InvalidCursorError):
            SightingRepository.decode_cursor("not-valid")
