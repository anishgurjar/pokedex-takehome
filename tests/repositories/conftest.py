from datetime import date

import pytest
from app.models import AppUser, Campaign, Pokemon, Ranger


@pytest.fixture
def repo_ranger_id(db_session) -> str:
    user = AppUser(
        role="ranger",
        display_name="Repo Ranger",
        display_name_normalized="repo ranger",
        email="repo@example.org",
        email_normalized="repo@example.org",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(Ranger(user_id=user.id, specialization="Electric"))
    db_session.commit()
    return user.id


@pytest.fixture
def repo_second_ranger_id(db_session) -> str:
    user = AppUser(
        role="ranger",
        display_name="Repo Ranger Two",
        display_name_normalized="repo ranger two",
        email="repo2@example.org",
        email_normalized="repo2@example.org",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(Ranger(user_id=user.id, specialization="Water"))
    db_session.commit()
    return user.id


@pytest.fixture
def repo_pokemon_id(db_session) -> int:
    db_session.add(
        Pokemon(
            id=25,
            name="Pikachu",
            type1="Electric",
            type2=None,
            generation=1,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=190,
            evolution_chain_id=10,
        )
    )
    db_session.commit()
    return 25


@pytest.fixture
def repo_pokemon_chikorita_id(db_session) -> int:
    db_session.add(
        Pokemon(
            id=152,
            name="Chikorita",
            type1="Grass",
            type2=None,
            generation=2,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=79,
        )
    )
    db_session.commit()
    return 152


@pytest.fixture
def repo_active_campaign_id(db_session) -> str:
    campaign = Campaign(
        name="Survey",
        description="Field survey",
        region="Kanto",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status="active",
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign.id
