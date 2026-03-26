from app.domain.regions import RegionName
from app.repositories.regions import RegionRepository
from app.schemas import RegionSummaryResponse


class RegionService:
    def __init__(self, repository: RegionRepository):
        self.repository = repository

    def get_summary(self, region_name: str) -> RegionSummaryResponse:
        region = RegionName.parse(region_name)
        return self.repository.get_summary(region)
