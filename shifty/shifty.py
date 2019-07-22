from datetime import date

from ortools.sat.python import cp_model

from model import Person, Shift, assign_shifts


def ops():
    solution = assign_shifts(
        [Person(name=f"person_{index}") for index in range(7)],
        {
            date(2019, 1, 1): [Shift(name="shift")],
            date(2019, 1, 2): [Shift(name="shift")],
            date(2019, 1, 3): [Shift(name="shift")],
            date(2019, 1, 4): [Shift(name="shift")],
            date(2019, 1, 5): [Shift(name="shift")],
            date(2019, 1, 6): [Shift(name="shift")],
            date(2019, 1, 7): [Shift(name="shift")],
        },
    )

    for person, day, shift in solution:
        print(f"{person.name} works {day}/{shift.name}")
    print()


def nurses():
    num_nurses = 5
    num_shifts = 3
    num_days = 7

    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    shift_requests = [
        [[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 1]],
        [[0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 1, 0], [1, 0, 0], [0, 0, 0], [0, 0, 1]],
        [[0, 1, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 1], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]],
    ]

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar("shift_n%id%is%i" % (n, d, s))

    # Each shift is assigned to exactly one nurse in .
    for d in all_days:
        for s in all_shifts:
            model.Add(sum(shifts[(n, d, s)] for n in all_nurses) == 1)

    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.Add(sum(shifts[(n, d, s)] for s in all_shifts) <= 1)

    # min_shifts_assigned is the largest integer such that every nurse can be
    # assigned at least that number of shifts.
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    max_shifts_per_nurse = min_shifts_per_nurse + 1
    for n in all_nurses:
        num_shifts_worked = sum(shifts[(n, d, s)] for d in all_days for s in all_shifts)
        model.Add(min_shifts_per_nurse <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_nurse)

    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_nurses
            for d in all_days
            for s in all_shifts
        )
    )
    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.Solve(model)
    for d in all_days:
        print("Day", d)
        for n in all_nurses:
            for s in all_shifts:
                if solver.Value(shifts[(n, d, s)]) == 1:
                    if shift_requests[n][d][s] == 1:
                        print("Nurse", n, "works shift", s, "(requested).")
                    else:
                        print("Nurse", n, "works shift", s, "(not requested).")
        print()

    # Statistics.
    print()
    print("Statistics")
    print(
        "  - Number of shift requests met = %i" % solver.ObjectiveValue(),
        "(out of",
        num_nurses * min_shifts_per_nurse,
        ")",
    )
    print("  - wall time       : %f s" % solver.WallTime())


def main():
    ops()


if __name__ == "__main__":
    main()
