from enum import StrEnum


class SightingWeather(StrEnum):
    SUNNY = "sunny"
    RAINY = "rainy"
    SNOWY = "snowy"
    SANDSTORM = "sandstorm"
    FOGGY = "foggy"
    CLEAR = "clear"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    DAY = "day"
    NIGHT = "night"
