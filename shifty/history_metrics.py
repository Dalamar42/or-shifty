from datetime import date, timedelta
from typing import Dict, List, NamedTuple

from shifty.data import History, Person, ShiftType

NEVER = date(1970, 1, 1)


class HistoryMetrics(NamedTuple):
    num_of_shifts: Dict[ShiftType, Dict[Person, int]]
    date_last_on_shift: Dict[Person, date]
    free_days_of_shift_type_since_last_on_shift: Dict[ShiftType, Dict[Person, int]]

    @classmethod
    def build(cls, history: History, people: List[Person], now: date):
        return cls(
            num_of_shifts=_num_of_shifts(history, people),
            date_last_on_shift=_date_last_on_shift(history, people),
            free_days_of_shift_type_since_last_on_shift=_free_days_of_type_since_last_on_shift(
                history, people, now
            ),
        )


def _num_of_shifts(history: History, people: List[Person]):
    return {
        shift_type: _num_of_shifts_for_type(history, people, shift_type)
        for shift_type in ShiftType
    }


def _num_of_shifts_for_type(
    history: History, people: List[Person], shift_type: ShiftType
):
    shifts = {person: 0 for person in people}
    for past_shift in history.past_shifts:
        if past_shift.counts_as(shift_type) and past_shift.person in shifts:
            shifts.setdefault(past_shift.person, 0)
            shifts[past_shift.person] += 1
    return shifts


def _date_last_on_shift(history: History, people: List[Person]):
    people_seen = set()
    date_last = {person: NEVER for person in people}
    for past_shift in history.past_shifts:
        if past_shift.person in date_last and past_shift.person not in people_seen:
            people_seen.add(past_shift.person)
            date_last[past_shift.person] = past_shift.day
    return date_last


def _free_days_of_type_since_last_on_shift(
    history: History, people: List[Person], now: date
):
    return {
        shift_type: _free_days_of_type_since_last_on_shift_for_type(
            history, people, now, shift_type
        )
        for shift_type in ShiftType
    }


def _free_days_of_type_since_last_on_shift_for_type(
    history: History, people: List[Person], now: date, shift_type: ShiftType
):
    people_seen = set()
    free_since = {person: 1 << 16 for person in people}
    for past_shift in history.past_shifts:
        if (
            past_shift.counts_as(shift_type)
            and past_shift.person in free_since
            and past_shift.person not in people_seen
        ):
            people_seen.add(past_shift.person)

            from_date = past_shift.day + timedelta(days=1)
            day_gen = (
                from_date + timedelta(x + 1) for x in range((now - from_date).days)
            )
            if shift_type is ShiftType.WEEKDAY:
                day_filter = lambda day: day.weekday() < 5
            elif shift_type is ShiftType.SATURDAY:
                day_filter = lambda day: day.weekday() == 5
            elif shift_type is ShiftType.SUNDAY:
                day_filter = lambda day: day.weekday() == 6
            else:
                assert False, shift_type

            free_since[past_shift.person] = sum(1 for day in day_gen if day_filter(day))
    return free_since
