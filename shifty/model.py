import logging
from datetime import date
from typing import Dict, List

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import INFEASIBLE

from shifty.base_types import DayShift, Person
from shifty.config import Config
from shifty.constraints import FIXED_CONSTRAINTS, Constraint
from shifty.history import History
from shifty.objective import Objective, RankingWeight
from shifty.shift import AssignedShift

log = logging.getLogger(__name__)


class Infeasible(Exception):
    pass


def assign(
    people: List[Person],
    max_shifts_per_person: int,
    shifts_by_day: Dict[date, List[DayShift]],
    history: History = History.build(),
    now: date = None,
    objective: Objective = RankingWeight(),
    constraints: List[Constraint] = tuple(),
):
    constraints = list(constraints) + FIXED_CONSTRAINTS
    constraints = sorted(constraints, key=lambda c: c.priority)

    now = now or date.today()
    log.debug("Setting now to %s", now)

    data = Config.build(people, max_shifts_per_person, shifts_by_day, history, now)
    log.info(str(data.history_metrics))

    solver, assignments = _run_with_retries(data, objective, list(constraints))

    _validate_constraints_against_solution(solver, constraints, data, assignments)

    return list(_solution(solver, data, assignments))


def _run_with_retries(data, objective, constraints):
    log.info("Running model...")
    while True:
        try:
            result = _run(data, objective, constraints)
            log.info("Solution found")
            return result
        except Infeasible:
            log.warning("Failed to find solution with current constraints")
            constraints = _drop_least_important_constraints(constraints)
            if constraints is None:
                raise
            log.info("Retrying model...")


def _drop_least_important_constraints(constraints):
    priority_to_drop = max(constraint.priority for constraint in constraints)
    if priority_to_drop == 0:
        return None
    log.debug("Dropping constraints with priority %s", priority_to_drop)
    constraints_to_drop = [
        constraint
        for constraint in constraints
        if constraint.priority == priority_to_drop
    ]
    log.info("Dropping constraints %s", ", ".join(str(c) for c in constraints_to_drop))

    return [
        constraint
        for constraint in constraints
        if constraint.priority != priority_to_drop
    ]


def _run(data, objective, constraints):
    model = cp_model.CpModel()

    assignments = init_assignments(model, data)

    for constraint in constraints:
        log.debug("Adding constraint %s", constraint)
        for expression, _ in constraint.generate(assignments, data):
            model.Add(expression)

    model.Maximize(objective.objective(assignments, data))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status is INFEASIBLE:
        raise Infeasible()

    return solver, assignments


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
                    yield AssignedShift(
                        person=index.person.val,
                        day=index.day.val,
                        day_shift=index.day_shift.val,
                    )


def _validate_constraints_against_solution(solver, constraints, data, assignments):
    for constraint in constraints:
        log.debug("Evaluating constraint %s against solution", constraint)
        for expression, impact in constraint.generate(assignments, data):
            expr = expression.Expression()
            bounds = expression.Bounds()
            value = solver.Value(expr)
            expr_valid = bounds[0] <= value <= bounds[1]
            if not expr_valid:
                log.debug(
                    "Solution violates constraint %s, expr %s, value %s, bounds %s, impact %s",
                    constraint,
                    expr,
                    value,
                    bounds,
                    impact,
                )
                log.warning("Solution violates constraint %s %s", constraint, impact)
