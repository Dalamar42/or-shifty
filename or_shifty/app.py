import logging
import sys

from or_shifty.cli import Inputs, parse_args, write_output
from or_shifty.config import Config
from or_shifty.model import evaluate, solve

logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(levelname)-7s - %(message)s",
)
log = logging.getLogger(__name__)


def main() -> None:
    inputs = parse_args()
    configure_logging(inputs.verbose)
    config = Config.build(
        people=inputs.people,
        max_shifts_per_person=inputs.max_shifts_per_person,
        shifts_by_day=inputs.shifts_by_day,
        history=inputs.history,
    )

    if inputs.evaluate:
        evaluation_mode(inputs, config)
    else:
        solving_mode(inputs, config)


def evaluation_mode(inputs: Inputs, config: Config) -> None:
    evaluate(
        config=config,
        objective=inputs.objective,
        constraints=inputs.constraints,
        solution=inputs.output,
    )


def solving_mode(inputs: Inputs, config: Config) -> None:
    solution = solve(
        config=config, objective=inputs.objective, constraints=inputs.constraints,
    )
    if inputs.output_path is not None:
        write_output(inputs.output_path, solution)


def configure_logging(verbose=False):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)
