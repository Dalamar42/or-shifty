import logging
from datetime import date
from typing import Dict, List

from ortools.sat.python import cp_model

from .constraints import Constraint
from .data import History, Person, RunData, Shift

log = logging.getLogger(__name__)


def assign(
    people: List[Person],
    shifts_by_day: Dict[date, List[Shift]],
    history: History = History.build(),
    now: date = None,
    constraints: List[Constraint] = tuple(),
):
    assert list(constraints) == sorted(constraints, key=lambda c: c.priority)
    now = now or date.today()
    data = RunData.build(people, shifts_by_day, history, now)
    return _run(data, constraints)


def _run(data, constraints):
    log.info("Running model with constraints: %s", [str(c) for c in constraints])

    model = cp_model.CpModel()

    assignments = init_assignments(model, data.people, data.shifts_by_day)

    for constraint in constraints:
        for expression in constraint.generate(assignments, data):
            model.Add(expression)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    return list(_solution(solver, data.people, data.shifts_by_day, assignments))


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


def _solution(solver, indexed_people, indexed_shifts_by_day, assignments):
    for day, shifts in indexed_shifts_by_day.items():
        for shift in shifts:
            for person in indexed_people:
                index = (person.index, day.index, shift.index)
                if solver.Value(assignments[index]) == 1:
                    yield person.val, day.val, shift.val
