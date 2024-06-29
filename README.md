# mix_test_slowest

## After 100 Runs of `mix test --slowest` in alloy_access_web repo

```
Removing Top 10 Tests could save '1.51' seconds from test suite runs.

Top 10 Tests with Most Instances:
 count  avg_s  min_s  max_s                                                                 file_path                                             test_name
    95   0.36   0.13   1.32 test/alloy_access_web/internal_api/public/session_controller_test.exs:261 POST /internal-api/v1/public/login login with id_t...
    82   0.12   0.11   0.16 test/alloy_access/cloud_bridge_api/smrtp_test.exs:145                     handle_reply/2 resets temporary door mode when tri...
    81   0.12   0.12   0.15 test/alloy_access/cloud_bridge_api/smrtp_test.exs:114                     handle_reply/2 resets temporary door mode when tri...
    77   0.12   0.11   0.19 test/alloy_access_web/api/member_door_test.exs:186                        POST /api/v1/members/:member_id/doors/:door_id doe...
    22   0.15   0.14   0.16 test/alloy_access/controller_sync/mpl/doors_sync_test.exs:157             base_commands/2 can delete a door with elevator_ac...
    20   0.11   0.11   0.12 test/alloy_access/mpl_test.exs:44                                         handle_reply Does not broadcast reply without subs...
    18   0.14   0.12   0.19 test/alloy_access_web/internal_api/user/controller_test.exs:297           PUT /internal-api/v1/controllers/:controller_id/fi...
    16   0.13   0.11   0.20 test/alloy_access_web/internal_api/user/member_access_levels_test.exs:358 POST /internal-api/member-access-levels/:member_id...
    12   0.13   0.12   0.16 test/alloy_access_web/internal_api/site_firmware_controller_test.exs:42   GET /internal-api/v1/sites/site-firmware lists onl...
    12   0.13   0.11   0.16 test/alloy_access_web/internal_api/user/member_access_levels_test.exs:322 POST /internal-api/member-access-levels/:member_id...

Distribution of tests based on 'count':
Range      Number of Tests      Total Avg Time (s)
--------------------------------------------------
> 75%      4                    0.72
50% - 75%  0                    0.0
25% - 50%  0                    0.0
< 25%      278                  105.72

Distribution of tests based on 'avg_s':
Range      Number of Tests      Total Avg Time (s)
--------------------------------------------------
> 0.2      157                  88.47
0.1 - 0.2  125                  17.97
0.05 - 0.1 0                    0.0
< 0.05     0                    0.0
```
