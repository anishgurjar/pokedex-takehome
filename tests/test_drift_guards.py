from typing import get_type_hints

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


def _client_with_db(db_session):
    from app.deps import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, raise_server_exceptions=False)


def test_auth_allowed_roles_come_from_shared_enum():
    from app.auth import ALLOWED_ROLES
    from app.domain.users import UserRole

    assert {role.value for role in UserRole} == ALLOWED_ROLES


def test_domain_campaign_reuses_shared_campaign_status_enum():
    from app.domain.campaign import CampaignStatus as DomainCampaignStatus
    from app.domain.campaign.status import CampaignStatus

    assert DomainCampaignStatus is CampaignStatus


def test_sighting_create_uses_shared_enum_types():
    from app.domain.sightings.enums import SightingWeather, TimeOfDay
    from app.schemas import SightingCreate

    hints = get_type_hints(SightingCreate, include_extras=True)

    assert hints["weather"] is SightingWeather
    assert hints["time_of_day"] is TimeOfDay


def test_campaign_schemas_use_shared_campaign_status_enum():
    from app.domain.campaign.status import CampaignStatus
    from app.schemas import CampaignResponse, CampaignTransitionRequest

    transition_hints = get_type_hints(CampaignTransitionRequest, include_extras=True)
    response_hints = get_type_hints(CampaignResponse, include_extras=True)

    assert transition_hints["to_status"] is CampaignStatus
    assert response_hints["status"] is CampaignStatus


def test_db_rejects_duplicate_normalized_email(db_session):
    from app.models import AppUser

    first_user = AppUser(
        role="trainer",
        display_name="Trainer Red",
        display_name_normalized="trainer red",
        email="red@pokemon-league.org",
        email_normalized="red@pokemon-league.org",
    )
    duplicate_email_user = AppUser(
        role="ranger",
        display_name="Ranger Blue",
        display_name_normalized="ranger blue",
        email=" RED@pokemon-league.org ",
        email_normalized="red@pokemon-league.org",
    )

    db_session.add(first_user)
    db_session.commit()

    db_session.add(duplicate_email_user)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_app_user_default_timestamps_are_timezone_aware():
    from datetime import UTC

    from app.models import AppUser

    user = AppUser(
        role="trainer",
        display_name="Trainer Red",
        display_name_normalized="trainer red",
        email="red@pokemon-league.org",
        email_normalized="red@pokemon-league.org",
    )

    assert user.created_at.tzinfo == UTC
    assert user.updated_at.tzinfo == UTC


def test_ranger_creation_returns_conflict_for_duplicate_display_name(db_session):
    client = _client_with_db(db_session)

    with client:
        first_response = client.post(
            "/rangers",
            json={
                "name": "Ranger Ash",
                "email": "ash@pokemon-institute.org",
                "specialization": "Electric",
            },
        )
        assert first_response.status_code == 200

        duplicate_name_response = client.post(
            "/rangers",
            json={
                "name": " ranger ash ",
                "email": "ash-2@pokemon-institute.org",
                "specialization": "Water",
            },
        )

    assert duplicate_name_response.status_code == 409
    assert "display name" in duplicate_name_response.json()["detail"].lower()
