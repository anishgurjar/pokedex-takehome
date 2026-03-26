from fastapi import FastAPI

from app.routers import campaigns, pokedex, rangers, regions, sightings, trainers, users

app = FastAPI(title="Endeavor PokéTracker", version="0.0.1")

app.include_router(trainers.router)
app.include_router(rangers.router)
app.include_router(users.router)
app.include_router(pokedex.router)
app.include_router(regions.router)
app.include_router(sightings.router)
app.include_router(campaigns.router)
