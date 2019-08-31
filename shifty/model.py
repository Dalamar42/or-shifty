import logging
from typing import Any, NamedTuple

from ortools.sat.python import cp_model

from .constraints import CONSTRAINTS


log = logging.getLogger(__name__)


class Indexed(NamedTuple):
    index: int
    val: Any


class Person(NamedTuple):
    name: str


class Shift(NamedTuple):
    name: str


def _index_inputs(people, shifts_by_day):
    indexed_people = []
    indexed_shifts_by_day = {}

    for index, person in enumerate(people):
        indexed_people.append(Indexed(index=index, val=person))

    for index, day in enumerate(sorted(shifts_by_day.keys())):
        day = Indexed(index=index, val=day)

        for index, shift in enumerate(shifts_by_day[day.val]):
            indexed_shifts_by_day.setdefault(day, []).append(
                Indexed(index=index, val=shift)
            )

    return indexed_people, indexed_shifts_by_day


def assign_shifts(input_people, input_shifts_by_day):
    people, shifts_by_day = _index_inputs(input_people, input_shifts_by_day)

    model = cp_model.CpModel()

    assignments = init_assignments(model, people, shifts_by_day)

    constraints = CONSTRAINTS
    log.info("Running model with constraints: %s", [str(c) for c in constraints])
    for constraint in constraints:
        constraint.apply(model, assignments, people, shifts_by_day)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    for day, shifts in shifts_by_day.items():
        for shift in shifts:
            for person in people:
                index = (person.index, day.index, shift.index)
                if solver.Value(assignments[index]) == 1:
                    yield person.val, day.val, shift.val


def init_assignments(model, people, shifts_by_day):
    assignments = {}
    for person in people:
        for day, shifts in shifts_by_day.items():
            for shift in shifts:
                index = (person.index, day.index, shift.index)
                assignments[index] = model.NewBoolVar(
                    f"shift_{person.val.name}_{day.val}_{shift.val.name}"
                )
    return assignments
