import logging
from datetime import date
from typing import Dict, List

from ortools.sat.python import cp_model

from .constraints import CONSTRAINTS, Constraint
from .data import Config, History, Person, RunData, Shift

log = logging.getLogger(__name__)


def assign(
    people: List[Person],
    shifts_by_day: Dict[date, List[Shift]],
    config: Config = Config.build(),
    history: History = History.build(),
    now: date = None,
    constraints: List[Constraint] = CONSTRAINTS,
):
    now = now or date.today()
    data = RunData.build(people, shifts_by_day, config, history, now)
    return _run(data, constraints)


def _run(data, constraints):
    log.info("Running model with constraints: %s", [str(c) for c in constraints])

    model = cp_model.CpModel()

    assignments = _init_assignments(model, data.people, data.shifts_by_day)

    for constraint in constraints:
        constraint.apply(model, assignments, data)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    return list(_solution(solver, data.people, data.shifts_by_day, assignments))


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
