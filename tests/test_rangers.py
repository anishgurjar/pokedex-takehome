class TestRangerRegistration:
    def test_create_ranger(self, client):
        response = client.post(
            "/rangers",
            json={
                "name": "Ranger Ash",
                "email": "ash@pokemon-institute.org",
                "specialization": "Electric",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Ranger Ash"
        assert data["specialization"] == "Electric"
        assert "id" in data

    def test_get_ranger(self, client, sample_ranger):
        response = client.get(f"/rangers/{sample_ranger['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == sample_ranger["name"]

    def test_get_ranger_not_found(self, client):
        response = client.get("/rangers/nonexistent-uuid")
        assert response.status_code == 404


class TestRangerSightings:
    def test_get_ranger_sightings(self, client, sample_sighting, sample_ranger):
        response = client.get(f"/rangers/{sample_ranger['id']}/sightings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["ranger_id"] == sample_ranger["id"]

    def test_get_ranger_sightings_not_found(self, client):
        response = client.get("/rangers/nonexistent-uuid/sightings")
        assert response.status_code == 404
