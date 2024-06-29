import re
import json
from collections import defaultdict
import sys

if len(sys.argv) < 3:
    print("Usage: python analyze_slowest_tests.py <log_file> <analysis_file>")
    sys.exit(1)

log_file = sys.argv[1]
analysis_file = sys.argv[2]

# Parse the log file
test_pattern = re.compile(r"\* test (.+?) \((.+?)\) \[(.+?)\:(\d+)\]")

test_data = defaultdict(lambda: {'count': 0, 'times': []})

with open(log_file, 'r') as f:
    for line in f:
        match = test_pattern.search(line)
        if match:
            test_name, module, test_time, file_path, line_number = match.groups()
            test_time_ms = float(test_time.replace('ms', ''))
            key = f"{test_name} ({module}) [{file_path}:{line_number}]"
            test_data[key]['count'] += 1
            test_data[key]['times'].append(test_time_ms)

# Compute statistics
analysis_results = []

for key, data in test_data.items():
    times = data['times']
    analysis_results.append({
        'test_name': key,
        'count': data['count'],
        'average_time_s': round(sum(times) / len(times) / 1000, 2),
        'min_time_s': round(min(times) / 1000, 2),
        'max_time_s': round(max(times) / 1000, 2),
        'times': [round(t / 1000, 2) for t in times]
    })

# Save analysis results to a JSON file
with open(analysis_file, 'w') as f:
    json.dump(analysis_results, f, indent=2)

print(f"Analysis complete. Results saved to {analysis_file}.")
