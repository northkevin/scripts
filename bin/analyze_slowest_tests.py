import re
import json
from collections import defaultdict

log_file = '/Users/kevin.north/scripts/slowest_tests_db.log'
analysis_file = '/Users/kevin.north/scripts/slowest_tests_analysis.json'

analysis_file = '/mnt/data/slowest_tests_analysis.json'

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
        'average_time_ms': sum(times) / len(times),
        'min_time_ms': min(times),
        'max_time_ms': max(times),
        'times': times
    })

# Save analysis results to a JSON file
with open(analysis_file, 'w') as f:
    json.dump(analysis_results, f, indent=2)

print(f"Analysis complete. Results saved to {analysis_file}.")
