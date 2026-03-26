"""Tests for `app.routers.users` — GET /users/lookup."""


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
