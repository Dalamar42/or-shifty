from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from or_shifty.history import History
from or_shifty.person import Person
from or_shifty.shift import ShiftType

NEVER = date(1970, 1, 1)


@dataclass(frozen=True)
class HistoryMetrics:
    num_of_shifts: Dict[ShiftType, Dict[Person, int]]
    date_last_on_shift: Dict[Person, date]
    date_last_on_shift_of_type: Dict[Person, Dict[ShiftType, date]]
    now: date

    @classmethod
    def build(cls, history: History, people: List[Person], now: date):
        return cls(
            num_of_shifts=cls._num_of_shifts(history, people),
            date_last_on_shift=cls._date_last_on_shift(history, people),
            date_last_on_shift_of_type=cls._date_last_on_shift_of_type(history, people),
            now=now,
        )

    @classmethod
    def _num_of_shifts(cls, history: History, people: List[Person]):
        return {
            shift_type: cls._num_of_shifts_for_type(history, people, shift_type)
            for shift_type in ShiftType
        }

    @classmethod
    def _num_of_shifts_for_type(
        cls, history: History, people: List[Person], shift_type: ShiftType
    ):
        shifts = {person: 0 for person in people}

        for offset in history.offsets:
            if offset.shift_type is shift_type:
                shifts[offset.person] = offset.offset

        for past_shift in history.past_shifts:
            if past_shift.shift_type is shift_type and past_shift.person in shifts:
                shifts.setdefault(past_shift.person, 0)
                shifts[past_shift.person] += 1

        return shifts

    @classmethod
    def _date_last_on_shift(cls, history: History, people: List[Person]):
        people_seen = set()
        date_last = {person: NEVER for person in people}
        for past_shift in history.past_shifts:
            if past_shift.person in date_last and past_shift.person not in people_seen:
                people_seen.add(past_shift.person)
                date_last[past_shift.person] = past_shift.day
        return date_last

    @classmethod
    def _date_last_on_shift_of_type(cls, history: History, people: List[Person]):
        people_seen = {person: set() for person in people}
        date_last = {
            person: {shift_type: NEVER for shift_type in ShiftType} for person in people
        }
        for past_shift in history.past_shifts:
            if (
                past_shift.person in date_last
                and past_shift.shift_type not in people_seen[past_shift.person]
            ):
                people_seen[past_shift.person].add(past_shift.shift_type)
                date_last[past_shift.person][past_shift.shift_type] = past_shift.day
        return date_last

    def __str__(self):
        formatted = "Pre-allocation history metrics:\n"
        formatted += "{: <20}{: <15}{: <15}{: <15}{: <15}\n".format(
            "Name", "Standard", "Special A", "Special B", "Last on"
        )

        for person in self.date_last_on_shift.keys():
            if len(person.name) > 16:
                formatted += f"{person.name[:16] + '...': <20}"
            else:
                formatted += f"{person.name: <20}"

            formatted += f"{self.num_of_shifts[ShiftType.STANDARD][person]: <15}"
            formatted += f"{self.num_of_shifts[ShiftType.SPECIAL_A][person]: <15}"
            formatted += f"{self.num_of_shifts[ShiftType.SPECIAL_B][person]: <15}"
            formatted += f"{(self.date_last_on_shift[person] - self.now).days: <15}"

            formatted += "\n"
        return formatted
