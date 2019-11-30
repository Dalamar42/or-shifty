from abc import ABCMeta, abstractmethod
from itertools import product
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
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
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


class EachDayShiftIsAssignedToExactlyOnePersonShift(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for day, day_shifts in data.shifts_by_day.items():
            for day_shift in day_shifts:
                yield (
                    sum(
                        assignments[index.get()]
                        for index in data.iter(
                            day_filter=day, day_shift_filter=day_shift
                        )
                    )
                    == 1
                )


class EachPersonShiftIsAssignedToAtMostOneDayShift(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, person_shifts in data.shifts_by_person.items():
            for person_shift in person_shifts:
                yield (
                    sum(
                        assignments[index.get()]
                        for index in data.iter(
                            person_filter=person, person_shift_filter=person_shift
                        )
                    )
                    <= 1
                )


class EachPersonsShiftsAreFilledInOrder(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, person_shifts in data.shifts_by_person.items():
            for person_shift_idx, person_shift in enumerate(person_shifts):
                shift_assigned = sum(
                    assignments[index.get()]
                    for index in data.iter(
                        person_filter=person, person_shift_filter=person_shift
                    )
                )
                next_idx = person_shift_idx + 1
                for subsequent_person_shift in person_shifts[next_idx:]:
                    subsequent_shift_assigned = sum(
                        assignments[index.get()]
                        for index in data.iter(
                            person_filter=person,
                            person_shift_filter=subsequent_person_shift,
                        )
                    )
                    yield shift_assigned >= subsequent_shift_assigned


class EachPersonWorksAtMostOneShiftPerAssignmentPeriod(Constraint):
    def generate(
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person in data.shifts_by_person.keys():
            yield (
                sum(
                    assignments[index.get()]
                    for index in data.iter(person_filter=person)
                )
                <= 1
            )


class ThereShouldBeAtLeastXDaysBetweenOps(Constraint):
    def __init__(self, x=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        self._x = x

    def generate(
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            date_last_on_shift = data.history_metrics.date_last_on_shift.get(person.val)

            if date_last_on_shift is None:
                continue

            if (day.val - date_last_on_shift).days > self._x:
                continue

            for index in data.iter(person_filter=person, day_filter=day):
                yield assignments[index.get()] == 0

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
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            day_shift_type = ShiftType.from_day(day.val)
            is_weekend = day_shift_type in {ShiftType.SATURDAY, ShiftType.SUNDAY}
            if not is_weekend:
                continue

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

            if sats_since_last < self._x or suns_since_last < self._x:
                for index in data.iter(person_filter=person, day_filter=day):
                    yield assignments[index.get()] == 0

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
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            yield from self._generate_for_type(
                assignments, data, person, day, ShiftType.SATURDAY
            )
            yield from self._generate_for_type(
                assignments, data, person, day, ShiftType.SUNDAY
            )

    def _generate_for_type(self, assignments, data, person, day, shift_type):
        if not shift_type.is_of_type(day.val):
            return
        if person.val.name not in self._forbidden_by_shift_type.get(shift_type, set()):
            return
        for index in data.iter(person_filter=person, day_filter=day):
            yield assignments[index.get()] == 0

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
        self, assignments: Dict[Tuple[int, int, int, int], IntVar], data: RunData
    ) -> Generator[LinearExpr, None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            if day.val.weekday() in self._restrictions.get(person.val.name, set()):
                for index in data.iter(person_filter=person, day_filter=day):
                    yield assignments[index.get()] == 0

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._restrictions == other._restrictions


FIXED_CONSTRAINTS = [
    EachDayShiftIsAssignedToExactlyOnePersonShift(priority=0),
    EachPersonShiftIsAssignedToAtMostOneDayShift(priority=0),
    EachPersonsShiftsAreFilledInOrder(priority=0),
]


CONSTRAINTS = {
    constraint.__name__: constraint
    for constraint in [
        EachPersonWorksAtMostOneShiftPerAssignmentPeriod,
        ThereShouldBeAtLeastXDaysBetweenOps,
        ThereShouldBeAtLeastXWeekendsBetweenWeekendOps,
        RespectPersonRestrictionsPerShiftType,
        RespectPersonRestrictionsPerDay,
    ]
}
