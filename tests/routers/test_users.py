"""Tests for `app.routers.users` — GET /users/lookup."""

import pytest
from sqlalchemy.exc import IntegrityError


class TestUserLookup:
    def test_lookup_trainer_by_name(self, client, sample_trainer):
        response = client.get("/users/lookup", params={"name": sample_trainer["name"]})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_trainer["id"]
        assert data["role"] == "trainer"

    def test_lookup_ranger_by_name(self, client, sample_ranger):
        response = client.get("/users/lookup", params={"name": sample_ranger["name"]})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_ranger["id"]
        assert data["role"] == "ranger"

    def test_lookup_not_found(self, client):
        response = client.get("/users/lookup", params={"name": "Nobody"})
        assert response.status_code == 404


class TestUserDatabaseConstraints:
    def test_db_rejects_blank_display_name(self, db_session):
        from app.models import AppUser

        db_session.add(
            AppUser(
                role="trainer",
                display_name="   ",
                display_name_normalized="red",
                email="red@pokemon-league.org",
                email_normalized="red@pokemon-league.org",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_mismatched_email_normalized(self, db_session):
        from app.models import AppUser

        db_session.add(
            AppUser(
                role="trainer",
                display_name="Trainer Red",
                display_name_normalized="trainer red",
                email="Red@Pokemon-League.Org ",
                email_normalized="not-normalized@example.org",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()
