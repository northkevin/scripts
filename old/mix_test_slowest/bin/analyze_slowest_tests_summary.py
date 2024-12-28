import sys
import json
import pandas as pd
import re

if len(sys.argv) < 6:
    print("Usage: python analyze_slowest_tests_summary.py <analysis_file> <summary_file> <top_10_csv> <full_summary_json> <full_summary_csv>")
    sys.exit(1)

analysis_file = sys.argv[1]
summary_file = sys.argv[2]
top_10_csv = sys.argv[3]
full_summary_json = sys.argv[4]
full_summary_csv = sys.argv[5]

# Load the JSON data
with open(analysis_file, 'r') as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Extract file path and line number from test_name and create a combined column
def extract_file_info(test_name):
    match = re.search(r'\[(.+?)\:(\d+)\]', test_name)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    return None

df['file_path'] = df['test_name'].apply(extract_file_info)

# Sort by count and average time
top_tests = df.sort_values(by=['count', 'avg_s'], ascending=[False, False]).head(10)

# Add index numbers for the top tests
top_tests.reset_index(drop=True, inplace=True)
top_tests.index += 1

# Ensure file_path column is fully displayed and left-aligned
pd.set_option('display.max_colwidth', None)

# Limit the length of test_name to fit within a single line
def truncate_test_name(test_name, max_length=50):
    if len(test_name) > max_length:
        return test_name[:max_length] + '...'
    return test_name

top_tests['test_name'] = top_tests['test_name'].apply(truncate_test_name)

# Define a custom format for left-aligned columns
def left_align(column, width):
    return [f'{str(item):<{width}}' for item in column]

# Apply left alignment to file_path
file_path_width = max(top_tests['file_path'].apply(len))
top_tests['file_path'] = left_align(top_tests['file_path'], file_path_width)

# Calculate the total average time saved by removing the top 10 tests
total_time_saved = top_tests['avg_s'].sum().round(2)

# Categorize and count tests based on count and avg_s
count_ranges = {
    '> 75%': df[df['count'] > 75],
    '50% - 75%': df[(df['count'] > 50) & (df['count'] <= 75)],
    '25% - 50%': df[(df['count'] > 25) & (df['count'] <= 50)],
    '< 25%': df[df['count'] <= 25],
}

avg_s_ranges = {
    '> 0.2': df[df['avg_s'] > 0.2],
    '0.1 - 0.2': df[(df['avg_s'] > 0.1) & (df['avg_s'] <= 0.2)],
    '0.05 - 0.1': df[(df['avg_s'] > 0.05) & (df['avg_s'] <= 0.1)],
    '< 0.05': df[df['avg_s'] <= 0.05],
}

# Create distribution summaries
def create_distribution_summary(distribution):
    summary = []
    for range_label, subset in distribution.items():
        num_tests = len(subset)
        total_avg_time = subset['avg_s'].sum().round(2)
        summary.append((range_label, num_tests, total_avg_time))
    return summary

count_summary = create_distribution_summary(count_ranges)
avg_s_summary = create_distribution_summary(avg_s_ranges)

# Print the quick summary
print(f"Removing Top 10 Tests could save '{total_time_saved}' seconds from test suite runs.\n")

# Print the summary of top 10 tests
print("Top 10 Tests with Most Instances:")
print(top_tests[['count', 'avg_s', 'min_s', 'max_s', 'file_path', 'test_name']].to_string(index=False))

# Print the distribution summaries
def print_distribution_summary(summary, title):
    print(f"\nDistribution of tests based on '{title}':")
    print(f"{'Range':<10} {'Number of Tests':<20} {'Total Avg Time (s)':<20}")
    print('-' * 50)
    for range_label, num_tests, total_avg_time in summary:
        print(f"{range_label:<10} {num_tests:<20} {total_avg_time:<20}")

print_distribution_summary(count_summary, 'count')
print_distribution_summary(avg_s_summary, 'avg_s')

# Save the summary to a new JSON file
top_tests.to_json(summary_file, orient='records', indent=2)

# Also save the full summary to a new JSON file for all tests
df.to_json(full_summary_json, orient='records', indent=2)

# Save the full summary to a CSV file for all tests
df.to_csv(full_summary_csv, index=False)

print(f"\nSummary saved to {summary_file}")
print(f"Full summary saved to {full_summary_json}")
