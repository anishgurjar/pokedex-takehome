from enum import StrEnum


class UserRole(StrEnum):
    TRAINER = "trainer"
    RANGER = "ranger"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
