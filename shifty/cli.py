import argparse
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, NamedTuple

from .constraints import CONSTRAINTS, Constraint
from .data import History, PastShift, PastShiftOffset, Person, Shift, ShiftType
from .objective import OBJECTIVE_FUNCTIONS, Objective


class Inputs(NamedTuple):
    people: List[Person]
    max_shifts_per_person: int
    shifts_by_day: Dict[date, List[Shift]]
    objective: Objective
    constraints: List[Constraint]
    history: History
    now: date


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
        "--date-from",
        dest="date_from",
        action="store",
        required=True,
        help="Date from which to assign ops (inclusive)",
    )
    parser.add_argument(
        "--date-to",
        dest="date_to",
        action="store",
        required=True,
        help="Date to which to assign ops (inclusive)",
    )

    parsed_args = parser.parse_args(args)

    return _parse_inputs(
        config_path=parsed_args.config,
        history_path=parsed_args.history,
        date_from=datetime.fromisoformat(parsed_args.date_from).date(),
        date_to=datetime.fromisoformat(parsed_args.date_to).date(),
    )


def _parse_inputs(
    config_path: str, history_path: str, date_from: date, date_to: date
) -> Inputs:
    with open(config_path, "r") as f:
        config = json.load(f)

    with open(history_path, "r") as f:
        history = json.load(f)

    return Inputs(
        people=_parse_people(config),
        max_shifts_per_person=_parse_max_shifts_per_person(config),
        shifts_by_day=_parse_shifts_by_day(config, date_from, date_to),
        objective=_parse_objective(config),
        constraints=_parse_constraints(config),
        history=_parse_history(history),
        now=date.today(),
    )


def _parse_people(config) -> List[Person]:
    return [Person(name=person["name"]) for person in config["people"]]


def _parse_max_shifts_per_person(config) -> int:
    return int(config["max_shifts_per_person"])


def _parse_shifts_by_day(config, date_from, date_to) -> Dict[date, List[Shift]]:
    shifts = [Shift(name=shift["name"]) for shift in config["shifts"]]
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
        past_shift = PastShift.build(
            person=Person(name=shift["person"]),
            day=day,
            shift=Shift(name=shift["shift"]),
        )
        shifts.append(past_shift)

    return History.build(past_shifts=shifts, offsets=offsets)
