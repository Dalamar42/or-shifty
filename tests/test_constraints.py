from collections import defaultdict
from datetime import date
from unittest.mock import Mock

from ortools.sat.python.cp_model import CpModel, EvaluateLinearExpr
from pytest import fixture

from shifty.constraints import (
    EachDayShiftIsAssignedToExactlyOnePersonShift,
    EachPersonShiftIsAssignedToAtMostOneDayShift,
    EachPersonsShiftsAreFilledInOrder,
    EachPersonWorksAtMostOneShiftPerAssignmentPeriod,
    RespectPersonRestrictionsPerDay,
    RespectPersonRestrictionsPerShiftType,
    ThereShouldBeAtLeastXDaysBetweenOps,
    ThereShouldBeAtLeastXWeekendsBetweenWeekendOps,
)
from shifty.data import History, PastShift, Person, Shift
from shifty.data.run import RunData
from shifty.model import init_assignments


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
def shifts():
    return [Shift(name="shift")]


@fixture
def now():
    return date(2019, 1, 1)


@fixture
def build_run_data(people, days, shifts, now):
    def build(history=History.build()):
        shifts_per_day = {day: list(shifts) for day in days}
        run_data = RunData.build(
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
        expressions = list(constraint.generate(assignments, data))
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


def test_each_person_works_at_most_one_shift_per_day(
    model, build_run_data, build_expressions
):
    constraint = EachPersonWorksAtMostOneShiftPerAssignmentPeriod(priority=0)

    data = build_run_data()
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Each person has only one shift
    assert evaluate(assignments, ((0, 0, 0, 0), (1, 0, 1, 0)), expressions)

    # First person has been given two shifts
    assert not evaluate(assignments, ((0, 0, 0, 0), (0, 0, 1, 0)), expressions)


def test_there_should_be_at_least_x_days_between_ops(
    model, build_run_data, build_expressions, people, shifts
):
    constraint = ThereShouldBeAtLeastXDaysBetweenOps(priority=0, x=1)

    history = History.build(
        past_shifts=[PastShift.build(people[0], date(2018, 12, 31), shifts[0])]
    )
    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # One day gap between shifts
    assert evaluate(assignments, ((0, 0, 1, 0),), expressions)

    # Shifts are back to back
    assert not evaluate(assignments, ((0, 0, 0, 0),), expressions)


def test_there_should_be_at_least_x_weekends_between_weekend_ops(
    model, build_run_data, build_expressions, people, shifts
):
    constraint = ThereShouldBeAtLeastXWeekendsBetweenWeekendOps(priority=0, x=1)

    history = History.build(
        past_shifts=[
            PastShift.build(people[0], date(2018, 12, 29), shifts[0]),
            PastShift.build(people[1], date(2018, 12, 23), shifts[0]),
        ]
    )
    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person is ok to assign to the weekend because they had a free weekend in between
    assert evaluate(assignments, ((1, 0, 4, 0),), expressions)
    assert evaluate(assignments, ((1, 0, 5, 0),), expressions)

    # First person has just been on a weekend ops
    assert not evaluate(assignments, ((0, 0, 4, 0),), expressions)
    assert not evaluate(assignments, ((0, 0, 5, 0),), expressions)


def test_respect_person_permissions_per_shift_type(
    model, build_run_data, build_expressions
):
    data = build_run_data()

    constraint = RespectPersonRestrictionsPerShiftType(
        priority=0, forbidden_by_shift_type={"SATURDAY": ["A"]}
    )

    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person can be assigned to both Sat and Sun
    assert evaluate(assignments, ((1, 0, 4, 0),), expressions)
    assert evaluate(assignments, ((1, 0, 5, 0),), expressions)

    # First person can be assigned to Sun, but not Sat
    assert not evaluate(assignments, ((0, 0, 4, 0),), expressions)
    assert evaluate(assignments, ((0, 0, 5, 0),), expressions)


def test_respect_person_permissions_per_day(model, build_run_data, build_expressions):
    data = build_run_data()

    constraint = RespectPersonRestrictionsPerDay(priority=0, restrictions={"A": [1]})

    assignments = init_assignments(model, data)
    expressions = build_expressions(constraint, data, assignments)

    # Second person can be assigned to all days
    for day in range(0, 5):
        assert evaluate(assignments, ((1, 0, day, 0),), expressions)

    # First person can be assigned to every day, but Monday
    assert not evaluate(assignments, ((0, 0, 0, 0),), expressions)
    for day in range(1, 5):
        assert evaluate(assignments, ((0, 0, day, 0),), expressions)
