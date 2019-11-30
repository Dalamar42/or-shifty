from shifty.cli import parse_args
from shifty.model import assign


def test_solution_when_all_constraints_cannot_be_satisfied():
    config_file_path = "tests/test_files/no_solution/config.json"
    history_file_path = "tests/test_files/no_solution/history.json"
    inputs = parse_args(["--config", config_file_path, "--history", history_file_path])

    solution = assign(
        people=inputs.people,
        max_shifts_per_person=inputs.max_shifts_per_person,
        shifts_by_day=inputs.shifts_by_day,
        history=inputs.history,
        now=inputs.now,
        objective=inputs.objective,
        constraints=inputs.constraints,
    )
    assert len(list(solution)) == 2
