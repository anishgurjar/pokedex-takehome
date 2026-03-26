from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Pokemon
from app.schemas import PokemonResponse, PokemonSearchResult

router = APIRouter(tags=["pokedex"])

REGION_TO_GENERATION = {
    "kanto": 1,
    "johto": 2,
    "hoenn": 3,
    "sinnoh": 4,
}


@router.get("/pokedex", response_model=list[PokemonResponse])
def list_pokemon(db: Session = Depends(get_db)):
    pokemon_list = db.query(Pokemon).all()
    return pokemon_list


@router.get("/pokedex/search", response_model=list[PokemonSearchResult])
def search_pokemon(name: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return db.query(Pokemon).filter(Pokemon.name.ilike(f"{name}%")).all()


@router.get("/pokedex/{pokemon_id_or_region}")
def get_pokemon(pokemon_id_or_region: str, db: Session = Depends(get_db)):
    try:
        pokemon_id = int(pokemon_id_or_region)
        pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
        if not pokemon:
            raise HTTPException(status_code=404, detail="Pokémon not found")
        return PokemonResponse.model_validate(pokemon)
    except ValueError:
        pass

    region_lower = pokemon_id_or_region.lower()
    generation = REGION_TO_GENERATION.get(region_lower)
    if generation is None:
        try:
            generation = int(pokemon_id_or_region)
        except ValueError:
            raise HTTPException(
                status_code=404, detail="Invalid Pokémon ID or region name"
            ) from None

    pokemon_list = db.query(Pokemon).filter(Pokemon.generation == generation).all()
    return [PokemonResponse.model_validate(p) for p in pokemon_list]
