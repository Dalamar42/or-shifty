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
