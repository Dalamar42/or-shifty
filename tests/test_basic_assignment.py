from datetime import date

from or_shifty.config import Config
from or_shifty.history import History
from or_shifty.model import solve
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
    config = Config.build(
        people=[Person(name=f"person_{index}") for index in range(7)],
        max_shifts_per_person=1,
        shifts_by_day={shift.day: [shift] for shift in shifts},
        history=History.build(),
        now=date.today(),
    )
    solution = solve(config)
    assert len(list(solution)) == 7
