from datetime import date
from typing import List

from shifty.data import History, Person, ShiftType


def num_of_shifts(history: History, people: List[Person]):
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


def days_since_last_on_shift(history: History, people: List[Person], now: date):
    return {
        shift_type: _days_since_last_on_shift_for_type(history, people, now, shift_type)
        for shift_type in ShiftType
    }


def _days_since_last_on_shift_for_type(
    history: History, people: List[Person], now: date, shift_type: ShiftType
):
    people_seen = set()
    days_since = {person: None for person in people}
    for past_shift in history.past_shifts:
        if (
            past_shift.counts_as(shift_type)
            and past_shift.person in days_since
            and past_shift.person not in people_seen
        ):
            people_seen.add(past_shift.person)
            days_since[past_shift.person] = (now - past_shift.day).days
    return days_since
