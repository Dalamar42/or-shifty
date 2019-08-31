from typing import Any, NamedTuple


class Constraint(NamedTuple):
    name: str
    fn: Any
    priority: int  # lower is higher

    @classmethod
    def build(cls, fn, priority):
        return cls(name=fn.__name__[1:], fn=fn, priority=priority)

    def __str__(self):
        return self.name

    def apply(self, model, assignments, people, shifts_by_day):
        self.fn(model, assignments, people, shifts_by_day)


def _each_shift_is_assigned_to_exactly_one_person(
    model, assignments, people, shifts_by_day
):
    for day, shifts in shifts_by_day.items():
        for shift in shifts:
            model.Add(
                sum(
                    assignments[(person.index, day.index, shift.index)]
                    for person in people
                )
                == 1
            )


def _each_person_works_at_most_one_shift_per_day(
    model, assignments, people, shifts_by_day
):
    for person in people:
        model.Add(
            sum(
                assignments[(person.index, day.index, shift.index)]
                for day, shifts in shifts_by_day.items()
                for shift in shifts
            )
            <= 1
        )


CONSTRAINTS = [
    Constraint.build(fn=_each_shift_is_assigned_to_exactly_one_person, priority=0),
    Constraint.build(fn=_each_person_works_at_most_one_shift_per_day, priority=0),
]
assert CONSTRAINTS == sorted(CONSTRAINTS, key=lambda c: c.priority)
