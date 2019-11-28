from collections import defaultdict
from datetime import date
from unittest.mock import Mock

from ortools.sat.python.cp_model import CpModel, EvaluateLinearExpr
from pytest import fixture

from shifty.constraints import EachPersonWorksAtMostOneShiftPerAssignmentPeriod
from shifty.data import History, Person, Shift
from shifty.data.run import IndexedDay, IndexedPerson, IndexedShift, RunData
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
    return [
        IndexedPerson(index=0, val=Person("A")),
        IndexedPerson(index=1, val=Person("B")),
    ]


@fixture
def shifts():
    return {
        IndexedDay(index=0, val=date(2019, 1, 1)): [
            IndexedShift(index=0, val=Shift(name="shift-1"))
        ],
        IndexedDay(index=1, val=date(2019, 1, 2)): [
            IndexedShift(index=0, val=Shift(name="shift-1"))
        ],
    }


@fixture
def now():
    return date(2019, 1, 1)


@fixture
def assignments(model, people, shifts):
    return init_assignments(model, people, shifts)


def test_each_person_works_at_most_one_shift_per_day(
    model, now, people, shifts, assignments
):
    constraint = EachPersonWorksAtMostOneShiftPerAssignmentPeriod(priority=0)
    run_data = RunData.build(people, shifts, History.build(), now)
    expressions = list(constraint.generate(assignments, run_data))
    for expr in expressions:
        model.Add(expr)

    days = list(shifts.keys())
    shift_index = 0

    # Each person has only one shift
    assert evaluate(
        assignments,
        (
            (people[0].index, days[0].index, shift_index),
            (people[1].index, days[1].index, shift_index),
        ),
        expressions,
    )

    # First person has been given two shifts
    assert not evaluate(
        assignments,
        (
            (people[0].index, days[0].index, shift_index),
            (people[0].index, days[1].index, shift_index),
        ),
        expressions,
    )
