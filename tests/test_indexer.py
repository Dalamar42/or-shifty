from datetime import date

from pytest import fixture

from or_shifty.indexer import IndexEntry, Indexer
from or_shifty.person import Person
from or_shifty.shift import Shift, ShiftType


@fixture
def people():
    return [Person("A"), Person("B")]


@fixture
def max_shifts_per_person():
    return 1


@fixture
def days():
    return [
        date(2019, 11, 26),
        date(2019, 11, 27),
    ]


@fixture
def shifts_per_day(days):
    return {
        day: [Shift(name="shift-1", shift_type=ShiftType.STANDARD, day=day)]
        for day in days
    }


@fixture
def indexer(people, max_shifts_per_person, shifts_per_day):
    return Indexer.build(people, max_shifts_per_person, shifts_per_day)


def test_get_index(indexer, people, days, shifts_per_day):
    assert indexer.get((0, 0, 1, 0)) == IndexEntry(
        (0, 0, 1, 0), people[0], 0, days[1], shifts_per_day[days[1]][0],
    )


def test_iter(indexer, people, days, shifts_per_day):
    assert [entry.idx for entry in indexer.iter()] == [
        (0, 0, 0, 0),
        (0, 0, 1, 0),
        (1, 0, 0, 0),
        (1, 0, 1, 0),
    ]
    entries = list(
        indexer.iter(
            person_filter=people[1],
            person_shift_filter=0,
            day_filter=days[1],
            day_shift_filter=shifts_per_day[days[1]][0],
        )
    )
    assert len(entries) == 1
    assert entries[0].idx == (1, 0, 1, 0)
