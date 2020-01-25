import logging
import sys

from or_shifty.cli import parse_args, write_output
from or_shifty.config import Config
from or_shifty.model import solve

logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(levelname)-7s - %(message)s",
)
log = logging.getLogger(__name__)


def ops():
    inputs = parse_args()
    configure_logging(inputs.verbose)
    config = Config.build(
        people=inputs.people,
        max_shifts_per_person=inputs.max_shifts_per_person,
        shifts_by_day=inputs.shifts_by_day,
        history=inputs.history,
    )
    solution = solve(
        config=config, objective=inputs.objective, constraints=inputs.constraints,
    )
    if inputs.output_path is not None and not inputs.evaluate:
        write_output(inputs.output_path, solution)


def configure_logging(verbose=False):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    ops()
