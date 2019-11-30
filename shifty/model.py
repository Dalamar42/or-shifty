import logging
from datetime import date
from typing import Dict, List

from ortools.sat.python import cp_model

from .constraints import FIXED_CONSTRAINTS, Constraint
from .data import History, Person, RunData, Shift
from .objective import Objective, RankingWeight

log = logging.getLogger(__name__)


def assign(
    people: List[Person],
    max_shifts_per_person: int,
    shifts_by_day: Dict[date, List[Shift]],
    history: History = History.build(),
    now: date = None,
    objective: Objective = RankingWeight(),
    constraints: List[Constraint] = tuple(),
):
    constraints = list(constraints) + FIXED_CONSTRAINTS
    constraints = sorted(constraints, key=lambda c: c.priority)
    now = now or date.today()
    data = RunData.build(people, max_shifts_per_person, shifts_by_day, history, now)
    return _run(data, objective, constraints)


def _run(data, objective, constraints):
    log.info("Running model")
    log.info(str(data.history_metrics))

    model = cp_model.CpModel()

    assignments = init_assignments(model, data)

    for constraint in constraints:
        for expression in constraint.generate(assignments, data):
            model.Add(expression)

    model.Maximize(objective.objective(assignments, data))

    solver = cp_model.CpSolver()
    solver.Solve(model)

    return list(_solution(solver, data, assignments))


def init_assignments(model, data):
    assignments = {}
    for idx in data.iter():
        assignments[idx.get()] = model.NewBoolVar(
            f"shift_{idx.person.val.name}_{idx.person_shift.val}_{idx.day.val}_{idx.day_shift.val.name}"
        )
    return assignments


def _solution(solver, data, assignments):
    for day, day_shifts in data.shifts_by_day.items():
        for day_shift in day_shifts:
            for index in data.iter(day_filter=day, day_shift_filter=day_shift):
                if solver.Value(assignments[index.get()]) == 1:
                    yield index.person.val, index.person_shift.val, index.day.val, index.day_shift.val
