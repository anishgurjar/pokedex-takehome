from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError


class TestCampaignLifecycle:
    def _create_campaign(
        self,
        client,
        auth_headers,
        *,
        name: str = "Cerulean Cave Survey",
        description: str = "Track rare cave encounters",
        region: str = "Kanto",
        start_date: str = "2026-02-01",
        end_date: str = "2026-02-28",
    ):
        response = client.post(
            "/campaigns",
            json={
                "name": name,
                "description": description,
                "region": region,
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        return response.json()

    def _transition_campaign(
        self, client, campaign_id: str, auth_headers, to_status: str
    ):
        return client.post(
            f"/campaigns/{campaign_id}/transition",
            json={"to_status": to_status},
            headers=auth_headers,
        )

    def test_create_campaign_defaults_to_draft_and_can_be_fetched(
        self, client, sample_ranger, auth_headers_for
    ):
        created = self._create_campaign(client, auth_headers_for(sample_ranger))

        assert created["status"] == "draft"
        assert created["region"] == "Kanto"

        fetched = client.get(f"/campaigns/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == created["id"]
        assert fetched.json()["status"] == "draft"

    def test_campaign_lifecycle_only_moves_forward(
        self, client, sample_ranger, auth_headers_for
    ):
        created = self._create_campaign(client, auth_headers_for(sample_ranger))

        activate = self._transition_campaign(
            client,
            created["id"],
            auth_headers_for(sample_ranger),
            "active",
        )
        assert activate.status_code == 200
        assert activate.json()["status"] == "active"

        backwards = self._transition_campaign(
            client,
            created["id"],
            auth_headers_for(sample_ranger),
            "draft",
        )
        assert backwards.status_code == 409
        assert "Cannot transition" in backwards.json()["detail"]

    def test_only_active_campaigns_accept_new_sightings(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        created = self._create_campaign(client, auth_headers_for(sample_ranger))

        against_draft = client.post(
            "/sightings",
            json={
                "pokemon_id": 25,
                "campaign_id": created["id"],
                "region": "Kanto",
                "route": "Cerulean Cave",
                "date": "2026-02-10T08:15:00",
                "weather": "clear",
                "time_of_day": "morning",
                "height": 1.0,
                "weight": 10.0,
            },
            headers=auth_headers_for(sample_ranger),
        )
        assert against_draft.status_code == 409
        assert (
            against_draft.json()["detail"]
            == "Only active campaigns can accept sightings"
        )

        self._transition_campaign(
            client,
            created["id"],
            auth_headers_for(sample_ranger),
            "active",
        )

        against_active = client.post(
            "/sightings",
            json={
                "pokemon_id": 25,
                "campaign_id": created["id"],
                "region": "Kanto",
                "route": "Cerulean Cave",
                "date": "2026-02-10T08:15:00",
                "weather": "clear",
                "time_of_day": "morning",
                "height": 1.0,
                "weight": 10.0,
            },
            headers=auth_headers_for(sample_ranger),
        )
        assert against_active.status_code == 200
        assert against_active.json()["campaign_id"] == created["id"]

    def test_completed_campaign_locks_associated_sightings(
        self, client, sample_pokemon, sample_ranger, auth_headers_for
    ):
        created = self._create_campaign(client, auth_headers_for(sample_ranger))
        self._transition_campaign(
            client,
            created["id"],
            auth_headers_for(sample_ranger),
            "active",
        )

        sighting = client.post(
            "/sightings",
            json={
                "pokemon_id": 25,
                "campaign_id": created["id"],
                "region": "Kanto",
                "route": "Cerulean Cave",
                "date": "2026-02-10T08:15:00",
                "weather": "clear",
                "time_of_day": "morning",
                "height": 1.0,
                "weight": 10.0,
            },
            headers=auth_headers_for(sample_ranger),
        )
        assert sighting.status_code == 200

        complete = self._transition_campaign(
            client,
            created["id"],
            auth_headers_for(sample_ranger),
            "completed",
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"

        delete = client.delete(
            f"/sightings/{sighting.json()['id']}",
            headers=auth_headers_for(sample_ranger),
        )
        assert delete.status_code == 409
        assert delete.json()["detail"] == "Sightings in completed campaigns are locked"


class TestCampaignSummary:
    def _create_campaign(self, client, auth_headers):
        response = client.post(
            "/campaigns",
            json={
                "name": "Johto Migration Study",
                "description": "Observe migratory patterns",
                "region": "Johto",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        return response.json()

    def test_summary_returns_aggregate_stats(
        self,
        client,
        sample_pokemon,
        sample_ranger,
        second_ranger,
        auth_headers_for,
    ):
        campaign = self._create_campaign(client, auth_headers_for(sample_ranger))
        activated = client.post(
            f"/campaigns/{campaign['id']}/transition",
            json={"to_status": "active"},
            headers=auth_headers_for(sample_ranger),
        )
        assert activated.status_code == 200

        for headers, pokemon_id, date_value in [
            (auth_headers_for(sample_ranger), 25, "2026-03-10T07:00:00"),
            (auth_headers_for(second_ranger), 25, "2026-03-11T08:30:00"),
            (auth_headers_for(second_ranger), 152, "2026-03-12T21:15:00"),
        ]:
            response = client.post(
                "/sightings",
                json={
                    "pokemon_id": pokemon_id,
                    "campaign_id": campaign["id"],
                    "region": "Johto",
                    "route": "Route 29",
                    "date": date_value,
                    "weather": "sunny",
                    "time_of_day": "day",
                    "height": 1.0,
                    "weight": 10.0,
                },
                headers=headers,
            )
            assert response.status_code == 200

        summary = client.get(f"/campaigns/{campaign['id']}/summary")
        assert summary.status_code == 200

        data = summary.json()
        assert data["total_sightings"] == 3
        assert data["unique_species_observed"] == 2
        assert data["observation_started_at"] == "2026-03-10T07:00:00"
        assert data["observation_ended_at"] == "2026-03-12T21:15:00"
        assert {ranger["id"] for ranger in data["contributing_rangers"]} == {
            sample_ranger["id"],
            second_ranger["id"],
        }


class TestCampaignDatabaseConstraints:
    def test_db_rejects_campaign_with_end_before_start(self, db_session):
        from app.models import Campaign

        db_session.add(
            Campaign(
                name="Broken Campaign",
                description="Bad date ordering",
                region="Kanto",
                start_date=date.fromisoformat("2026-03-10"),
                end_date=date.fromisoformat("2026-03-01"),
                status="draft",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_invalid_campaign_status(self, db_session):
        from app.models import Campaign

        db_session.add(
            Campaign(
                name="Broken Campaign",
                description="Bad status",
                region="Kanto",
                start_date=date.fromisoformat("2026-03-01"),
                end_date=date.fromisoformat("2026-03-10"),
                status="paused",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()
