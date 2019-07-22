from collections import defaultdict
from datetime import date
from unittest.mock import Mock

from ortools.sat.python.cp_model import CpModel, EvaluateLinearExpr
from pytest import fixture

from or_shifty.config import Config
from or_shifty.constraints import (
    EachDayShiftIsAssignedToExactlyOnePersonShift,
    EachPersonShiftIsAssignedToAtMostOneDayShift,
    EachPersonsShiftsAreFilledInOrder,
    EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
    ThereShouldBeAtLeastXDaysBetweenOpsOfShiftTypes,
)
from or_shifty.history import History
from or_shifty.model import init_assignments
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType


def evaluate(assignments, chosen_assignments, expressions):
    solution = Mock()
    solution_map = defaultdict(lambda: False)
    for assignment in chosen_assignments:
        solution_map[assignments[assignment].Index()] = True
    solution.solution = solution_map

    for expression in expressions:
        expr = expression.Expression()
        bounds = expression.Bounds()
        value = EvaluateLinearExpr(expr, solution)
        valid = bounds[0] <= value <= bounds[1]
        if not valid:
            return False

    return True


@fixture
def model():
    return CpModel()


@fixture
def people():
    return [Person("A"), Person("B")]


@fixture
def days():
    return [
        date(2019, 1, 1),
        date(2019, 1, 2),
        date(2019, 1, 3),
        date(2019, 1, 4),
        date(2019, 1, 5),  # Sat
        date(2019, 1, 6),  # Sun
    ]


@fixture
def shifts_per_day(days):
    shifts = {
        day: [Shift(name="shift", shift_type=ShiftType.STANDARD, day=day)]
        for day in days[:-2]
    }
    shifts[days[-2]] = [
        Shift(name="shift-a", shift_type=ShiftType.SPECIAL_A, day=days[-2])
    ]
    shifts[days[-1]] = [
        Shift(name="shift-b", shift_type=ShiftType.SPECIAL_B, day=days[-1])
    ]
    return shifts


@fixture
def now():
    return date(2019, 1, 1)


@fixture
def build_run_data(people, shifts_per_day, now):
    def build(history=History.build()):
        run_data = Config.build(
            people=people,
            max_shifts_per_person=2,
            shifts_by_day=shifts_per_day,
            history=history,
            now=now,
        )
        return run_data

    return build


@fixture
def build_expressions(model, now):
    def build(constraint, data, assignments):
        expressions = [e[0] for e in constraint.generate(assignments, data)]
        for expr in expressions:
            model.Add(expr)

        return expressions

    return build


def test_each_day_shift_is_assigned_to_exactly_one_person_shift(
    model, build_run_data, build_expressions
):
    constraint = EachDayShiftIsAssignedToExactlyOnePersonShift(priority=0)

    data = build_run_data()
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Each shift is assigned
    assert evaluate(
        assignments,
        (
            (0, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 2, 0),
            (0, 0, 3, 0),
            (0, 0, 4, 0),
            (0, 0, 5, 0),
        ),
        expressions,
    )

    # First day's shift has been given to both people
    assert not evaluate(
        assignments,
        (
            (0, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 2, 0),
            (0, 0, 3, 0),
            (0, 0, 4, 0),
            (0, 0, 5, 0),
        ),
        expressions,
    )

    # Last shift is unassigned
    assert not evaluate(
        assignments,
        ((0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 2, 0), (0, 0, 3, 0), (0, 0, 4, 0)),
        expressions,
    )


def test_each_person_shift_is_assigned_to_at_most_one_day_shift(
    model, build_run_data, build_expressions
):
    constraint = EachPersonShiftIsAssignedToAtMostOneDayShift(priority=0)

    data = build_run_data()
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # No shift assigned
    assert evaluate(assignments, (), expressions)

    # Each person shift is assigned to different day shift
    assert evaluate(assignments, ((0, 0, 0, 0), (0, 1, 1, 0)), expressions)

    # Same person shift is assigned to two day shifts
    assert not evaluate(assignments, ((0, 0, 0, 0), (0, 0, 1, 0)), expressions)


def test_each_persons_shifts_are_filled_in_order(
    model, build_run_data, build_expressions
):
    constraint = EachPersonsShiftsAreFilledInOrder(priority=0)

    data = build_run_data()
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # No shift assigned
    assert evaluate(assignments, (), expressions)

    # Both shifts assigned
    assert evaluate(assignments, ((0, 0, 0, 0), (0, 1, 1, 0)), expressions)

    # Shift 1 is assigned, but 2 is not
    assert evaluate(assignments, ((0, 0, 0, 0),), expressions)

    # Shift 2 is assigned, but 1 is not
    assert not evaluate(assignments, ((0, 1, 0, 0),), expressions)


def test_each_person_works_at_most_x_shifts_per_day(
    model, build_run_data, build_expressions
):
    constraint = EachPersonWorksAtMostXShiftsPerAssignmentPeriod(priority=0, x=1)

    data = build_run_data()
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Each person has only one shift
    assert evaluate(assignments, ((0, 0, 0, 0), (1, 0, 1, 0)), expressions)

    # First person has been given two shifts
    assert not evaluate(assignments, ((0, 0, 0, 0), (0, 0, 1, 0)), expressions)


def test_there_should_be_at_least_x_days_between_ops(
    model, build_run_data, build_expressions, people, shifts_per_day
):
    constraint = ThereShouldBeAtLeastXDaysBetweenOps(priority=0, x=1)

    history = History.build(
        past_shifts=[
            AssignedShift("shift", ShiftType.STANDARD, date(2018, 12, 31), people[0])
        ]
    )
    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # One day gap between shifts
    assert evaluate(assignments, ((0, 0, 1, 0),), expressions)

    # Shifts are back to back
    assert not evaluate(assignments, ((0, 0, 0, 0),), expressions)


def test_there_should_be_at_least_x_days_between_ops_of_shift_types(
    model, build_run_data, build_expressions, people
):
    constraint = ThereShouldBeAtLeastXDaysBetweenOpsOfShiftTypes(
        priority=0, x=8, shift_types=["SPECIAL_A", "SPECIAL_B"]
    )

    history = History.build(
        past_shifts=[
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2018, 12, 29), people[0]),
            AssignedShift("shift", ShiftType.SPECIAL_B, date(2018, 12, 22), people[0]),
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2018, 12, 23), people[1]),
            AssignedShift("shift", ShiftType.STANDARD, date(2018, 12, 28), people[1]),
        ]
    )
    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person is ok to assign because they had more than 8 free days
    assert evaluate(assignments, ((1, 0, 0, 0),), expressions)
    assert evaluate(assignments, ((1, 0, 4, 0),), expressions)
    assert evaluate(assignments, ((1, 0, 5, 0),), expressions)

    # First person has just been on a special_a shift
    assert evaluate(assignments, ((0, 0, 0, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 4, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 5, 0),), expressions)


def test_respect_person_permissions_per_shift_type(
    model, build_run_data, build_expressions
):
    data = build_run_data()

    constraint = RespectPersonRestrictionsPerShiftType(
        priority=0,
        forbidden_by_shift_type={"SPECIAL_A": ["A"], "SPECIAL_B": ["A", "B"]},
    )

    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person can be assigned to special_a, but not special_b
    assert evaluate(assignments, ((1, 0, 0, 0),), expressions)
    assert evaluate(assignments, ((1, 0, 4, 0),), expressions)
    assert not evaluate(assignments, ((1, 0, 5, 0),), expressions)

    # First person can be assigned to neither special shift
    assert evaluate(assignments, ((0, 0, 0, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 4, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 5, 0),), expressions)


def test_respect_person_permissions_per_day(model, build_run_data, build_expressions):
    data = build_run_data()

    constraint = RespectPersonRestrictionsPerDay(
        priority=0, restrictions={"A": ["2019-01-01", "2019-01-02"]}
    )

    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person can be assigned to all days
    for day in range(0, 5):
        assert evaluate(assignments, ((1, 0, day, 0),), expressions)

    # First person can be assigned to every day, but the first two
    assert not evaluate(assignments, ((0, 0, 0, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 1, 0),), expressions)
    for day in range(2, 5):
        assert evaluate(assignments, ((0, 0, day, 0),), expressions)
