import logging
from datetime import date
from typing import Any, Dict, List, NamedTuple

from ortools.sat.python import cp_model

from shifty.data import Person, Shift

from .constraints import CONSTRAINTS

log = logging.getLogger(__name__)


class Indexed(NamedTuple):
    index: int
    val: Any


def assign(people: List[Person], shifts_by_day: Dict[date, List[Shift]]):
    constraints = CONSTRAINTS
    indexed_people, indexed_shifts_by_day = _index_inputs(people, shifts_by_day)
    return _run(indexed_people, indexed_shifts_by_day, constraints)


def _run(indexed_people, indexed_shifts_by_day, constraints):
    log.info("Running model with constraints: %s", [str(c) for c in constraints])

    model = cp_model.CpModel()

    assignments = _init_assignments(model, indexed_people, indexed_shifts_by_day)

    for constraint in constraints:
        constraint.apply(model, assignments, indexed_people, indexed_shifts_by_day)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    return list(_solution(solver, indexed_people, indexed_shifts_by_day, assignments))


def _index_inputs(people, shifts_by_day):
    indexed_people = []
    indexed_shifts_by_day = {}

    for person_idx, person in enumerate(people):
        indexed_people.append(Indexed(index=person_idx, val=person))

    for day_idx, day in enumerate(sorted(shifts_by_day.keys())):
        day = Indexed(index=day_idx, val=day)

        for shift_idx, shift in enumerate(shifts_by_day[day.val]):
            indexed_shifts_by_day.setdefault(day, []).append(
                Indexed(index=shift_idx, val=shift)
            )

    return indexed_people, indexed_shifts_by_day


def _init_assignments(model, people, shifts_by_day):
    assignments = {}
    for person in people:
        for day, shifts in shifts_by_day.items():
            for shift in shifts:
                index = (person.index, day.index, shift.index)
                assignments[index] = model.NewBoolVar(
                    f"shift_{person.val.name}_{day.val}_{shift.val.name}"
                )
    return assignments


def _solution(solver, indexed_people, indexed_shifts_by_day, assignments):
    for day, shifts in indexed_shifts_by_day.items():
        for shift in shifts:
            for person in indexed_people:
                index = (person.index, day.index, shift.index)
                if solver.Value(assignments[index]) == 1:
                    yield person.val, day.val, shift.val
