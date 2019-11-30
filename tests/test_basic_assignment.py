from datetime import date

from shifty.constraints import (
    EachPersonWorksAtMostOneShiftPerAssignmentPeriod,
    ThereShouldBeAtLeastXDaysBetweenOps,
)
from shifty.data import Person, Shift
from shifty.model import assign


def test_basic_assignment():
    solution = assign(
        [Person(name=f"person_{index}") for index in range(7)],
        1,
        {
            date(2019, 1, 1): [Shift(name="shift")],
            date(2019, 1, 2): [Shift(name="shift")],
            date(2019, 1, 3): [Shift(name="shift")],
            date(2019, 1, 4): [Shift(name="shift")],
            date(2019, 1, 5): [Shift(name="shift")],
            date(2019, 1, 6): [Shift(name="shift")],
            date(2019, 1, 7): [Shift(name="shift")],
        },
        constraints=[
            EachPersonWorksAtMostOneShiftPerAssignmentPeriod(priority=0),
            ThereShouldBeAtLeastXDaysBetweenOps(priority=1, x=4),
        ],
    )
    assert len(list(solution)) == 7
