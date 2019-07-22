# OR-Shifty
`OR-Shifty` is a CLI app to automate assignment of on-call shifts via constraint solving by use of the
[OR-tools](https://github.com/google/or-tools) library.

It is designed to accept two JSON files as input:

- a config file which describes the desired on-call rota, the people to assign, and any constraints
- a history file which describes past shifts per person, to be used by certain constraints described below

It will then attempt to create a rota allocation given these inputs and print it either on terminal or as JSON to an
output file if provided.

The given constraints can be prioritised so if a solution cannot be found that satisfies all of them the tool will
drop the least important constraint and try again, repeatedly, until a solution is found or no more constraints can
be dropped. If any constraints had to be dropped the tool will also print to the terminal which of the original
constraints were violated, for which person, and on which day.

## Use
Help:

```bash
shifty --help
```

Basic use:

```bash
shifty --config <path_to_config.json> --history <path_to_history.json> [--output <path_to_optional_output.json>]
```

### Shift types
Any shift can be assigned one of three types. These types have no intrinsic meaning and only exist so different 
constraints can be applied to different shifts, e.g. it might be desired to have more unassigned days after having a
Saturday shift or similar.

The currently supported shift types are:

- STANDARD
- SPECIAL_A
- SPECIAL_B

### Constraints
Solver constraints fall into one of two categories:

- Mandatory, that are always included
- User selected, that can be included and configured using the config input file

For each user selected constraint there will be an example of the JSON configuration needed to include it.

User selected constraints can also be given a priority. If a solution can not be found the constraints with the highest
priority number will be dropped and the solver will retry, then the constraints with the second highest priority
number will be dropped and so on. Priority must be a positive integer. A priority of 0 means the constraint cannot ever
be dropped. If multiple constraints have the same priority and that priority is due to be dropped then all these
constraints will be dropped together.

Constraints can also be named to make them easier to manager by providing `"name": "constraint name"` in the JSON
config.

It is valid to include the same type of constraint multiple times in the config, e.g. by having a stricter constraint
with a higher priority number, followed by a more permissive one with a lower priority number. This way the solver
will try to meet the strict one first, but if it cannot it will then at least try to meet the more permissive one.

The mandatory constraints are mostly common sense and can be seen in the code, e.g. you can't assign Eve's first shift
twice, etc.

The user selected constraints are as follows:

#### Each person works at most X shifts per assignment period
```json
"constraints": [
    {
      "type": "EachPersonWorksAtMostXShiftsPerAssignmentPeriod",
      "priority": 0,
      "params": {"x":  1}
    }
]
```

An assignment period is one run of the program with given input files. This constraints that a person can only be
assigned X of these shifts.

#### There should be at least X days between ops
```json
"constraints": [
    {
      "type": "ThereShouldBeAtLeastXDaysBetweenOps",
      "priority": 0,
      "params": {"x":  4}
    }
]
```

Subtract the last date on ops from the date assigned on a shift. The resulting number of days must be greater that X.

#### There should be at least X days between ops of shift types
```json
"constraints": [
    {
      "type": "ThereShouldBeAtLeastXDaysBetweenOpsOfShiftTypes",
      "priority": 0,
      "params": {"x":  8, "shift_types": ["SPECIAL_A", "SPECIAL_B"]}
    }
]
```
Subtract the last date on ops of any the given types from the date assigned on a shift of one of the given types. The
resulting number of days must be grater than X. In the example configuration someone cannot be assigned to a
SPECIAL_A or SPECIAL_B type shift if they have had a SPECIAL_A or SPECIAL_B shift in the last 8 days.

#### Respect person restrictions per shift type
```json
"constraints": [
    {
      "type": "RespectPersonRestrictionsPerShiftType",
      "priority": 0,
      "params": {"forbidden_by_shift_type": {"special_a": ["Alice"]}}
    }
]
```

Disallow particular people from being assigned any shifts of a given type.

#### Respect person restrictions per day
```json
"constraints": [
    {
      "type": "RespectPersonRestrictionsPerDay",
      "name": "Holidays",
      "priority": 0,
      "params": {"restrictions": {"Alice": ["2019-11-01"]}}
    }
]
```

Disallow particular people from being assigned any shifts on a given date.

### Objective function
When scheduling the solver will choose between possible solutions that satisfy the constraints by using an objective 
function. Each possible solution will be assigned a score using this function and the solution with the highest score
will be chosen.

There is currently support for only one type of objective function called `RankingWeight`.

#### RankingWeight
This objective function will rank people for each shift type based on the following criteria:

1. How many shifts of the given type have they done before
1. How recently have they been on shift
1. Their name (just to ensure there is a total ordering)

In addition it will also rank someone being assigned a second shift below everyone else being assigned their first shift
and so on for possible additional shifts on the same person.

e.g. we have Bob, Alice, and Eve. Bob has done 10 shifts, Alice and Eve have done 8 each. Alice was last on call 2 days
ago and Even was 4 days ago. Everyone can be assigned a maximum of two shifts. The ranking would be:

1. Eve, 1st shift
1. Alice, 1st shift
1. Bob, 1st shift
1. Eve, 2nd shift
1. Alice, 2nd shift
1. Bob, 2nd shift

Eve is given the highest priority because she is tied for least number of shifts done, but has not been on call as
recently. Second shifts are ranked the same way, but after all first shifts.

Each level of this rank is then assigned a weight that is higher the further up in the ranking. 

There is a large gap in the weights when switching from the first shift to the second and so on in order to discourage
assigning multiple shifts before exhausting other possibilities.

This process is repeated for each shift type. The resulting weights are then added together to produce the final score.
This final score is then given as a reward to the solver for assigning the corresponding person/shift.

### Config
Examples can be found under `examples`.

The config file describes the desired on-call rota, the people to assign, and any constraints. The meaning of its
sections are as follows:

- `shifts`: contains one entry for each shift to assign, along with its name, and type
- `people`: the people to assign
- `max_shifts_per_person`: a hard limit on how many shifts a single person can be assigned
- `objective`: the chosen objective function
- `constraints`: the chosen constraints

### History
Examples can be found under `examples`.

The history file describes past shifts per person, to be used by certain constraints. The meaning of its sections
are as follows:

- `shifts`: one entry per past shift a person has done, including its type
- `offset`: offsets to be added to number of shifts done per type for each person

## Development
OR-Shifty is Python3 application developed using [Poetry](https://github.com/python-poetry/poetry). The minimum required
Python version, project dependencies, and other project information can be found in the `pyproject.toml` file.

For ease of development there is a `Makefile`.

```bash
make help     # Get a list of all supported make targets
make freeze   # Update and freeze python requirements
make test     # Run tests
make format   # Run formatters and linters
make install  # Install project dependencies from poetry.lock, project module, and `shifty` script
make build    # Build source and wheels
```

Before submitting any pull requests `make test` and `make format` must both be run an be passing.

## License
See the LICENSE file that is included with this repository.
