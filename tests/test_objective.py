from collections import defaultdict
from datetime import date, timedelta
from unittest.mock import Mock

from ortools.sat.python.cp_model import CpModel, EvaluateLinearExpr
from pytest import fixture

from shifty.base_types import DayShift, Person
from shifty.config import Config
from shifty.history import History
from shifty.model import init_assignments
from shifty.objective import RankingWeight
from shifty.shift import AssignedShift


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
        date(2019, 11, 30),  # Sat
        date(2019, 12, 1),  # Sun
    ]


@fixture
def shifts():
    return [DayShift(name="shift-1")]


@fixture
def now():
    return date(2019, 11, 25)


@fixture
def build_run_data(people, days, shifts, now):
    def build(history=History.build()):
        shifts_per_day = {day: list(shifts) for day in days}
        run_data = Config.build(
            people=people,
            shifts_by_day=shifts_per_day,
            max_shifts_per_person=2,
            history=history,
            now=now,
        )
        return run_data

    return build


def test_objective_function_for_weekdays(model, build_run_data, people, now, shifts):
    history = History.build(
        past_shifts=[
            # A has done 2 past shifts, most recent is 4 days ago
            AssignedShift.build(
                person=people[0], day=now - timedelta(days=4), day_shift=shifts[0]
            ),  # Thu
            AssignedShift.build(
                person=people[0], day=now - timedelta(days=5), day_shift=shifts[0]
            ),  # Wed
            # B has done 2 past shifts, most recent is 3 days ago
            AssignedShift.build(
                person=people[1], day=now - timedelta(days=3), day_shift=shifts[0]
            ),  # Fri
            AssignedShift.build(
                person=people[1], day=now - timedelta(days=7), day_shift=shifts[0]
            ),  # Mon
            # C has done 1 past shifts, most recent is 6 days ago
            AssignedShift.build(
                person=people[2], day=now - timedelta(days=6), day_shift=shifts[0]
            ),  # Tue
            # D has done no past shifts
        ]
    )

    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    objective = RankingWeight()

    assert (
        evaluate(
            assignments,
            ((3, 0, 0, 0), (2, 1, 1, 0), (1, 0, 2, 0)),
            objective.objective(assignments, data),
        )
        == (107 + 2 + 104) * 1000
    )


def test_objective_function_for_entire_week(model, build_run_data, people, now, shifts):
    history = History.build(
        past_shifts=[
            # WEEKDAYS
            # A has done 2 past shifts, most recent is 4 days ago
            AssignedShift.build(
                person=people[0], day=now - timedelta(days=4), day_shift=shifts[0]
            ),  # Thu
            AssignedShift.build(
                person=people[0], day=now - timedelta(days=5), day_shift=shifts[0]
            ),  # Wed
            # B has done 2 past shifts, most recent is 3 days ago
            AssignedShift.build(
                person=people[1], day=now - timedelta(days=3), day_shift=shifts[0]
            ),  # Fri
            AssignedShift.build(
                person=people[1], day=now - timedelta(days=7), day_shift=shifts[0]
            ),  # Mon
            # C has done 1 past shifts, most recent is 6 days ago
            AssignedShift.build(
                person=people[2], day=now - timedelta(days=6), day_shift=shifts[0]
            ),  # Tue
            # D has done no past shifts
            # SATURDAYS
            # A has done 1 past shifts, most recent is 2 days ago
            AssignedShift.build(
                person=people[0], day=now - timedelta(days=2), day_shift=shifts[0]
            ),  # Sat
            # B has done no past shifts
            # C has done no past shifts
            # D has done 1 past Saturday shifts, most recent is 9 days ago
            AssignedShift.build(
                person=people[3], day=now - timedelta(days=9), day_shift=shifts[0]
            ),  # Sat
            # SUNDAYS
            # A has done no past shifts
            # B has done no past shifts
            # C has done 1 past Sunday shifts, most recent is 1 days ago
            AssignedShift.build(
                person=people[2], day=now - timedelta(days=1), day_shift=shifts[0]
            ),  # Sun
            # D has done no past shifts
        ]
    )

    data = build_run_data(history=history)
    assignments = init_assignments(model, data)
    objective = RankingWeight()

    expected_weekday_weight = (107 + 2 + 105) * 1000
    expected_sat_weight = 105 * 1000
    expected_sun_weight = 104 * 1000

    assert (
        evaluate(
            assignments,
            (
                # Weekdays
                (3, 0, 0, 0),
                (2, 1, 1, 0),
                (1, 0, 2, 0),
            ),
            objective.objective(assignments, data),
        )
        == expected_weekday_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Saturdays
                (3, 0, 4, 0),
            ),
            objective.objective(assignments, data),
        )
        == expected_sat_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Sundays
                (2, 0, 5, 0),
            ),
            objective.objective(assignments, data),
        )
        == expected_sun_weight
    )

    assert (
        evaluate(
            assignments,
            (
                # Weekdays
                (3, 0, 0, 0),
                (2, 1, 1, 0),
                (1, 0, 2, 0),
                # Saturdays
                (3, 0, 4, 0),
                # Sundays
                (2, 0, 5, 0),
            ),
            objective.objective(assignments, data),
        )
        == expected_weekday_weight + expected_sat_weight + expected_sun_weight
    )
