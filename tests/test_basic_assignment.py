from datetime import date

from or_shifty.model import assign
from or_shifty.person import Person
from or_shifty.shift import Shift, ShiftType


def test_basic_assignment():
    shifts = [
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 1)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 2)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 3)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 4)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 5)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 6)),
        Shift(name="shift", shift_type=ShiftType.STANDARD, day=date(2019, 1, 7)),
    ]
    solution = assign(
        [Person(name=f"person_{index}") for index in range(7)],
        1,
        {shift.day: [shift] for shift in shifts},
    )
    assert len(list(solution)) == 7
