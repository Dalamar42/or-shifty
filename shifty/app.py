import logging
import sys

from shifty.cli import parse_args
from shifty.model import assign

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
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

    for shift in solution:
        log.info(str(shift))


def configure_logging(verbose=False):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    ops()
