import csv
import json

import dateparser as dateparser

data = {'shifts': [], 'offsets': []}
with open('history.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            # print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
            data['shifts'].append({
                'person': row[1],
                'day': dateparser.parse(row[0], date_formats=['%d/%m/%Y']).strftime('%Y-%m-%d'),
                'name': 'ops',
                'type': row[2]
            })
            line_count += 1
    print(f'Processed {line_count} lines.')

with open('history.json', 'w') as outfile:
    json.dump(data, outfile,indent=4)
