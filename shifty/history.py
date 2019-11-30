from typing import List, NamedTuple, Tuple

from shifty.base_types import Person
from shifty.shift import AssignedShift, ShiftType


class PastShiftOffset(NamedTuple):
    person: Person
    shift_type: ShiftType
    offset: int

    @classmethod
    def build(cls, person, shift_type, offset):
        return cls(person=person, shift_type=shift_type, offset=offset)


class History(NamedTuple):
    past_shifts: Tuple[AssignedShift, ...]
    offsets: Tuple[PastShiftOffset, ...]

    @classmethod
    def build(
        cls, past_shifts: List[AssignedShift] = (), offsets: List[PastShiftOffset] = ()
    ):
        past_shifts = sorted(past_shifts, key=lambda ps: ps.day, reverse=True)
        return cls(past_shifts=tuple(past_shifts), offsets=tuple(offsets))
