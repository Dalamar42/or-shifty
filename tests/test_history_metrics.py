from datetime import date

from shifty.data import History, PastShift, Person, Shift, ShiftType
from shifty.history_metrics import num_of_shifts


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

    shifts = num_of_shifts(history, [person_a, person_b])

    assert shifts == {
        ShiftType.NORMAL: {person_a: 0, person_b: 1},
        ShiftType.SATURDAY: {person_a: 2, person_b: 0},
        ShiftType.SUNDAY: {person_a: 1, person_b: 1},
    }
