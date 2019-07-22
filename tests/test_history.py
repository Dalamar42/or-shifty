from datetime import date

from or_shifty.history import History, PastShiftOffset
from or_shifty.history_metrics import NEVER, HistoryMetrics
from or_shifty.person import Person
from or_shifty.shift import AssignedShift, ShiftType


def test_num_of_shifts():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        [
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2019, 8, 31), person_a,),
            AssignedShift("shift", ShiftType.SPECIAL_B, date(2019, 9, 1), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 2), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 3), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 4), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 5), person_c,),
        ]
    )

    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 5))

    assert metrics.num_of_shifts == {
        ShiftType.STANDARD: {person_a: 2, person_b: 1},
        ShiftType.SPECIAL_A: {person_a: 1, person_b: 0},
        ShiftType.SPECIAL_B: {person_a: 0, person_b: 1},
    }


def test_num_of_shifts_with_offsets():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        past_shifts=[
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2019, 8, 31), person_a,),
            AssignedShift("shift", ShiftType.SPECIAL_B, date(2019, 9, 1), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 2), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 3), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 4), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 5), person_c,),
        ],
        offsets=[
            PastShiftOffset(person=person_a, shift_type=ShiftType.STANDARD, offset=2),
            PastShiftOffset(person=person_b, shift_type=ShiftType.SPECIAL_A, offset=1),
            PastShiftOffset(person=person_c, shift_type=ShiftType.SPECIAL_B, offset=5),
        ],
    )

    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 5))

    assert metrics.num_of_shifts == {
        ShiftType.STANDARD: {person_a: 4, person_b: 1},
        ShiftType.SPECIAL_A: {person_a: 1, person_b: 1},
        ShiftType.SPECIAL_B: {person_a: 0, person_b: 1, person_c: 5},
    }


def test_date_last_on_shift():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")
    person_d = Person("d")

    history = History.build(
        [
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2019, 8, 31), person_a,),
            AssignedShift("shift", ShiftType.SPECIAL_B, date(2019, 9, 1), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 2), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 3), person_b,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 4), person_a,),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 5), person_c,),
        ]
    )

    metrics = HistoryMetrics.build(
        history, [person_a, person_b, person_d], date(2019, 9, 8)
    )

    assert metrics.date_last_on_shift == {
        person_a: date(2019, 9, 4),
        person_b: date(2019, 9, 3),
        person_d: NEVER,
    }


def test_date_last_on_shift_of_type():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")
    person_d = Person("d")

    history = History.build(
        [
            AssignedShift("shift", ShiftType.SPECIAL_A, date(2019, 8, 31), person_a),
            AssignedShift("shift", ShiftType.SPECIAL_B, date(2019, 9, 1), person_b),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 2), person_a),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 3), person_b),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 4), person_a),
            AssignedShift("shift", ShiftType.STANDARD, date(2019, 9, 5), person_c),
        ]
    )

    metrics = HistoryMetrics.build(
        history, [person_a, person_b, person_d], date(2019, 9, 8)
    )

    assert metrics.date_last_on_shift_of_type == {
        person_a: {
            ShiftType.STANDARD: date(2019, 9, 4),
            ShiftType.SPECIAL_A: date(2019, 8, 31),
            ShiftType.SPECIAL_B: NEVER,
        },
        person_b: {
            ShiftType.STANDARD: date(2019, 9, 3),
            ShiftType.SPECIAL_A: NEVER,
            ShiftType.SPECIAL_B: date(2019, 9, 1),
        },
        person_d: {
            ShiftType.STANDARD: NEVER,
            ShiftType.SPECIAL_A: NEVER,
            ShiftType.SPECIAL_B: NEVER,
        },
    }
