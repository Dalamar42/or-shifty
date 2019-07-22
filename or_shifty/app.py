import logging
import sys

from or_shifty.cli import parse_args, write_output
from or_shifty.model import assign

logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(levelname)-7s - %(message)s",
)
log = logging.getLogger(__name__)


def ops():
    inputs = parse_args()
    configure_logging(inputs.verbose)
    solution = assign(
        people=inputs.people,
        max_shifts_per_person=inputs.max_shifts_per_person,
        shifts_by_day=inputs.shifts_by_day,
        history=inputs.history,
        now=inputs.now,
        objective=inputs.objective,
        constraints=inputs.constraints,
    )
    if inputs.output is not None:
        write_output(inputs.output, solution)


def configure_logging(verbose=False):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    ops()
