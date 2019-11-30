from datetime import date

from shifty.data import History, PastShift, Person, Shift, ShiftType
from shifty.history_metrics import HistoryMetrics


def test_num_of_shifts():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        [
            PastShift.build(person_a, date(2019, 8, 31), Shift("shift")),  # Sat
            PastShift.build(person_b, date(2019, 9, 1), Shift("shift")),  # Sun
            PastShift.build(
                person_a, date(2019, 9, 2), Shift("shift"), override_as_sunday=True
            ),  # Mon
            PastShift.build(person_b, date(2019, 9, 3), Shift("shift")),  # Tue
            PastShift.build(
                person_a, date(2019, 9, 4), Shift("shift"), override_as_saturday=True
            ),  # Wed
            PastShift.build(person_c, date(2019, 9, 5), Shift("shift")),  # Thu
        ]
    )

    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 5))

    assert metrics.num_of_shifts == {
        ShiftType.WEEKDAY: {person_a: 0, person_b: 1},
        ShiftType.SATURDAY: {person_a: 2, person_b: 0},
        ShiftType.SUNDAY: {person_a: 1, person_b: 1},
    }


def test_date_last_on_shift():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")
    person_d = Person("d")

    history = History.build(
        [
            PastShift.build(person_a, date(2019, 8, 31), Shift("shift")),  # Sat
            PastShift.build(person_b, date(2019, 9, 1), Shift("shift")),  # Sun
            PastShift.build(
                person_a, date(2019, 9, 2), Shift("shift"), override_as_sunday=True
            ),  # Mon
            PastShift.build(person_b, date(2019, 9, 3), Shift("shift")),  # Tue
            PastShift.build(
                person_a, date(2019, 9, 4), Shift("shift"), override_as_saturday=True
            ),  # Wed
            PastShift.build(person_c, date(2019, 9, 5), Shift("shift")),  # Thu
        ]
    )

    metrics = HistoryMetrics.build(
        history, [person_a, person_b, person_d], date(2019, 9, 8)
    )

    assert metrics.date_last_on_shift == {
        person_a: date(2019, 9, 4),
        person_b: date(2019, 9, 3),
        person_d: None,
    }


def test_free_days_of_type_since_last_on_shift():
    person_a = Person("a")
    person_b = Person("b")
    person_c = Person("c")

    history = History.build(
        [
            PastShift.build(person_a, date(2019, 8, 31), Shift("shift")),  # Sat
            PastShift.build(person_b, date(2019, 9, 1), Shift("shift")),  # Sun
            PastShift.build(person_a, date(2019, 9, 2), Shift("shift")),  # Mon
            PastShift.build(person_b, date(2019, 9, 7), Shift("shift")),  # Sat
            PastShift.build(person_c, date(2019, 9, 8), Shift("shift")),  # Sun
        ]
    )
    metrics = HistoryMetrics.build(history, [person_a, person_b], date(2019, 9, 16))

    assert metrics.free_days_of_shift_type_since_last_on_shift == {
        ShiftType.WEEKDAY: {person_a: 9, person_b: None},
        ShiftType.SATURDAY: {person_a: 2, person_b: 1},
        ShiftType.SUNDAY: {person_a: None, person_b: 2},
    }
