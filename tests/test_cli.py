from datetime import date

from or_shifty.cli import parse_args
from or_shifty.constraints import (
    EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
)
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType

CONFIG_FILE_PATH = "tests/test_files/cli/config.json"
HISTORY_FILE_PATH = "tests/test_files/cli/history.json"


def test_parsing_inputs():
    inputs = parse_args(["--config", CONFIG_FILE_PATH, "--history", HISTORY_FILE_PATH])

    assert set(inputs.people) == {
        Person(name="Admiral Ackbar"),
        Person(name="Mon Mothma"),
    }
    assert inputs.shifts_by_day == {
        date(2019, 11, 29): [
            Shift(day=date(2019, 11, 29), name="ops", shift_type=ShiftType.STANDARD)
        ],
        date(2019, 11, 30): [
            Shift(day=date(2019, 11, 30), name="ops", shift_type=ShiftType.STANDARD)
        ],
        date(2019, 12, 1): [
            Shift(day=date(2019, 12, 1), name="ops", shift_type=ShiftType.SPECIAL_A)
        ],
    }
    assert inputs.constraints == [
        EachPersonWorksAtMostXShiftsPerAssignmentPeriod(priority=0, x=1),
        ThereShouldBeAtLeastXDaysBetweenOps(priority=1, x=4),
        RespectPersonRestrictionsPerShiftType(
            priority=2, forbidden_by_shift_type={"special_a": ["Admiral Ackbar"]}
        ),
        RespectPersonRestrictionsPerDay(
            priority=3, name="Holidays", restrictions={"Admiral Ackbar": ["2019-11-01"]}
        ),
    ]
    assert inputs.history.past_shifts == (
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 28),
            name="ops",
            shift_type=ShiftType.SPECIAL_A,
        ),
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 27),
            name="ops",
            shift_type=ShiftType.SPECIAL_B,
        ),
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 26),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
        AssignedShift(
            person=Person("Mon Mothma"),
            day=date(2019, 11, 25),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
        AssignedShift(
            person=Person("Mon Mothma"),
            day=date(2019, 11, 24),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 23),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
    )
