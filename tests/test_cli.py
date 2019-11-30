from datetime import date

from shifty.cli import parse_args
from shifty.constraints import (
    EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
)
from shifty.data import PastShift, Person, Shift

CONFIG_FILE_PATH = "tests/test_files/config.json"
HISTORY_FILE_PATH = "tests/test_files/history.json"
DATE_FROM = date(2019, 11, 29)
DATE_TO = date(2019, 12, 1)


def test_parsing_inputs():
    inputs = parse_args(
        [
            "--config",
            CONFIG_FILE_PATH,
            "--history",
            HISTORY_FILE_PATH,
            "--date-from",
            DATE_FROM.isoformat(),
            "--date-to",
            DATE_TO.isoformat(),
        ]
    )

    assert set(inputs.people) == {
        Person(name="Admiral Ackbar"),
        Person(name="Mon Mothma"),
    }
    assert inputs.shifts_by_day == {
        date(2019, 11, 29): [Shift(name="ops")],
        date(2019, 11, 30): [Shift(name="ops")],
        date(2019, 12, 1): [Shift(name="ops")],
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
        PastShift.build(Person("Admiral Ackbar"), date(2019, 11, 28), Shift("ops")),
        PastShift.build(Person("Admiral Ackbar"), date(2019, 11, 27), Shift("ops")),
        PastShift.build(Person("Admiral Ackbar"), date(2019, 11, 26), Shift("ops")),
        PastShift.build(Person("Mon Mothma"), date(2019, 11, 25), Shift("ops")),
        PastShift.build(Person("Mon Mothma"), date(2019, 11, 24), Shift("ops")),
        PastShift.build(Person("Admiral Ackbar"), date(2019, 11, 23), Shift("ops")),
    )
