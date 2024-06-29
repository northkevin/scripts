IO.puts("Number of schedulers online: #{:erlang.system_info(:schedulers_online)}")
IO.puts("Number of schedulers available: #{:erlang.system_info(:schedulers)}")
