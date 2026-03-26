from time import perf_counter


class TestRegionSummary:
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
    ) -> dict:
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
                "notes": "Regional summary fixture",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        return response.json()

    def test_get_region_summary_returns_expected_aggregates(
        self, client, sample_pokemon, sample_ranger, second_ranger, auth_headers_for
    ):
        first = self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=25,
            region="Kanto",
            date="2025-06-15T08:00:00",
            weather="sunny",
            time_of_day="morning",
        )
        self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=25,
            region="Kanto",
            date="2025-06-15T12:00:00",
            weather="sunny",
            time_of_day="day",
        )
        self._create_sighting(
            client,
            auth_headers_for(sample_ranger),
            pokemon_id=1,
            region="Kanto",
            date="2025-06-15T18:00:00",
            weather="rainy",
            time_of_day="night",
        )
        self._create_sighting(
            client,
            auth_headers_for(second_ranger),
            pokemon_id=4,
            region="Kanto",
            date="2025-06-16T12:00:00",
            weather="sunny",
            time_of_day="day",
        )
        self._create_sighting(
            client,
            auth_headers_for(second_ranger),
            pokemon_id=152,
            region="Johto",
            date="2025-06-16T16:00:00",
            weather="foggy",
            time_of_day="day",
        )

        confirmation = client.post(
            f"/sightings/{first['id']}/confirm",
            headers=auth_headers_for(second_ranger),
        )
        assert confirmation.status_code == 200

        response = client.get("/regions/kanto/summary")

        assert response.status_code == 200
        assert response.json() == {
            "region": "Kanto",
            "total_sightings": 4,
            "confirmed_sightings": 1,
            "unconfirmed_sightings": 3,
            "unique_species_observed": 3,
            "top_pokemon": [
                {
                    "pokemon_id": 25,
                    "pokemon_name": "Pikachu",
                    "sightings_count": 2,
                },
                {
                    "pokemon_id": 1,
                    "pokemon_name": "Bulbasaur",
                    "sightings_count": 1,
                },
                {
                    "pokemon_id": 4,
                    "pokemon_name": "Charmander",
                    "sightings_count": 1,
                },
            ],
            "top_rangers": [
                {
                    "ranger_id": sample_ranger["id"],
                    "ranger_name": sample_ranger["name"],
                    "sightings_count": 3,
                },
                {
                    "ranger_id": second_ranger["id"],
                    "ranger_name": second_ranger["name"],
                    "sightings_count": 1,
                },
            ],
            "weather_breakdown": [
                {"weather": "sunny", "sightings_count": 3},
                {"weather": "rainy", "sightings_count": 1},
            ],
            "time_of_day_breakdown": [
                {"time_of_day": "day", "sightings_count": 2},
                {"time_of_day": "morning", "sightings_count": 1},
                {"time_of_day": "night", "sightings_count": 1},
            ],
        }

    def test_get_region_summary_rejects_unknown_region(self, client):
        response = client.get("/regions/orange-islands/summary")

        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid region name"}

    def test_get_region_summary_meets_expected_response_time(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        for index in range(1200):
            pokemon_id = 25 if index % 2 == 0 else 1
            weather = "sunny" if index % 3 else "rainy"
            time_of_day = "day" if index % 4 else "night"
            self._create_sighting(
                client,
                auth_headers_for(sample_ranger),
                pokemon_id=pokemon_id,
                region="Kanto",
                date=f"2025-06-{(index % 28) + 1:02d}T12:00:00",
                weather=weather,
                time_of_day=time_of_day,
                route=f"Route {(index % 10) + 1}",
            )

        warm_response = client.get("/regions/kanto/summary")
        assert warm_response.status_code == 200

        started_at = perf_counter()
        response = client.get("/regions/kanto/summary")
        elapsed_ms = (perf_counter() - started_at) * 1000

        assert response.status_code == 200
        assert response.json()["total_sightings"] == 1200
        assert elapsed_ms < 400
