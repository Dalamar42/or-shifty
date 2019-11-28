from abc import ABCMeta, abstractmethod
from typing import Dict, Generator, List, Optional, Tuple

from ortools.sat.python.cp_model import IntVar, LinearExpr

from shifty.data import ShiftType

from .data import RunData


class Constraint(metaclass=ABCMeta):
    def __init__(self, priority: int, name: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._priority = priority  # lower is higher

    def __str__(self):
        return self._name

    @property
    def priority(self):
        return self._priority

    @abstractmethod
    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        yield from ()

    def __eq__(self, other):
        if other is None:
            return False
        if type(self) != type(other):
            return False
        if str(self) != str(other):
            return False
        return self.priority == other.priority


class EachShiftIsAssignedToExactlyOnePerson(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, shifts in data.shifts_by_day.items():
            for shift in shifts:
                yield (
                    sum(
                        assignments[(person.index, day.index, shift.index)]
                        for person in data.people
                    )
                    == 1
                )


class EachPersonWorksAtMostOneShiftPerAssignmentPeriod(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person in data.people:
            yield (
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

    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, shifts in data.shifts_by_day.items():
            for person in data.people:
                date_last_on_shift = data.history_metrics.date_last_on_shift.get(
                    person.val
                )

                if date_last_on_shift is None:
                    continue

                if (day.val - date_last_on_shift).days > self._x:
                    continue

                for shift in shifts:
                    yield assignments[(person.index, day.index, shift.index)] == 0

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


class ThereShouldBeAtLeastXWeekendsBetweenWeekendOps(Constraint):
    def __init__(self, x=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        self._x = x

    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, shifts in data.shifts_by_day.items():
            is_weekend = day.val.weekday() in {5, 6}
            if not is_weekend:
                continue

            for person in data.people:
                sats_since_last = data.history_metrics.free_days_of_shift_type_since_last_on_shift.get(
                    ShiftType.SATURDAY, {}
                ).get(
                    person.val
                )

                suns_since_last = data.history_metrics.free_days_of_shift_type_since_last_on_shift.get(
                    ShiftType.SUNDAY, {}
                ).get(
                    person.val
                )

                if (sats_since_last is not None and sats_since_last < self._x) or (
                    suns_since_last is not None and suns_since_last < self._x
                ):
                    for shift in shifts:
                        yield assignments[(person.index, day.index, shift.index)] == 0

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


class RespectPersonRestrictionsPerShiftType(Constraint):
    def __init__(self, forbidden_by_shift_type: Dict[str, List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        assert forbidden_by_shift_type is not None
        self._forbidden_by_shift_type = {
            ShiftType[shift_type]: set(names)
            for shift_type, names in forbidden_by_shift_type.items()
        }

    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, shifts in data.shifts_by_day.items():
            for person in data.people:
                if day.val.weekday() == 5 and person.val.name in self._forbidden_by_shift_type.get(
                    ShiftType.SATURDAY, set()
                ):
                    for shift in shifts:
                        yield assignments[(person.index, day.index, shift.index)] == 0

                if day.val.weekday() == 6 and person.val.name in self._forbidden_by_shift_type.get(
                    ShiftType.SUNDAY, set()
                ):
                    for shift in shifts:
                        yield assignments[(person.index, day.index, shift.index)] == 0

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._forbidden_by_shift_type == other._forbidden_by_shift_type


class RespectPersonRestrictionsPerDay(Constraint):
    def __init__(self, restrictions: Dict[str, List[int]] = None, **kwargs):
        super().__init__(**kwargs)
        assert restrictions is not None
        self._restrictions = {
            person_name: set(weekdays) for person_name, weekdays in restrictions.items()
        }

    def generate(
        self, assignments: Dict[Tuple[int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, shifts in data.shifts_by_day.items():
            for person in data.people:
                if day.val.weekday() in self._restrictions.get(person.val.name, set()):
                    for shift in shifts:
                        yield assignments[(person.index, day.index, shift.index)] == 0

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._restrictions == other._restrictions


CONSTRAINTS = {
    constraint.__name__: constraint
    for constraint in [
        EachShiftIsAssignedToExactlyOnePerson,
        EachPersonWorksAtMostOneShiftPerAssignmentPeriod,
        ThereShouldBeAtLeastXDaysBetweenOps,
        ThereShouldBeAtLeastXWeekendsBetweenWeekendOps,
        RespectPersonRestrictionsPerShiftType,
        RespectPersonRestrictionsPerDay,
    ]
}
