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

    @classmethod
    def from_day(cls, day: date):
        if day.weekday() == 5:
            return ShiftType.SATURDAY
        if day.weekday() == 6:
            return ShiftType.SUNDAY
        return ShiftType.WEEKDAY

    def is_of_type(self, day: date):
        if day.weekday() == 5:
            return self is ShiftType.SATURDAY
        if day.weekday() == 6:
            return self is ShiftType.SUNDAY
        return self is ShiftType.WEEKDAY
