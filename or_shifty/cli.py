import argparse
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List

from or_shifty.constraints import CONSTRAINTS, Constraint
from or_shifty.history import History, PastShiftOffset
from or_shifty.objective import OBJECTIVE_FUNCTIONS, Objective
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Inputs:
    people: List[Person]
    max_shifts_per_person: int
    shifts_by_day: Dict[date, List[Shift]]
    objective: Objective
    constraints: List[Constraint]
    history: History
    now: date
    verbose: bool
    output: str


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

    parsed_args = parser.parse_args(args)

    return _parse_inputs(
        config_path=parsed_args.config,
        history_path=parsed_args.history,
        verbose=parsed_args.verbose,
        output=parsed_args.output,
    )


def _parse_inputs(
    config_path: str, history_path: str, verbose: bool, output: str
) -> Inputs:
    with open(config_path, "r") as f:
        config = json.load(f)

    with open(history_path, "r") as f:
        history = json.load(f)

    return Inputs(
        people=_parse_people(config),
        max_shifts_per_person=_parse_max_shifts_per_person(config),
        shifts_by_day=_parse_shifts_by_day(config),
        objective=_parse_objective(config),
        constraints=_parse_constraints(config),
        history=_parse_history(history),
        now=date.today(),
        verbose=verbose,
        output=output,
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
            **constraint.get("params", {})
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


def write_output(output: str, solution: List[AssignedShift]):
    log.info("Writing solution to %s...", output)
    solution_json = {
        "shifts": [assigned_shift.to_json() for assigned_shift in solution]
    }
    with open(output, "w") as f:
        json.dump(solution_json, f, indent=2)
    log.info("Solution written successfully")
