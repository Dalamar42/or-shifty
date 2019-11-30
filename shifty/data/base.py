from datetime import date
from enum import Enum, auto
from typing import NamedTuple


class Person(NamedTuple):
    name: str


class Shift(NamedTuple):
    name: str


class ShiftType(Enum):
    WEEKDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()

    def is_of_type(self, day: date):
        if day.weekday() == 5:
            return self is ShiftType.SATURDAY
        if day.weekday() == 6:
            return self is ShiftType.SUNDAY
        return self is ShiftType.WEEKDAY
