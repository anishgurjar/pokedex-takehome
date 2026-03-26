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
