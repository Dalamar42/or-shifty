import argparse
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from or_shifty.constraints import CONSTRAINTS, Constraint
from or_shifty.history import History, PastShiftOffset
from or_shifty.objective import OBJECTIVE_FUNCTIONS, Objective
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType

log = logging.getLogger(__name__)


class InvalidInputs(Exception):
    def __init__(self, msg):
        self.msg = msg


@dataclass(frozen=True)
class Inputs:
    people: List[Person]
    max_shifts_per_person: int
    shifts_by_day: Dict[date, List[Shift]]
    objective: Objective
    constraints: List[Constraint]
    history: History
    verbose: bool
    output_path: Optional[str]
    evaluate: bool
    output: Optional[List[AssignedShift]]


def parse_args(args=None) -> Inputs:
    parser = argparse.ArgumentParser(
        description="Automatic ops shift allocator using constraint solver"
    )
    parser.add_argument(
        "--config",
        dest="config",
        action="store",
        required=True,
        help="Path to json file contain the application config",
    )
    parser.add_argument(
        "--history",
        dest="history",
        action="store",
        required=True,
        help="Path to json file containing history of past shifts",
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
        default=False,
        help="Change the log level to debug",
    )
    parser.add_argument(
        "--output",
        dest="output",
        action="store",
        default=None,
        help="Path to file in which to write the solution",
    )
    parser.add_argument(
        "--evaluate",
        dest="evaluate",
        action="store_true",
        default=False,
        help="If selected then instead of running the solver, an existing solution will "
        "be evaluated against the given config and history and the script will print "
        "the score of the objective function and any violated constraints. When used "
        "--output must also be provided",
    )

    parsed_args = parser.parse_args(args)

    return _parse_inputs(
        config_path=parsed_args.config,
        history_path=parsed_args.history,
        verbose=parsed_args.verbose,
        output_path=parsed_args.output,
        evaluate=parsed_args.evaluate,
    )


def _parse_inputs(
    config_path: str,
    history_path: str,
    verbose: bool,
    output_path: Optional[str],
    evaluate: bool,
) -> Inputs:
    _validate_args(output_path, evaluate)

    with open(config_path, "r") as f:
        config = json.load(f)

    with open(history_path, "r") as f:
        history = json.load(f)

    shifts_by_day = _parse_shifts_by_day(config)

    if evaluate:
        output = read_output(output_path)
        _validate_evaluation_output(shifts_by_day, output)
    else:
        output = None

    return Inputs(
        people=_parse_people(config),
        max_shifts_per_person=_parse_max_shifts_per_person(config),
        shifts_by_day=shifts_by_day,
        objective=_parse_objective(config),
        constraints=_parse_constraints(config),
        history=_parse_history(history),
        verbose=verbose,
        output_path=output_path,
        evaluate=evaluate,
        output=output,
    )


def _validate_args(output: Optional[str], evaluate: bool,) -> None:
    if evaluate and output is None:
        raise InvalidInputs("When in evaluate mode output path must be provided")


def _validate_evaluation_output(
    shifts_by_day: Dict[date, List[Shift]], output: List[AssignedShift]
) -> None:
    expected_shifts = {shift for shifts in shifts_by_day.values() for shift in shifts}
    output_shifts = {shift.unassigned() for shift in output}
    missing_from_output = output_shifts - expected_shifts
    extra_in_output = expected_shifts - output_shifts
    if missing_from_output or extra_in_output:
        raise InvalidInputs(
            f"There is a discrepancy between the shifts in the output and those from config. "
            f"Extra in output: {extra_in_output}, Missing from output: {missing_from_output}"
        )


def _parse_people(config) -> List[Person]:
    return [Person(name=person["name"]) for person in config["people"]]


def _parse_max_shifts_per_person(config) -> int:
    return int(config["max_shifts_per_person"])


def _parse_shifts_by_day(config) -> Dict[date, List[Shift]]:
    shifts = {}

    for shift in config["shifts"]:
        day = datetime.fromisoformat(shift["day"]).date()
        name = shift["name"]
        shift_type = ShiftType.from_json(shift["type"])

        day_shift = Shift(day=day, name=name, shift_type=shift_type)

        shifts.setdefault(day, []).append(day_shift)

    return shifts


def _parse_objective(config) -> Objective:
    return OBJECTIVE_FUNCTIONS[config["objective"]]()


def _parse_constraints(config) -> List[Constraint]:
    return [
        CONSTRAINTS[constraint["type"]](
            priority=constraint["priority"],
            name=constraint.get("name"),
            **constraint.get("params", {}),
        )
        for constraint in config["constraints"]
    ]


def _parse_history(history) -> History:
    offsets = []
    shifts = []

    for offset in history["offsets"]:
        offsets.append(PastShiftOffset.from_json(offset))

    for shift in history["shifts"]:
        shifts.append(AssignedShift.from_json(shift))

    return History.build(past_shifts=shifts, offsets=offsets)


def read_output(output_path: str) -> List[AssignedShift]:
    with open(output_path, "r") as f:
        output = json.load(f)
    shifts = [AssignedShift.from_json(shift) for shift in output["shifts"]]
    return shifts


def write_output(output_path: str, solution: List[AssignedShift]):
    log.info("Writing solution to %s...", output_path)
    solution_json = {
        "shifts": [assigned_shift.to_json() for assigned_shift in solution]
    }
    with open(output_path, "w") as f:
        json.dump(solution_json, f, indent=2)
    log.info("Solution written successfully")
