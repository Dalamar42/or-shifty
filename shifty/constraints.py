from abc import ABCMeta, abstractmethod
from typing import Dict, Tuple

from ortools.sat.python.cp_model import CpModel, IntVar

from .data import RunData


class Constraint(metaclass=ABCMeta):
    def __init__(self, priority: int):
        self._name = self.__class__.__name__
        self._priority = priority  # lower is higher

    def __str__(self):
        return self._name

    @property
    def priority(self):
        return self._priority

    @abstractmethod
    def apply(
        self,
        model: CpModel,
        assignments: Dict[Tuple[int, int, int], IntVar],
        data: RunData,
    ):
        pass

    def __eq__(self, other):
        if other is None:
            return False
        if type(self) != type(other):
            return False
        return self.priority == other.priority


class EachShiftIsAssignedToExactlyOnePerson(Constraint):
    def apply(
        self,
        model: CpModel,
        assignments: Dict[Tuple[int, int, int], IntVar],
        data: RunData,
    ):
        for day, shifts in data.shifts_by_day.items():
            for shift in shifts:
                model.Add(
                    sum(
                        assignments[(person.index, day.index, shift.index)]
                        for person in data.people
                    )
                    == 1
                )


class EachPersonWorksAtMostOneShiftPerDay(Constraint):
    def apply(
        self,
        model: CpModel,
        assignments: Dict[Tuple[int, int, int], IntVar],
        data: RunData,
    ):
        for person in data.people:
            model.Add(
                sum(
                    assignments[(person.index, day.index, shift.index)]
                    for day, shifts in data.shifts_by_day.items()
                    for shift in shifts
                )
                <= 1
            )


class ThereShouldBeAtLeastXDaysBetweenOps(Constraint):
    def __init__(self, x=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        self._x = x

    def apply(
        self,
        model: CpModel,
        assignments: Dict[Tuple[int, int, int], IntVar],
        data: RunData,
    ):
        for day, shifts in data.shifts_by_day.items():
            for person in data.people:
                date_last_on_shift = data.history_metrics.date_last_on_shift[person.val]

                if date_last_on_shift is None:
                    continue

                if (day.val - date_last_on_shift).days >= self._x:
                    continue

                for shift in shifts:
                    model.Add(assignments[(person.index, day.index, shift.index)] == 0)

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


CONSTRAINTS = {
    constraint.__name__: constraint
    for constraint in [
        EachShiftIsAssignedToExactlyOnePerson,
        EachPersonWorksAtMostOneShiftPerDay,
        ThereShouldBeAtLeastXDaysBetweenOps,
    ]
}
