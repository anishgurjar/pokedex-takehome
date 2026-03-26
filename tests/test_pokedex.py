"""Tests for `app.routers.pokedex` — /pokedex and /pokedex/search."""


class TestPokedex:
    def test_list_pokemon(self, client, sample_pokemon):
        response = client.get("/pokedex")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_pokemon)

    def test_get_pokemon_by_id(self, client, sample_pokemon):
        response = client.get("/pokedex/25")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pikachu"
        assert data["type1"] == "Electric"

    def test_get_pokemon_not_found(self, client, sample_pokemon):
        response = client.get("/pokedex/999")
        assert response.status_code == 404

    def test_get_pokemon_by_region(self, client, sample_pokemon):
        response = client.get("/pokedex/kanto")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for p in data:
            assert p["generation"] == 1

    def test_search_pokemon(self, client, sample_pokemon):
        response = client.get("/pokedex/search", params={"name": "char"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == "Charmander" for p in data)
