import argparse
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, NamedTuple

from shifty.base_types import DayShift, Person
from shifty.constraints import CONSTRAINTS, Constraint
from shifty.history import History, PastShiftOffset
from shifty.objective import OBJECTIVE_FUNCTIONS, Objective
from shifty.shift import AssignedShift, ShiftType


class Inputs(NamedTuple):
    people: List[Person]
    max_shifts_per_person: int
    shifts_by_day: Dict[date, List[DayShift]]
    objective: Objective
    constraints: List[Constraint]
    history: History
    now: date
    verbose: bool


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

    parsed_args = parser.parse_args(args)

    return _parse_inputs(
        config_path=parsed_args.config,
        history_path=parsed_args.history,
        verbose=parsed_args.verbose,
    )


def _parse_inputs(config_path: str, history_path: str, verbose: bool) -> Inputs:
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
    )


def _parse_people(config) -> List[Person]:
    return [Person(name=person["name"]) for person in config["people"]]


def _parse_max_shifts_per_person(config) -> int:
    return int(config["max_shifts_per_person"])


def _parse_shifts_by_day(config) -> Dict[date, List[DayShift]]:
    date_from = datetime.fromisoformat(config["dates"]["from"]).date()
    date_to = datetime.fromisoformat(config["dates"]["to"]).date()
    shifts = [DayShift(name=shift["name"]) for shift in config["shifts"]]
    dates = [
        date_from + timedelta(days=i) for i in range((date_to - date_from).days + 1)
    ]
    return {date: list(shifts) for date in dates}


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
        past_shift_offset = PastShiftOffset.build(
            person=Person(name=offset["person"]),
            shift_type=ShiftType[offset["shift_type"]],
            offset=int(offset["offset"]),
        )
        offsets.append(past_shift_offset)

    for shift in history["shifts"]:
        day = datetime.fromisoformat(shift["date"]).date()
        past_shift = AssignedShift.build(
            person=Person(name=shift["person"]),
            day=day,
            day_shift=DayShift(name=shift["shift"]),
        )
        shifts.append(past_shift)

    return History.build(past_shifts=shifts, offsets=offsets)
