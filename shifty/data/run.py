from datetime import date
from typing import NamedTuple, List, Dict

from . import Shift, Person, History
from shifty.history import HistoryMetrics


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
    history: History
    history_metrics: HistoryMetrics

    @classmethod
    def build(cls, people, shifts_by_day, history, now):
        return cls(
            people=cls._index_people(people),
            shifts_by_day=cls._index_shifts_by_day(shifts_by_day),
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
