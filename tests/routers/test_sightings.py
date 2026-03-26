from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError


class TestSightingList:
    def _create_sighting(
        self,
        client,
        auth_headers,
        *,
        pokemon_id: int,
        region: str,
        date: str,
        weather: str = "sunny",
        time_of_day: str = "day",
        route: str = "Route 1",
    ):
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": pokemon_id,
                "region": region,
                "route": route,
                "date": date,
                "weather": weather,
                "time_of_day": time_of_day,
                "height": 1.0,
                "weight": 10.0,
                "is_shiny": False,
                "notes": "Field note",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        return response.json()

    def test_list_sightings_filters_and_total_count(
        self, client, sample_pokemon, sample_ranger, second_ranger, auth_headers_for
    ):
        self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=25,
            region="Kanto",
            date="2025-06-15T10:30:00",
            weather="sunny",
            time_of_day="morning",
        )
        self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=25,
            region="Kanto",
            date="2025-06-16T10:30:00",
            weather="sunny",
            time_of_day="morning",
        )
        self._create_sighting(
            client,
            auth_headers_for(second_ranger),
            pokemon_id=25,
            region="Johto",
            date="2025-06-17T10:30:00",
            weather="rainy",
            time_of_day="night",
        )

        response = client.get(
            "/sightings",
            params={
                "pokemon_id": 25,
                "region": "Kanto",
                "weather": "sunny",
                "time_of_day": "morning",
                "ranger_id": sample_ranger["id"],
                "date_from": "2025-06-15T00:00:00",
                "date_to": "2025-06-16T23:59:59",
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 2
        assert data["next_cursor"] is None
        assert len(data["items"]) == 2
        assert [item["date"] for item in data["items"]] == [
            "2025-06-16T10:30:00",
            "2025-06-15T10:30:00",
        ]
        assert {item["ranger_id"] for item in data["items"]} == {sample_ranger["id"]}
        assert {item["region"] for item in data["items"]} == {"Kanto"}

    def test_list_sightings_uses_cursor_pagination_latest_first(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        created = [
            self._create_sighting(
                client,
                auth_headers_for(sample_ranger),
                pokemon_id=25,
                region="Kanto",
                date="2025-06-15T10:30:00",
            ),
            self._create_sighting(
                client,
                auth_headers_for(sample_ranger),
                pokemon_id=25,
                region="Kanto",
                date="2025-06-16T10:30:00",
            ),
            self._create_sighting(
                client,
                auth_headers_for(sample_ranger),
                pokemon_id=25,
                region="Kanto",
                date="2025-06-17T10:30:00",
            ),
        ]

        first_page = client.get("/sightings", params={"limit": 2})
        assert first_page.status_code == 200

        first_data = first_page.json()
        assert first_data["total_count"] == 3
        assert len(first_data["items"]) == 2
        assert first_data["items"][0]["id"] == created[2]["id"]
        assert first_data["items"][1]["id"] == created[1]["id"]
        assert isinstance(first_data["next_cursor"], str)

        second_page = client.get(
            "/sightings",
            params={"limit": 2, "cursor": first_data["next_cursor"]},
        )
        assert second_page.status_code == 200

        second_data = second_page.json()
        assert second_data["total_count"] == 3
        assert [item["id"] for item in second_data["items"]] == [created[0]["id"]]
        assert second_data["next_cursor"] is None

    def test_list_sightings_rejects_invalid_date_range(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=25,
            region="Kanto",
            date="2025-06-15T10:30:00",
        )

        response = client.get(
            "/sightings",
            params={
                "date_from": "2025-06-20T00:00:00",
                "date_to": "2025-06-10T00:00:00",
            },
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"] == "date_from must be before or equal to date_to"
        )

    def test_list_sightings_rejects_invalid_cursor(self, client):
        response = client.get("/sightings", params={"cursor": "not-a-valid-cursor"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid cursor"


class TestSightingDatabaseConstraints:
    def test_db_rejects_invalid_weather(
        self, db_session, sample_pokemon, sample_ranger
    ):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="Kanto",
                route="Route 1",
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                weather="stormy",
                time_of_day="morning",
                height=1.0,
                weight=10.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_invalid_time_of_day(
        self, db_session, sample_pokemon, sample_ranger
    ):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="Kanto",
                route="Route 1",
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                weather="sunny",
                time_of_day="dusk",
                height=1.0,
                weight=10.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_non_positive_height(
        self, db_session, sample_pokemon, sample_ranger
    ):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="Kanto",
                route="Route 1",
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                weather="sunny",
                time_of_day="morning",
                height=0,
                weight=10.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_out_of_bounds_latitude(
        self, db_session, sample_pokemon, sample_ranger
    ):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="Kanto",
                route="Route 1",
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                weather="sunny",
                time_of_day="morning",
                height=1.0,
                weight=10.0,
                latitude=100.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_blank_region(self, db_session, sample_pokemon, sample_ranger):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="   ",
                route="Route 1",
                date=datetime.fromisoformat("2025-06-15T10:30:00"),
                weather="sunny",
                time_of_day="morning",
                height=1.0,
                weight=10.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()


"""Tests for `app.routers.sightings` — /sightings CRUD and bearer auth."""


class TestSightings:
    def test_create_sighting(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "sunny",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
                "is_shiny": False,
                "notes": "Spotted in tall grass",
            },
            headers=auth_headers_for(sample_ranger),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pokemon_id"] == 1
        assert data["region"] == "Kanto"
        assert data["ranger_id"] == sample_ranger["id"]
        assert data["is_confirmed"] is False

    def test_create_sighting_requires_ranger(
        self, client, sample_pokemon, sample_trainer, auth_headers_for
    ):
        """Trainers should not be able to log sightings."""
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "sunny",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
            },
            headers=auth_headers_for(sample_trainer),
        )
        assert response.status_code == 403

    def test_create_sighting_requires_auth(self, client, sample_pokemon):
        """Sightings require a bearer token."""
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "sunny",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
            },
        )
        assert response.status_code == 401

    def test_create_sighting_rejects_invalid_token(self, client, sample_pokemon):
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "sunny",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
            },
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401

    def test_create_sighting_rejects_disabled_token(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "sunny",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
            },
            headers=auth_headers_for(sample_ranger, status="disabled"),
        )
        assert response.status_code == 403

    def test_create_sighting_invalid_weather(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        response = client.post(
            "/sightings",
            json={
                "pokemon_id": 1,
                "region": "Kanto",
                "route": "Route 1",
                "date": "2025-06-15T10:30:00",
                "weather": "tornado",
                "time_of_day": "morning",
                "height": 0.7,
                "weight": 6.9,
            },
            headers=auth_headers_for(sample_ranger),
        )
        assert response.status_code == 422

    def test_get_sighting(self, client, sample_sighting):
        response = client.get(f"/sightings/{sample_sighting['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_sighting["id"]

    def test_get_sighting_not_found(self, client):
        response = client.get("/sightings/nonexistent-id")
        assert response.status_code == 404

    def test_delete_sighting(
        self, client, sample_sighting, sample_ranger, auth_headers_for
    ):
        sighting_id = sample_sighting["id"]
        response = client.delete(
            f"/sightings/{sighting_id}",
            headers=auth_headers_for(sample_ranger),
        )
        assert response.status_code == 200

        response = client.get(f"/sightings/{sighting_id}")
        assert response.status_code == 404

    def test_delete_sighting_wrong_ranger(
        self, client, sample_sighting, second_ranger, auth_headers_for
    ):
        """A ranger cannot delete another ranger's sighting."""
        response = client.delete(
            f"/sightings/{sample_sighting['id']}",
            headers=auth_headers_for(second_ranger),
        )
        assert response.status_code == 403


class TestSightingConfirmation:
    def test_ranger_can_confirm_another_rangers_sighting(
        self, client, sample_sighting, second_ranger, auth_headers_for
    ):
        response = client.post(
            f"/sightings/{sample_sighting['id']}/confirm",
            headers=auth_headers_for(second_ranger),
        )

        assert response.status_code == 200
        assert response.json() == {
            "sighting_id": sample_sighting["id"],
            "is_confirmed": True,
            "confirmed_by_ranger_id": second_ranger["id"],
            "confirmed_by_ranger_name": second_ranger["name"],
            "confirmed_at": response.json()["confirmed_at"],
        }
        assert (
            datetime.fromisoformat(
                response.json()["confirmed_at"].replace("Z", "+00:00")
            ).tzinfo
            == UTC
        )

        details = client.get(f"/sightings/{sample_sighting['id']}/confirmation")
        assert details.status_code == 200
        assert details.json() == response.json()

    def test_ranger_cannot_confirm_their_own_sighting(
        self, client, sample_sighting, sample_ranger, auth_headers_for
    ):
        response = client.post(
            f"/sightings/{sample_sighting['id']}/confirm",
            headers=auth_headers_for(sample_ranger),
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "Rangers cannot confirm their own sightings"
        }

    def test_sighting_cannot_be_confirmed_more_than_once(
        self,
        client,
        sample_sighting,
        second_ranger,
        auth_headers_for,
    ):
        initial_confirmation = client.post(
            f"/sightings/{sample_sighting['id']}/confirm",
            headers=auth_headers_for(second_ranger),
        )
        assert initial_confirmation.status_code == 200

        another_ranger = client.post(
            "/rangers",
            json={
                "name": "Ranger Misty",
                "email": "misty@pokemon-institute.org",
                "specialization": "Water",
            },
        ).json()
        another_ranger["role"] = "ranger"

        repeat_response = client.post(
            f"/sightings/{sample_sighting['id']}/confirm",
            headers=auth_headers_for(another_ranger),
        )

        assert repeat_response.status_code == 409
        assert repeat_response.json() == {
            "detail": "Sighting has already been confirmed"
        }

    def test_only_rangers_can_confirm_sightings(
        self, client, sample_sighting, sample_trainer, auth_headers_for
    ):
        response = client.post(
            f"/sightings/{sample_sighting['id']}/confirm",
            headers=auth_headers_for(sample_trainer),
        )

        assert response.status_code == 403
        assert response.json() == {"detail": "Only rangers can access this endpoint"}
