from datetime import date
from enum import Enum, auto
from typing import NamedTuple

from shifty.base_types import DayShift, Person


class AssignedShift(NamedTuple):
    person: Person
    day: date
    day_shift: DayShift

    @classmethod
    def build(cls, person, day, day_shift):
        return cls(person=person, day=day, day_shift=day_shift)

    @property
    def shift_type(self):
        return ShiftType.from_day(self.day)

    def __str__(self):
        return f"{self.person.name} works on {self.day} / {self.day_shift.name}"


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
