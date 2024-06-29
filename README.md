# mix_test_slowest

This project helps you identify and analyze the slowest tests in your Elixir project by running the tests multiple times and analyzing the results.

### Prerequisites

Ensure you have `mise` installed and configured for your project. Also, make sure `pandas` is installed in your environment.

```sh
mise activate
pip install pandas
```

### Running the Tests

To run the tests and collect the slowest test data, use the `run_mix_test_slowest` script.

```sh
bin/run_mix_test_slowest -p <project_directory> -n <number_of_runs> -s <number_of_slowest_tests>
```

- -n <number_of_runs>: Specifies the number of times to run the mix test --slowest command. (Default: 1)
- -p <project_directory>: The path to the Elixir project directory where the mix test command should be run.
- -s <number_of_slowest_tests>: Specifies the number of slowest tests to log in each run. (Default: 10)

Example

```sh
bin/run_mix_test_slowest -n 10 -p ~/dev/alloy_access_web -s 100
```

This command will:

    •	Run mix test --slowest 5 in the ~/dev/alloy_access_web directory 10 times.
    •	Collect the results and save them in slowest_tests_db.log and slowest_tests_logs.
    •	Analyze the log file and generate the analysis JSON file.
    •	Generate a summary JSON file, a summary CSV file, and a full summary JSON and CSV file.

Output

The generated files will be saved in the mix_test_slowest directory:

    •	slowest_tests_analysis.json
    •	slowest_tests_summary.json
    •	top_10_slowest_tests.csv
    •	full_slowest_tests_summary.json
    •	full_slowest_tests_summary.csv

Cleanup

The script will automatically clean up generated files between runs to ensure the log files are fresh for each execution.

## After 100 Runs of `mix test --slowest` in alloy_access_web repo

```

Removing Top 10 Tests could save '1.51' seconds from test suite runs.

Top 10 Tests with Most Instances:
count avg_s min_s max_s file_path test_name
95 0.36 0.13 1.32 test/alloy_access_web/internal_api/public/session_controller_test.exs:261 POST /internal-api/v1/public/login login with id_t...
82 0.12 0.11 0.16 test/alloy_access/cloud_bridge_api/smrtp_test.exs:145 handle_reply/2 resets temporary door mode when tri...
81 0.12 0.12 0.15 test/alloy_access/cloud_bridge_api/smrtp_test.exs:114 handle_reply/2 resets temporary door mode when tri...
77 0.12 0.11 0.19 test/alloy_access_web/api/member_door_test.exs:186 POST /api/v1/members/:member_id/doors/:door_id doe...
22 0.15 0.14 0.16 test/alloy_access/controller_sync/mpl/doors_sync_test.exs:157 base_commands/2 can delete a door with elevator_ac...
20 0.11 0.11 0.12 test/alloy_access/mpl_test.exs:44 handle_reply Does not broadcast reply without subs...
18 0.14 0.12 0.19 test/alloy_access_web/internal_api/user/controller_test.exs:297 PUT /internal-api/v1/controllers/:controller_id/fi...
16 0.13 0.11 0.20 test/alloy_access_web/internal_api/user/member_access_levels_test.exs:358 POST /internal-api/member-access-levels/:member_id...
12 0.13 0.12 0.16 test/alloy_access_web/internal_api/site_firmware_controller_test.exs:42 GET /internal-api/v1/sites/site-firmware lists onl...
12 0.13 0.11 0.16 test/alloy_access_web/internal_api/user/member_access_levels_test.exs:322 POST /internal-api/member-access-levels/:member_id...

Distribution of tests based on 'count':
Range Number of Tests Total Avg Time (s)

---

> 75% 4 0.72
> 50% - 75% 0 0.0
> 25% - 50% 0 0.0
> < 25% 278 105.72

Distribution of tests based on 'avg_s':
Range Number of Tests Total Avg Time (s)

---

> 0.2 157 88.47
> 0.1 - 0.2 125 17.97
> 0.05 - 0.1 0 0.0
> < 0.05 0 0.0

```

```

```
