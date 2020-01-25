from abc import ABCMeta, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from itertools import product
from typing import Dict, Generator, List, Optional, Set, Tuple

from ortools.sat.python.cp_model import IntVar, LinearExpr

from or_shifty.config import Config
from or_shifty.history_metrics import NEVER
from or_shifty.indexer import Idx
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, Shift, ShiftType


@dataclass(frozen=True)
class ConstraintImpact:
    affected_person: Optional[Person]
    affected_day: Optional[date]

    def __str__(self):
        if self.affected_person is not None and self.affected_day is not None:
            return f"affecting {self.affected_person.name} on {self.affected_day}"
        if self.affected_person is not None:
            return f"affecting {self.affected_person.name}"
        if self.affected_day:
            return f"on {self.affected_day}"
        return None


class Constraint(metaclass=ABCMeta):
    def __init__(self, priority: int, name: Optional[str] = None):
        assert priority >= 0
        self._name = name or self.__class__.__name__
        self._priority = priority  # lower number is higher priority, 0 means this constraint is mandatory

    def __str__(self):
        return self._name

    @property
    def priority(self):
        return self._priority

    @abstractmethod
    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
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
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for day, day_shifts in data.shifts_by_day.items():
            for day_shift in day_shifts:
                yield (
                    (
                        sum(
                            assignments[index.idx]
                            for index in data.indexer.iter(
                                day_filter=day, day_shift_filter=day_shift
                            )
                        )
                        == 1
                    ),
                    ConstraintImpact(None, day),
                )


class EachPersonShiftIsAssignedToAtMostOneDayShift(Constraint):
    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, Person], None, None]:
        for person, person_shifts in data.shifts_by_person.items():
            for person_shift in person_shifts:
                yield (
                    (
                        sum(
                            assignments[index.idx]
                            for index in data.indexer.iter(
                                person_filter=person, person_shift_filter=person_shift
                            )
                        )
                        <= 1
                    ),
                    ConstraintImpact(person, None),
                )


class EachPersonsShiftsAreFilledInOrder(Constraint):
    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for person, person_shifts in data.shifts_by_person.items():
            for person_shift_idx, person_shift in enumerate(person_shifts):
                shift_assigned = sum(
                    assignments[index.idx]
                    for index in data.indexer.iter(
                        person_filter=person, person_shift_filter=person_shift
                    )
                )
                next_idx = person_shift_idx + 1
                for subsequent_person_shift in person_shifts[next_idx:]:
                    subsequent_shift_assigned = sum(
                        assignments[index.idx]
                        for index in data.indexer.iter(
                            person_filter=person,
                            person_shift_filter=subsequent_person_shift,
                        )
                    )
                    yield (
                        shift_assigned >= subsequent_shift_assigned,
                        ConstraintImpact(person, None),
                    )


class EachPersonWorksAtMostXShiftsPerAssignmentPeriod(Constraint):
    def __init__(self, x=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        self._x = x

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        assert (
            self._x <= data.max_shifts_per_person
        ), f"X in {self.__class__.__name__} must be <= than max_shifts_per_person"
        for person in data.shifts_by_person.keys():
            yield (
                (
                    sum(
                        assignments[index.idx]
                        for index in data.indexer.iter(person_filter=person)
                    )
                    <= 1
                ),
                ConstraintImpact(person, None),
            )

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


class ThereShouldBeAtLeastXDaysBetweenOps(Constraint):
    def __init__(self, x=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        self._x = x

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            date_last_on_shift = data.history_metrics.date_last_on_shift.get(person)

            if date_last_on_shift is None:
                continue

            if (day - date_last_on_shift).days > self._x:
                continue

            for index in data.indexer.iter(person_filter=person, day_filter=day):
                yield (
                    assignments[index.idx] == 0,
                    ConstraintImpact(person, day),
                )

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


class ThereShouldBeAtLeastXDaysBetweenOpsOfShiftTypes(Constraint):
    def __init__(self, x=None, shift_types=None, **kwargs):
        super().__init__(**kwargs)
        assert x is not None
        assert shift_types is not None
        self._x = x
        self._shift_types = {
            ShiftType.from_json(shift_type) for shift_type in shift_types
        }

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for person, (day, day_shifts) in product(
            data.shifts_by_person.keys(), data.shifts_by_day.items()
        ):
            date_last_on_shift = max(
                data.history_metrics.date_last_on_shift_of_type.get(person, {}).get(
                    shift_type, NEVER
                )
                for shift_type in self._shift_types
            )

            if date_last_on_shift is None:
                continue

            if (day - date_last_on_shift).days > self._x:
                continue

            for day_shift in day_shifts:
                if day_shift.shift_type not in self._shift_types:
                    continue

                for index in data.indexer.iter(
                    person_filter=person, day_filter=day, day_shift_filter=day_shift
                ):
                    yield (
                        assignments[index.idx] == 0,
                        ConstraintImpact(person, day),
                    )

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._x == other._x


class RespectPersonRestrictionsPerShiftType(Constraint):
    def __init__(self, forbidden_by_shift_type: Dict[str, List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        assert forbidden_by_shift_type is not None
        self._forbidden_by_shift_type = {
            ShiftType.from_json(shift_type): set(names)
            for shift_type, names in forbidden_by_shift_type.items()
        }

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for person in data.shifts_by_person.keys():
            for day, day_shifts in data.shifts_by_day.items():
                for day_shift in day_shifts:
                    yield from self._generate_for_person_day_shift(
                        assignments, data, person, day, day_shift
                    )

    def _generate_for_person_day_shift(self, assignments, data, person, day, day_shift):
        if person.name not in self._forbidden_by_shift_type.get(
            day_shift.shift_type, set()
        ):
            return
        for index in data.indexer.iter(person_filter=person, day_filter=day):
            yield (assignments[index.idx] == 0, ConstraintImpact(person, day))

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._forbidden_by_shift_type == other._forbidden_by_shift_type


class RespectPersonRestrictionsPerDay(Constraint):
    def __init__(self, restrictions: Dict[str, List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        assert restrictions is not None
        self._restrictions = {
            person_name: {
                datetime.fromisoformat(weekday).date() for weekday in weekdays
            }
            for person_name, weekdays in restrictions.items()
        }

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        for person, day in product(
            data.shifts_by_person.keys(), data.shifts_by_day.keys()
        ):
            if day in self._restrictions.get(person.name, set()):
                for index in data.indexer.iter(person_filter=person, day_filter=day):
                    yield (
                        assignments[index.idx] == 0,
                        ConstraintImpact(person, day),
                    )

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._restrictions == other._restrictions


class PredeterminedAssignmentsConstraint(Constraint):
    """This constraint forces the solver to a given solution

    It is meant to be used with the evaluation mode so the solver can be forced to produce a given
    solution against which the constraints and objective function can then be evaluated.
    """

    def __init__(self, assigned_shifts: List[AssignedShift], **kwargs) -> None:
        super().__init__(**kwargs)
        self._assigned_shifts = assigned_shifts

    def generate(
        self, assignments: Dict[Idx, IntVar], data: Config
    ) -> Generator[Tuple[LinearExpr, ConstraintImpact], None, None]:
        selected_shifts = self._selected_shifts()

        for index in data.indexer.iter():
            key = (index.person, index.person_shift, index.day_shift)
            assignment = 1 if (key in selected_shifts) else 0
            yield (
                assignments[index.idx] == assignment,
                ConstraintImpact(None, None),
            )

    def _selected_shifts(self) -> Set[Tuple[Person, int, Shift]]:
        selected_shifts = set()
        next_person_shift = defaultdict(lambda: 0)

        for shift in self._assigned_shifts:
            selected_shifts.add(
                (shift.person, next_person_shift[shift.person], shift.unassigned())
            )
            next_person_shift[shift.person] += 1

        return selected_shifts

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._assigned_shifts == other._assigned_shifts


FIXED_CONSTRAINTS = [
    EachDayShiftIsAssignedToExactlyOnePersonShift(priority=0),
    EachPersonShiftIsAssignedToAtMostOneDayShift(priority=0),
    EachPersonsShiftsAreFilledInOrder(priority=0),
]


CONSTRAINTS = {
    constraint.__name__: constraint
    for constraint in [
        EachPersonWorksAtMostXShiftsPerAssignmentPeriod,
        ThereShouldBeAtLeastXDaysBetweenOps,
        ThereShouldBeAtLeastXDaysBetweenOpsOfShiftTypes,
        RespectPersonRestrictionsPerShiftType,
        RespectPersonRestrictionsPerDay,
    ]
}

EVALUATION_CONSTRAINT = PredeterminedAssignmentsConstraint
