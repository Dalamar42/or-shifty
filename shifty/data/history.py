from datetime import date
from typing import List, NamedTuple, Tuple

from . import Person, Shift, ShiftType


class PastShift(NamedTuple):
    person: Person
    day: date
    shift: Shift

    @classmethod
    def build(cls, person, day, shift):
        return cls(person=person, day=day, shift=shift)

    @property
    def shift_type(self):
        return ShiftType.from_day(self.day)


class PastShiftOffset(NamedTuple):
    person: Person
    shift_type: ShiftType
    offset: int

    @classmethod
    def build(cls, person, shift_type, offset):
        return cls(person=person, shift_type=shift_type, offset=offset)


class History(NamedTuple):
    past_shifts: Tuple[PastShift, ...]
    offsets: Tuple[PastShiftOffset, ...]

    @classmethod
    def build(
        cls, past_shifts: List[PastShift] = (), offsets: List[PastShiftOffset] = ()
    ):
        past_shifts = sorted(past_shifts, key=lambda ps: ps.day, reverse=True)
        return cls(past_shifts=tuple(past_shifts), offsets=tuple(offsets))
