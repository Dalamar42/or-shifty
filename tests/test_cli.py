from datetime import date

from shifty.base_types import DayShift, Person
from shifty.cli import parse_args
from shifty.constraints import (
    EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
)
from shifty.shift import AssignedShift

CONFIG_FILE_PATH = "tests/test_files/cli/config.json"
HISTORY_FILE_PATH = "tests/test_files/cli/history.json"


def test_parsing_inputs():
    inputs = parse_args(["--config", CONFIG_FILE_PATH, "--history", HISTORY_FILE_PATH])

    assert set(inputs.people) == {
        Person(name="Admiral Ackbar"),
        Person(name="Mon Mothma"),
    }
    assert inputs.shifts_by_day == {
        date(2019, 11, 29): [DayShift(name="ops")],
        date(2019, 11, 30): [DayShift(name="ops")],
        date(2019, 12, 1): [DayShift(name="ops")],
    }
    assert inputs.constraints == [
        EachPersonWorksAtMostXShiftsPerAssignmentPeriod(priority=0, x=1),
        ThereShouldBeAtLeastXDaysBetweenOps(priority=1, x=4),
        RespectPersonRestrictionsPerShiftType(
            priority=2, forbidden_by_shift_type={"SATURDAY": ["Admiral Ackbar"]}
        ),
        RespectPersonRestrictionsPerDay(
            priority=3, name="Holidays", restrictions={"Admiral Ackbar": ["2019-11-01"]}
        ),
    ]
    assert inputs.history.past_shifts == (
        AssignedShift.build(
            Person("Admiral Ackbar"), date(2019, 11, 28), DayShift("ops")
        ),
        AssignedShift.build(
            Person("Admiral Ackbar"), date(2019, 11, 27), DayShift("ops")
        ),
        AssignedShift.build(
            Person("Admiral Ackbar"), date(2019, 11, 26), DayShift("ops")
        ),
        AssignedShift.build(Person("Mon Mothma"), date(2019, 11, 25), DayShift("ops")),
        AssignedShift.build(Person("Mon Mothma"), date(2019, 11, 24), DayShift("ops")),
        AssignedShift.build(
            Person("Admiral Ackbar"), date(2019, 11, 23), DayShift("ops")
        ),
    )
