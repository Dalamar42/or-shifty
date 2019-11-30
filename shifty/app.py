import logging

from shifty.cli import parse_args
from shifty.model import assign

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

    for shift in solution:
        log.info(str(shift))


def main():
    ops()
