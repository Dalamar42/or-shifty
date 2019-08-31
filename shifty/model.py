import logging
from datetime import date
from typing import Dict, List, NamedTuple

from ortools.sat.python import cp_model

from .config import Config
from .constraints import CONSTRAINTS, Constraint
from .data import History, Person, Shift
from .history import HistoryMetrics

log = logging.getLogger(__name__)


class IndexedPerson(NamedTuple):
    index: int
    val: Person


class IndexedDay(NamedTuple):
    index: int
    val: date


class IndexedShift(NamedTuple):
    index: int
    val: Shift


class RunData(NamedTuple):
    people: List[IndexedPerson]
    shifts_by_day: Dict[IndexedDay, List[IndexedShift]]
    config: Config
    history: History
    history_metrics: HistoryMetrics

    @classmethod
    def build(cls, people, shifts_by_day, config, history, now):
        return cls(
            people=cls._index_people(people),
            shifts_by_day=cls._index_shifts_by_day(shifts_by_day),
            config=config,
            history=history,
            history_metrics=HistoryMetrics.build(history, people, now),
        )

    @staticmethod
    def _index_people(people):
        indexed_people = []

        for person_idx, person in enumerate(people):
            indexed_people.append(IndexedPerson(index=person_idx, val=person))

        return indexed_people

    @staticmethod
    def _index_shifts_by_day(shifts_by_day):
        indexed_shifts_by_day = {}

        for day_idx, day in enumerate(sorted(shifts_by_day.keys())):
            day = IndexedDay(index=day_idx, val=day)

            for shift_idx, shift in enumerate(shifts_by_day[day.val]):
                indexed_shifts_by_day.setdefault(day, []).append(
                    IndexedShift(index=shift_idx, val=shift)
                )

        return indexed_shifts_by_day


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
        constraint.apply(model, assignments, data.people, data.shifts_by_day)

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
