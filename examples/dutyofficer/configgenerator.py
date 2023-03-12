import csv
import json
import datetime, calendar

year = 2022
month = 2
data = {'shifts': [], 'people': [], 'constraints': []}
people = []
uniteweekends = []
weekdaysonly = []
student = []
atmostonceamonth = []

with open('people.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            if row[1] == 'TRUE':
                people.append(row[0])
            else:
                continue
            if row[2] == 'TRUE':
                uniteweekends.append(row[0])
            if row[3] == 'TRUE':
                weekdaysonly.append(row[0])
            if row[4] == 'TRUE':
                student.append(row[0])
            if row[5] == 'TRUE':
                atmostonceamonth.append(row[0])
            line_count += 1
    print(f'Processed {line_count} lines.')

people = list(set(people))

for p in people:
    data['people'].append({"name": p})

if len(weekdaysonly) > 0:
    data['constraints'].append({"type": "RespectPersonRestrictionsPerShiftType", "priority": 0, "name": "Weekdays Only",
                                "params": {"forbidden_by_shift_type": {"special_a": weekdaysonly}}})
if len(student) > 0:
    data['constraints'].append({"type": "RespectPersonRestrictionsPerShiftType", "priority": 0, "name": "Students - Weekends Only",
                                "params": {"forbidden_by_shift_type": {"standard": student}}})

if len(atmostonceamonth) > 0:
    data['constraints'].append({"type": "SpecificPersonsWorksAtMostXShiftsPerAssignmentPeriod", "priority": 0, "name": "At most once a month",
                                "params": {"x": 1, "persons": atmostonceamonth}})

if len(uniteweekends) > 0:
    data['constraints'].append({"type": "RespectConsecutiveShiftRequirement", "priority": 0, "name": "Religious",
                                "params": {"shift_type": "special_a", "persons": uniteweekends}})

data['constraints'].append({"type": "EachPersonWorksAtMostXShiftsPerAssignmentPeriod", "priority": 2, "name": "At most two shifts a month",
                            "params": {"x": 1}})

data['constraints'].append({"type": "ThereShouldBeAtLeastXDaysBetweenOps", "priority": 3, "name": "Minimum days between shifts", "params": {"x": 7}})

data["max_shifts_per_person"] = 2
data["objective"] = "RankingWeight"

num_days = calendar.monthrange(year, month)[1]
days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]

for d in days:
    data['shifts'].append({
        'day': d.isoformat(),
        'name': "ops",
        'type': "special_a" if d.weekday() == 4 or d.weekday() == 5 else "standard",
    })

with open('config.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
