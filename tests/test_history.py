from datetime import date

from shifty.base_types import DayShift, Person
from shifty.history import History, PastShiftOffset
from shifty.history_metrics import NEVER, HistoryMetrics
from shifty.shift import AssignedShift, ShiftType


def test_num_of_shifts():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        [
            AssignedShift.build(person_a, date(2019, 8, 31), DayShift("shift")),  # Sat
            AssignedShift.build(person_b, date(2019, 9, 1), DayShift("shift")),  # Sun
            AssignedShift.build(person_a, date(2019, 9, 2), DayShift("shift")),  # Mon
            AssignedShift.build(person_b, date(2019, 9, 3), DayShift("shift")),  # Tue
            AssignedShift.build(person_a, date(2019, 9, 4), DayShift("shift")),  # Wed
            AssignedShift.build(person_c, date(2019, 9, 5), DayShift("shift")),  # Thu
        ]
    )

    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 5))

    assert metrics.num_of_shifts == {
        ShiftType.WEEKDAY: {person_a: 2, person_b: 1},
        ShiftType.SATURDAY: {person_a: 1, person_b: 0},
        ShiftType.SUNDAY: {person_a: 0, person_b: 1},
    }


def test_num_of_shifts_with_offsets():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        past_shifts=[
            AssignedShift.build(person_a, date(2019, 8, 31), DayShift("shift")),  # Sat
            AssignedShift.build(person_b, date(2019, 9, 1), DayShift("shift")),  # Sun
            AssignedShift.build(person_a, date(2019, 9, 2), DayShift("shift")),  # Mon
            AssignedShift.build(person_b, date(2019, 9, 3), DayShift("shift")),  # Tue
            AssignedShift.build(person_a, date(2019, 9, 4), DayShift("shift")),  # Wed
            AssignedShift.build(person_c, date(2019, 9, 5), DayShift("shift")),  # Thu
        ],
        offsets=[
            PastShiftOffset.build(
                person=person_a, shift_type=ShiftType.WEEKDAY, offset=2
            ),
            PastShiftOffset.build(
                person=person_b, shift_type=ShiftType.SATURDAY, offset=1
            ),
            PastShiftOffset.build(
                person=person_c, shift_type=ShiftType.SUNDAY, offset=5
            ),
        ],
    )

    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 5))

    assert metrics.num_of_shifts == {
        ShiftType.WEEKDAY: {person_a: 4, person_b: 1},
        ShiftType.SATURDAY: {person_a: 1, person_b: 1},
        ShiftType.SUNDAY: {person_a: 0, person_b: 1, person_c: 5},
    }


def test_date_last_on_shift():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")
    person_d = Person("d")

    history = History.build(
        [
            AssignedShift.build(person_a, date(2019, 8, 31), DayShift("shift")),  # Sat
            AssignedShift.build(person_b, date(2019, 9, 1), DayShift("shift")),  # Sun
            AssignedShift.build(person_a, date(2019, 9, 2), DayShift("shift")),  # Mon
            AssignedShift.build(person_b, date(2019, 9, 3), DayShift("shift")),  # Tue
            AssignedShift.build(person_a, date(2019, 9, 4), DayShift("shift")),  # Wed
            AssignedShift.build(person_c, date(2019, 9, 5), DayShift("shift")),  # Thu
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


def test_free_days_of_type_since_last_on_shift():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        [
            AssignedShift.build(person_a, date(2019, 8, 31), DayShift("shift")),  # Sat
            AssignedShift.build(person_b, date(2019, 9, 1), DayShift("shift")),  # Sun
            AssignedShift.build(person_a, date(2019, 9, 2), DayShift("shift")),  # Mon
            AssignedShift.build(person_b, date(2019, 9, 7), DayShift("shift")),  # Sat
            AssignedShift.build(person_c, date(2019, 9, 8), DayShift("shift")),  # Sun
        ]
    )
    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 16))

    assert metrics.free_days_of_shift_type_since_last_on_shift == {
        ShiftType.WEEKDAY: {person_a: 9, person_b: 1 << 16},
        ShiftType.SATURDAY: {person_a: 2, person_b: 1},
        ShiftType.SUNDAY: {person_a: 1 << 16, person_b: 2},
    }
