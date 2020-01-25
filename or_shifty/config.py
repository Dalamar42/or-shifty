from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from or_shifty.history import History
from or_shifty.history_metrics import HistoryMetrics
from or_shifty.indexer import Indexer, PersonShift
from or_shifty.person import Person
from or_shifty.shift import Shift


@dataclass(frozen=True)
class Config:
    indexer: Indexer
    shifts_by_person: Dict[Person, List[PersonShift]]
    shifts_by_day: Dict[date, List[Shift]]
    max_shifts_per_person: int
    history: History
    history_metrics: HistoryMetrics
    now: date

    @classmethod
    def build(
        cls,
        people: List[Person],
        max_shifts_per_person: int,
        shifts_by_day: Dict[date, List[Shift]],
        history: History,
    ):
        now = min(shifts_by_day.keys())
        return cls(
            indexer=Indexer.build(people, max_shifts_per_person, shifts_by_day),
            shifts_by_person={
                person: [shift_idx for shift_idx in range(max_shifts_per_person)]
                for person in people
            },
            shifts_by_day=dict(shifts_by_day),
            max_shifts_per_person=max_shifts_per_person,
            history=history,
            history_metrics=HistoryMetrics.build(history, people, now),
            now=now,
        )
