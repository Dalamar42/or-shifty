import logging
import sys

from or_shifty.cli import Inputs, InvalidInputs, parse_args, write_output
from or_shifty.config import Config
from or_shifty.model import Infeasible, evaluate, solve

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
    try:
        evaluate(
            config=config,
            objective=inputs.objective,
            constraints=inputs.constraints,
            solution=inputs.output,
        )
    except Infeasible:
        log.error("The provided output is infeasible for the solver")
        exit(1)
    except InvalidInputs as e:
        log.error(e.msg)
        exit(1)


def solving_mode(inputs: Inputs, config: Config) -> None:
    try:
        solution = solve(
            config=config, objective=inputs.objective, constraints=inputs.constraints,
        )
    except Infeasible:
        log.error("Unable to solve for the given constraints")
        exit(1)
    else:
        if inputs.output_path is not None:
            write_output(inputs.output_path, solution)


def configure_logging(verbose=False):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)
