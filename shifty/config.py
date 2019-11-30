from datetime import date
from typing import Dict, Generator, List, NamedTuple, Tuple

from shifty.base_types import DayShift, Person
from shifty.history import History
from shifty.history_metrics import HistoryMetrics


class IndexedPerson(NamedTuple):
    index: int
    val: Person


class IndexedPersonShift(NamedTuple):
    index: int
    val: int


class IndexedDay(NamedTuple):
    index: int
    val: date


class IndexedDayShift(NamedTuple):
    index: int
    val: DayShift


Idx = Tuple[int, int, int, int]


class Index(NamedTuple):
    person: IndexedPerson
    person_shift: IndexedPersonShift
    day: IndexedDay
    day_shift: IndexedDayShift

    def get(self) -> Idx:
        return (
            self.person.index,
            self.person_shift.index,
            self.day.index,
            self.day_shift.index,
        )


class Config(NamedTuple):
    shifts_by_person: Dict[IndexedPerson, List[IndexedPersonShift]]
    shifts_by_day: Dict[IndexedDay, List[IndexedDayShift]]
    max_shifts_per_person: int
    history: History
    history_metrics: HistoryMetrics
    now: date

    @classmethod
    def build(
        cls,
        people: List[Person],
        max_shifts_per_person: int,
        shifts_by_day: Dict[date, List[DayShift]],
        history: History,
        now: date,
    ):
        return cls(
            shifts_by_person=cls._index_shifts_by_person(people, max_shifts_per_person),
            shifts_by_day=cls._index_shifts_by_day(shifts_by_day),
            max_shifts_per_person=max_shifts_per_person,
            history=history,
            history_metrics=HistoryMetrics.build(history, people, now),
            now=now,
        )

    @staticmethod
    def _index_shifts_by_person(people, max_shifts_per_person):
        indexed_shifts_by_person = {}

        for person_idx, person in enumerate(people):
            person = IndexedPerson(index=person_idx, val=person)

            for shift_idx in range(max_shifts_per_person):
                indexed_shifts_by_person.setdefault(person, []).append(
                    IndexedPersonShift(index=shift_idx, val=shift_idx)
                )

        return indexed_shifts_by_person

    @staticmethod
    def _index_shifts_by_day(shifts_by_day):
        indexed_shifts_by_day = {}

        for day_idx, day in enumerate(sorted(shifts_by_day.keys())):
            day = IndexedDay(index=day_idx, val=day)

            for shift_idx, shift in enumerate(shifts_by_day[day.val]):
                indexed_shifts_by_day.setdefault(day, []).append(
                    IndexedDayShift(index=shift_idx, val=shift)
                )

        return indexed_shifts_by_day

    def iter(
        self,
        person_filter: IndexedPerson = None,
        person_shift_filter: IndexedPersonShift = None,
        day_filter: IndexedDay = None,
        day_shift_filter: IndexedDayShift = None,
    ) -> Generator[Index, None, None]:
        def _filter(idx):
            if person_filter is not None and idx.person != person_filter:
                return False
            if (
                person_shift_filter is not None
                and idx.person_shift != person_shift_filter
            ):
                return False
            if day_filter is not None and idx.day != day_filter:
                return False
            if day_shift_filter is not None and idx.day_shift != day_shift_filter:
                return False
            return True

        for person, person_shifts in self.shifts_by_person.items():
            for person_shift in person_shifts:
                for day, day_shifts in self.shifts_by_day.items():
                    for day_shift in day_shifts:
                        index = Index(person, person_shift, day, day_shift)
                        if _filter(index):
                            yield index
