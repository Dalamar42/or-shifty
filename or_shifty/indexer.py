from dataclasses import dataclass
from datetime import date
from typing import Dict, Generator, List, Tuple

from or_shifty.person import Person
from or_shifty.shift import Shift

Idx = Tuple[int, int, int, int]
PersonShift = int


@dataclass(frozen=True)
class IndexEntry:
    idx: Idx
    person: Person
    person_shift: PersonShift
    day: date
    day_shift: Shift


@dataclass(frozen=True)
class Indexer:
    _person_indices: Dict[Person, int]
    _day_indices: Dict[date, int]
    _day_shift_indices: Dict[Tuple[date, Shift], int]

    _index_entries: Dict[Idx, IndexEntry]

    @classmethod
    def build(
        cls,
        people: List[Person],
        max_shifts_per_person: int,
        shifts_per_day: Dict[date, List[Shift]],
    ):
        _person_indices = {}
        _day_indices = {}
        _day_shift_indices = {}
        _index_entries = {}

        for person_idx, person in enumerate(people):
            _person_indices[person] = person_idx

            for person_shift_idx in range(max_shifts_per_person):
                for day_idx, day in enumerate(sorted(shifts_per_day.keys())):
                    _day_indices[day] = day_idx

                    for shift_idx, shift in enumerate(
                        sorted(shifts_per_day[day], key=lambda s: s.name)
                    ):
                        _day_shift_indices[(day, shift)] = shift_idx

                        idx = (
                            person_idx,
                            person_shift_idx,
                            day_idx,
                            shift_idx,
                        )
                        _index_entries[idx] = IndexEntry(
                            idx, person, person_shift_idx, day, shift,
                        )

        return cls(
            _person_indices=_person_indices,
            _day_indices=_day_indices,
            _day_shift_indices=_day_shift_indices,
            _index_entries=_index_entries,
        )

    def get(self, index: Idx) -> IndexEntry:
        return self._index_entries[index]

    def iter(
        self,
        person_filter: Person = None,
        person_shift_filter: PersonShift = None,
        day_filter: date = None,
        day_shift_filter: Shift = None,
    ) -> Generator[IndexEntry, None, None]:
        """Return all indices that match the given filters

        This implementation is not efficient as it sorts and traverses all the indices every
        time. This should be fine for normal use as the cost of solving for the rota should be
        the bottleneck as the indices grow, not this.
        """

        if day_shift_filter is not None:
            assert (
                day_filter is not None
            ), "day_shift_filter can only be used together with day_filter"

        def _filter(idx_):
            (person_idx, person_shift_idx, day_idx, day_shift_idx) = idx_

            if (
                person_filter is not None
                and self._person_indices[person_filter] != person_idx
            ):
                return False

            if (
                person_shift_filter is not None
                and person_shift_filter != person_shift_idx
            ):
                return False

            if day_filter is not None:
                if self._day_indices[day_filter] != day_idx:
                    return False
                if (
                    day_shift_filter is not None
                    and self._day_shift_indices[(day_filter, day_shift_filter)]
                    != day_shift_idx
                ):
                    return False

            return True

        for idx in sorted(self._index_entries.keys()):
            if _filter(idx):
                yield self._index_entries[idx]
