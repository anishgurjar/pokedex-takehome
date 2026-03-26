"""Tests for `app.routers.trainers` — POST/GET /trainers."""


class TestTrainerRegistration:
    def test_create_trainer(self, client):
        response = client.post(
            "/trainers",
            json={
                "name": "Trainer Red",
                "email": "red@pokemon-league.org",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Trainer Red"
        assert data["email"] == "red@pokemon-league.org"
        assert "id" in data

    def test_get_trainer(self, client, sample_trainer):
        response = client.get(f"/trainers/{sample_trainer['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == sample_trainer["name"]

    def test_get_trainer_not_found(self, client):
        response = client.get("/trainers/nonexistent-uuid")
        assert response.status_code == 404
