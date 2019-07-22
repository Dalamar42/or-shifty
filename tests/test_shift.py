from datetime import date

from or_shifty.person import Person
from or_shifty.shift import AssignedShift, ShiftType


def test_json_round_trip():
    shift = AssignedShift(
        person=Person(name="A"),
        day=date(2019, 1, 1),
        name="ops",
        shift_type=ShiftType.STANDARD,
    )
    assert shift == AssignedShift.from_json(shift.to_json())
