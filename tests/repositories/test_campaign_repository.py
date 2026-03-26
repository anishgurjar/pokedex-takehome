from datetime import date, datetime

from app.models import Campaign, Sighting
from app.repositories.campaigns import CampaignRepository


class TestCampaignRepository:
    def test_create_and_get_by_id(self, db_session):
        repo = CampaignRepository(db_session)
        campaign = Campaign(
            name="Alpha",
            description="Test campaign",
            region="Johto",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )
        saved = repo.create(campaign)

        loaded = repo.get_by_id(saved.id)
        assert loaded is not None
        assert loaded.name == "Alpha"
        assert loaded.status == "draft"

    def test_save_updates_row(self, db_session):
        repo = CampaignRepository(db_session)
        campaign = Campaign(
            name="Beta",
            description="Desc",
            region="Kanto",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        saved = repo.create(campaign)
        saved.status = "active"
        repo.save(saved)

        loaded = repo.get_by_id(saved.id)
        assert loaded is not None
        assert loaded.status == "active"

    def test_build_summary_aggregates_sightings(
        self,
        db_session,
        repo_ranger_id,
        repo_second_ranger_id,
        repo_pokemon_id,
        repo_pokemon_chikorita_id,
        repo_active_campaign_id,
    ):
        cid = repo_active_campaign_id
        db_session.add_all(
            [
                Sighting(
                    pokemon_id=25,
                    ranger_id=repo_ranger_id,
                    campaign_id=cid,
                    region="Kanto",
                    route="Route 1",
                    date=datetime.fromisoformat("2026-03-10T07:00:00"),
                    weather="sunny",
                    time_of_day="day",
                    height=1.0,
                    weight=10.0,
                ),
                Sighting(
                    pokemon_id=25,
                    ranger_id=repo_second_ranger_id,
                    campaign_id=cid,
                    region="Kanto",
                    route="Route 2",
                    date=datetime.fromisoformat("2026-03-11T08:30:00"),
                    weather="sunny",
                    time_of_day="day",
                    height=1.0,
                    weight=10.0,
                ),
                Sighting(
                    pokemon_id=152,
                    ranger_id=repo_second_ranger_id,
                    campaign_id=cid,
                    region="Kanto",
                    route="Route 3",
                    date=datetime.fromisoformat("2026-03-12T21:15:00"),
                    weather="clear",
                    time_of_day="night",
                    height=1.0,
                    weight=10.0,
                ),
            ]
        )
        db_session.commit()

        repo = CampaignRepository(db_session)
        summary = repo.build_summary(cid)

        assert summary.total_sightings == 3
        assert summary.unique_species_observed == 2
        assert summary.observation_started_at == datetime.fromisoformat(
            "2026-03-10T07:00:00"
        )
        assert summary.observation_ended_at == datetime.fromisoformat(
            "2026-03-12T21:15:00"
        )
        ranger_ids = {r.id for r in summary.contributing_rangers}
        assert ranger_ids == {repo_ranger_id, repo_second_ranger_id}

    def test_build_summary_empty_campaign(self, db_session):
        repo = CampaignRepository(db_session)
        campaign = Campaign(
            name="Empty",
            description="No sightings",
            region="Sinnoh",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
        )
        saved = repo.create(campaign)
        summary = repo.build_summary(saved.id)

        assert summary.total_sightings == 0
        assert summary.unique_species_observed == 0
        assert summary.contributing_rangers == []
        assert summary.observation_started_at is None
        assert summary.observation_ended_at is None
