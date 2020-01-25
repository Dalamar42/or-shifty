from datetime import date

import pytest

from or_shifty.cli import InvalidInputs, parse_args
from or_shifty.constraints import (
    EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
)
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType


def test_parsing_inputs():
    inputs = parse_args(
        [
            "--config",
            "tests/test_files/cli/config.json",
            "--history",
            "tests/test_files/cli/history.json",
        ]
    )

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
    assert inputs.output_path is None
    assert inputs.output is None


def test_parsing_output():
    inputs = parse_args(
        [
            "--config",
            "tests/test_files/cli/config.json",
            "--history",
            "tests/test_files/cli/history.json",
            "--output",
            "tests/test_files/cli/output.json",
            "--evaluate",
        ]
    )

    assert inputs.output_path == "tests/test_files/cli/output.json"
    assert inputs.output == [
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 29),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 11, 30),
            name="ops",
            shift_type=ShiftType.STANDARD,
        ),
        AssignedShift(
            person=Person("Admiral Ackbar"),
            day=date(2019, 12, 1),
            name="ops",
            shift_type=ShiftType.SPECIAL_A,
        ),
    ]


def test_parsing_invalid_output():
    with pytest.raises(InvalidInputs):
        parse_args(
            [
                "--config",
                "tests/test_files/invalid_evaluation_cli/config.json",
                "--history",
                "tests/test_files/invalid_evaluation_cli/history.json",
                "--output",
                "tests/test_files/invalid_evaluation_cli/output.json",
                "--evaluate",
            ]
        )
