from collections import defaultdict
from datetime import date, timedelta
from unittest.mock import Mock

from ortools.sat.python.cp_model import CpModel, EvaluateLinearExpr
from pytest import fixture

from or_shifty.config import Config
from or_shifty.history import History
from or_shifty.model import init_assignments
from or_shifty.objective import RankingWeight
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType


def evaluate(assignments, chosen_assignments, expression):
    solution = Mock()
    solution_map = defaultdict(lambda: False)
    for assignment in chosen_assignments:
        solution_map[assignments[assignment].Index()] = True
    solution.solution = solution_map

    return EvaluateLinearExpr(expression, solution)


@fixture
def model():
    return CpModel()


@fixture
def people():
    return [Person("A"), Person("B"), Person("C"), Person("D")]


@fixture
def days():
    return [
        date(2019, 11, 26),
        date(2019, 11, 27),
        date(2019, 11, 28),
        date(2019, 11, 29),
        date(2019, 11, 30),
        date(2019, 12, 1),
    ]


@fixture
def shifts_per_day(days):
    return {
        day: [
            Shift(name="shift", shift_type=ShiftType.STANDARD, day=day),
            Shift(name="shift-a", shift_type=ShiftType.SPECIAL_A, day=day),
            Shift(name="shift-b", shift_type=ShiftType.SPECIAL_B, day=day),
        ]
        for day in days
    }


@fixture
def now():
    return date(2019, 11, 25)


@fixture
def build_run_data(people, shifts_per_day, now):
    def build(history=History.build()):
        run_data = Config.build(
            people=people,
            shifts_by_day=shifts_per_day,
            max_shifts_per_person=2,
            history=history,
            now=now,
        )
        return run_data

    return build


def test_objective_function_for_weekdays(model, build_run_data, people, now):
    history = History.build(
        past_shifts=[
            # A has done 2 past shifts, most recent is 4 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=4), people[0],
            ),
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=5), people[0],
            ),
            # B has done 2 past shifts, most recent is 3 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=3), people[1],
            ),
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=7), people[1],
            ),
            # C has done 1 past shifts, most recent is 6 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=6), people[2],
            ),
            # D has done no past shifts
        ]
    )

    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    objective = RankingWeight()

    assert evaluate(
        assignments,
        ((3, 0, 0, 0), (2, 1, 1, 0), (1, 0, 2, 0)),
        objective.objective(assignments, data),
    ) == (107 + 2 + 104)


def test_objective_function_for_entire_week(model, build_run_data, people, now):
    history = History.build(
        past_shifts=[
            # STANDARD
            # A has done 2 past shifts, most recent is 4 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=4), people[0],
            ),
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=5), people[0],
            ),
            # B has done 2 past shifts, most recent is 3 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=3), people[1],
            ),
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=7), people[1],
            ),
            # C has done 1 past shifts, most recent is 6 days ago
            AssignedShift(
                "shift", ShiftType.STANDARD, now - timedelta(days=6), people[2],
            ),
            # D has done no past shifts
            # SPECIAL_A
            # A has done 1 past shift, most recent is 2 days ago
            AssignedShift(
                "shift", ShiftType.SPECIAL_A, now - timedelta(days=2), people[0],
            ),
            # B has done no past shifts
            # C has done no past shifts
            # D has done 1 past shift, most recent is 9 days ago
            AssignedShift(
                "shift", ShiftType.SPECIAL_A, now - timedelta(days=9), people[3],
            ),
            # SPECIAL_B
            # A has done no past shifts
            # B has done no past shifts
            # C has done 1 past shift, most recent is 1 days ago
            AssignedShift(
                "shift", ShiftType.SPECIAL_B, now - timedelta(days=1), people[2],
            ),  # Sun
            # D has done no past shifts
        ]
    )

    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    objective = RankingWeight()

    expected_standard_weight = 107 + 2 + 105
    expected_special_a_weight = 105
    expected_special_b_weight = 104

    assert (
        evaluate(
            assignments,
            (
                # Standard
                (2, 1, 1, 0),
                (1, 0, 2, 0),
                (3, 0, 3, 0),
            ),
            objective.objective(assignments, data),
        )
        == expected_standard_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Special A
                (3, 0, 4, 1),
            ),
            objective.objective(assignments, data),
        )
        == expected_special_a_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Special B
                (2, 0, 5, 2),
            ),
            objective.objective(assignments, data),
        )
        == expected_special_b_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Standard
                (2, 1, 1, 0),
                (1, 0, 2, 0),
                (3, 0, 3, 0),
                # Special A
                (3, 0, 4, 1),
                # Special B
                (2, 0, 5, 2),
            ),
            objective.objective(assignments, data),
        )
        == expected_standard_weight
        + expected_special_a_weight
        + expected_special_b_weight
    )
