from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from or_shifty.person import Person
from or_shifty.shift import AssignedShift, ShiftType


@dataclass(frozen=True)
class PastShiftOffset:
    person: Person
    shift_type: ShiftType
    offset: int

    @classmethod
    def from_json(cls, serialised: Dict[str, Any]) -> "PastShiftOffset":
        return PastShiftOffset(
            person=Person(name=serialised["person"]),
            shift_type=ShiftType.from_json(serialised["shift_type"]),
            offset=int(serialised["offset"]),
        )


@dataclass(frozen=True)
class History:
    past_shifts: Tuple[AssignedShift, ...]
    offsets: Tuple[PastShiftOffset, ...]

    @classmethod
    def build(
        cls, past_shifts: List[AssignedShift] = (), offsets: List[PastShiftOffset] = ()
    ):
        past_shifts = sorted(past_shifts, key=lambda ps: ps.day, reverse=True)
        return cls(past_shifts=tuple(past_shifts), offsets=tuple(offsets))
