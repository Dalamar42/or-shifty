from typing import Any, Dict, NamedTuple

from ortools.sat.python.cp_model import CpModel, IntVar

from .data import RunData


class Constraint(NamedTuple):
    name: str
    fn: Any
    priority: int  # lower is higher

    @classmethod
    def build(cls, fn, priority):
        return cls(name=fn.__name__[1:], fn=fn, priority=priority)

    def __str__(self):
        return self.name

    def apply(self, model: CpModel, assignments: Dict[int, IntVar], data: RunData):
        self.fn(model, assignments, data)


def _each_shift_is_assigned_to_exactly_one_person(model, assignments, data):
    for day, shifts in data.shifts_by_day.items():
        for shift in shifts:
            model.Add(
                sum(
                    assignments[(person.index, day.index, shift.index)]
                    for person in data.people
                )
                == 1
            )


def _each_person_works_at_most_one_shift_per_day(model, assignments, data):
    for person in data.people:
        model.Add(
            sum(
                assignments[(person.index, day.index, shift.index)]
                for day, shifts in data.shifts_by_day.items()
                for shift in shifts
            )
            <= 1
        )


def _there_should_be_at_least_x_days_between_ops(model, assignments, data):
    for day, shifts in data.shifts_by_day.items():
        for person in data.people:
            date_last_on_shift = data.history_metrics.date_last_on_shift[person.val]

            if date_last_on_shift is None:
                continue

            if (day - date_last_on_shift).days >= data.config.min_days_between_ops:
                continue

            for shift in shifts:
                model.Add(assignments[(person.index, day.index, shift.index)] == 0)


CONSTRAINTS = [
    Constraint.build(fn=_each_shift_is_assigned_to_exactly_one_person, priority=0),
    Constraint.build(fn=_each_person_works_at_most_one_shift_per_day, priority=0),
    Constraint.build(fn=_there_should_be_at_least_x_days_between_ops, priority=1),
]
assert CONSTRAINTS == sorted(CONSTRAINTS, key=lambda c: c.priority)
