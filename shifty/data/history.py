from datetime import date
from typing import List, NamedTuple, Tuple

from . import Person, Shift, ShiftType


class PastShift(NamedTuple):
    person: Person
    day: date
    shift: Shift
    override_as_saturday: bool
    override_as_sunday: bool

    @classmethod
    def build(
        cls, person, day, shift, override_as_saturday=False, override_as_sunday=False
    ):
        return cls(
            person=person,
            day=day,
            shift=shift,
            override_as_saturday=override_as_saturday,
            override_as_sunday=override_as_sunday,
        )

    def counts_as(self, shift_type: ShiftType):
        count_as_sat = self.day.weekday() == 5 or self.override_as_saturday
        count_as_sun = self.day.weekday() == 6 or self.override_as_sunday

        if shift_type is ShiftType.SATURDAY:
            return count_as_sat
        elif shift_type is ShiftType.SUNDAY:
            return count_as_sun
        else:
            return not count_as_sat and not count_as_sun


class History(NamedTuple):
    past_shifts: Tuple[PastShift, ...]

    @classmethod
    def build(cls, past_shifts: List[PastShift] = ()):
        past_shifts = sorted(past_shifts, key=lambda ps: ps.day, reverse=True)
        return cls(past_shifts=tuple(past_shifts))
