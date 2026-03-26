from enum import StrEnum


class RegionName(StrEnum):
    KANTO = "Kanto"
    JOHTO = "Johto"
    HOENN = "Hoenn"
    SINNOH = "Sinnoh"

    @classmethod
    def parse(cls, value: str) -> "RegionName":
        normalized = value.strip().lower()
        for region in cls:
            if region.value.lower() == normalized:
                return region
        raise ValueError("Invalid region name")

    @property
    def generation(self) -> int:
        return {
            RegionName.KANTO: 1,
            RegionName.JOHTO: 2,
            RegionName.HOENN: 3,
            RegionName.SINNOH: 4,
        }[self]
