"""
Candidate-written tests (take-home instructions).

Write tests for the scenarios described in each class docstring.
You may add helper fixtures in conftest.py if needed.
"""


class TestCandidateSightingFilters:
    """
    Write tests for the GET /sightings endpoint (Feature 1).

    Test that the endpoint supports:
    - Pagination (limit and offset query params)
    - At least two different filters (e.g., region, weather, pokemon_id)
    - Combining multiple filters narrows results correctly
    - The response includes both the page of results and the total count
    """

    # see: tests/routers/test_sightings.py
    pass


class TestCandidateCampaignLifecycle:
    """
    Write tests for the campaign lifecycle (Feature 2).

    Test that:
    - A campaign starts in 'draft' status
    - Transitions move the campaign forward through the lifecycle
    - A sighting can be added to an active campaign
    - A sighting CANNOT be added to a non-active campaign (draft, completed, archived)
    - Sightings tied to a completed campaign are locked (cannot be deleted)
    """

    # see: tests/routers/test_campaigns.py
    pass


class TestCandidateConfirmation:
    """
    Write tests for the peer confirmation system (Feature 3).

    Test that:
    - A ranger can confirm another ranger's sighting
    - A ranger cannot confirm their own sighting
    - A sighting cannot be confirmed more than once
    - Only rangers (not trainers) can confirm sightings
    """

    # see: tests/routers/test_sightings.py
    pass
