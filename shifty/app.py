import logging

from .cli import parse_args
from .model import assign

log = logging.getLogger(__name__)


def ops():
    inputs = parse_args()
    solution = assign(
        people=inputs.people,
        max_shifts_per_person=inputs.max_shifts_per_person,
        shifts_by_day=inputs.shifts_by_day,
        history=inputs.history,
        now=inputs.now,
        objective=inputs.objective,
        constraints=inputs.constraints,
    )

    for person, person_shift, day, day_shift in solution:
        print(
            f"{person.name} works shift {person_shift + 1} on {day} / {day_shift.name}"
        )
    print()


def main():
    ops()
