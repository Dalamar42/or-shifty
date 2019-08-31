import logging
from datetime import date

from .data import Person, Shift
from .model import assign_shifts

log = logging.getLogger(__name__)


def ops():
    solution = assign_shifts(
        [Person(name=f"person_{index}") for index in range(7)],
        {
            date(2019, 1, 1): [Shift(name="shift")],
            date(2019, 1, 2): [Shift(name="shift")],
            date(2019, 1, 3): [Shift(name="shift")],
            date(2019, 1, 4): [Shift(name="shift")],
            date(2019, 1, 5): [Shift(name="shift")],
            date(2019, 1, 6): [Shift(name="shift")],
            date(2019, 1, 7): [Shift(name="shift")],
        },
    )

    for person, day, shift in solution:
        print(f"{person.name} works {day}/{shift.name}")
    print()


def main():
    ops()
