from typing import Any, NamedTuple

from ortools.sat.python import cp_model


class Indexed(NamedTuple):
    index: int
    val: Any


class Person(NamedTuple):
    name: str


class Shift(NamedTuple):
    name: str


def index_inputs(people, shifts_by_day):
    indexed_people = []
    indexed_shifts_by_day = {}

    for index, person in enumerate(people):
        indexed_people.append(Indexed(index=index, val=person))

    for index, day in enumerate(sorted(shifts_by_day.keys())):
        day = Indexed(index=index, val=day)

        for index, shift in enumerate(shifts_by_day[day.val]):
            indexed_shifts_by_day.setdefault(day, []).append(
                Indexed(index=index, val=shift)
            )

    return indexed_people, indexed_shifts_by_day


def assign_shifts(input_people, input_shifts_by_day):
    people, shifts_by_day = index_inputs(input_people, input_shifts_by_day)

    model = cp_model.CpModel()

    assignments = init_assignments(model, people, shifts_by_day)

    each_shift_is_assigned_to_exactly_one_person(
        model, assignments, people, shifts_by_day
    )
    each_person_works_at_most_one_shift_per_day(
        model, assignments, people, shifts_by_day
    )

    solver = cp_model.CpSolver()
    solver.Solve(model)

    for day, shifts in shifts_by_day.items():
        for shift in shifts:
            for person in people:
                index = (person.index, day.index, shift.index)
                if solver.Value(assignments[index]) == 1:
                    yield person.val, day.val, shift.val


def each_shift_is_assigned_to_exactly_one_person(
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


def each_person_works_at_most_one_shift_per_day(
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


def init_assignments(model, people, shifts_by_day):
    assignments = {}
    for person in people:
        for day, shifts in shifts_by_day.items():
            for shift in shifts:
                index = (person.index, day.index, shift.index)
                assignments[index] = model.NewBoolVar(
                    f"shift_{person.val.name}_{day.val}_{shift.val.name}"
                )
    return assignments
