from datetime import date

from shifty.base_types import DayShift, Person
from shifty.model import assign


def test_basic_assignment():
    solution = assign(
        [Person(name=f"person_{index}") for index in range(7)],
        1,
        {
            date(2019, 1, 1): [DayShift(name="shift")],
            date(2019, 1, 2): [DayShift(name="shift")],
            date(2019, 1, 3): [DayShift(name="shift")],
            date(2019, 1, 4): [DayShift(name="shift")],
            date(2019, 1, 5): [DayShift(name="shift")],
            date(2019, 1, 6): [DayShift(name="shift")],
            date(2019, 1, 7): [DayShift(name="shift")],
        },
    )
    assert len(list(solution)) == 7
