import logging
from typing import List

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import INFEASIBLE

from or_shifty.config import Config
from or_shifty.constraints import (
    EVALUATION_CONSTRAINT,
    FIXED_CONSTRAINTS,
    Constraint,
)
from or_shifty.objective import Objective, RankingWeight
from or_shifty.shift import AssignedShift

log = logging.getLogger(__name__)


class Infeasible(Exception):
    pass


def solve(
    config: Config,
    objective: Objective = RankingWeight(),
    constraints: List[Constraint] = tuple(),
) -> List[AssignedShift]:
    constraints = _constraints(constraints)

    log.info(str(config.history_metrics))

    solver, assignments = _run_with_retries(config, objective, list(constraints))

    _validate_constraints_against_solution(solver, constraints, config, assignments)
    _display_objective_function_score(solver)

    solution = sorted(
        list(_solution(solver, config, assignments)), key=lambda s: (s.day, s.name)
    )
    log.info("Solution\n%s", "\n".join(f">>>> {shift}" for shift in solution))

    return solution


def evaluate(
    config: Config,
    objective: Objective,
    constraints: List[Constraint],
    solution: List[AssignedShift],
) -> None:
    constraints = _constraints(constraints)
    evaluation_constraint = EVALUATION_CONSTRAINT(priority=0, assigned_shifts=solution)

    log.info(str(config.history_metrics))

    solver, assignments = _run(config, objective, [evaluation_constraint])

    _validate_constraints_against_solution(solver, constraints, config, assignments)
    _display_objective_function_score(solver)

    solution = sorted(
        list(_solution(solver, config, assignments)), key=lambda s: (s.day, s.name)
    )
    log.info("Solution\n%s", "\n".join(f">>>> {shift}" for shift in solution))


def _constraints(constraints: List[Constraint]) -> List[Constraint]:
    constraints = list(constraints) + FIXED_CONSTRAINTS
    return sorted(constraints, key=lambda c: c.priority)


def _run_with_retries(config, objective, constraints):
    log.info("Running model...")
    while True:
        try:
            result = _run(config, objective, constraints)
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
    for index in data.indexer.iter():
        assignments[index.idx] = model.NewBoolVar(
            f"shift_{index.person.name}_{index.person_shift}_{index.day}_{index.day_shift.name}"
        )
    return assignments


def _solution(solver, data, assignments):
    for day, day_shifts in data.shifts_by_day.items():
        for day_shift in day_shifts:
            for index in data.indexer.iter(day_filter=day, day_shift_filter=day_shift):
                if solver.Value(assignments[index.idx]) == 1:
                    yield index.day_shift.assign(index.person)


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


def _display_objective_function_score(solver):
    log.info("Objective function score was %s", solver.ObjectiveValue())
