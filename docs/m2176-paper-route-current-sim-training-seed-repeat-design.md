# M2176 Paper-Route Current-Sim Training-Seed Repeat Design

- status: completed
- decision: `current_sim_training_seed_repeat_design_admit_materialization`
- manifest: `experiments/manifests/m2176-paper-route-current-sim-training-seed-repeat-design.json`
- training in M2176: `false`
- measured execution in M2176: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2175 audits M2174 as complete measured execution but not ranking-ready:

```text
episode_count = 320
failure_count = 0
raw_success = 63 / 320
active limitation = one training seed per trainable profile
secondary limitation = offtrack-dominated outcomes
```

M2176 freezes a controlled repeat protocol to test whether the visible M2174
profile differences survive training-seed variation.

## Repeat Structure

Use three training-repeat groups:

| Repeat | Role | Train? | Source |
| --- | --- | --- | --- |
| `repeat_0_existing` | existing reference group | no | M2171 checkpoints and M2174 measured output |
| `repeat_1_seed_21761` | new repeat group | yes | train 7 profile checkpoints with seed group 21761 |
| `repeat_2_seed_21762` | new repeat group | yes | train 7 profile checkpoints with seed group 21762 |

The repeat isolates training seed. It must not change:

```text
task specs;
profile definitions;
actor inputs;
training budget;
reward;
evaluation seed policy;
measured runner;
M2171/M2174 reference artifacts.
```

## Frozen Training Seeds

Each trainable profile gets a deterministic seed per repeat group.

`repeat_0_existing` uses the already materialized M2171 seeds:

```text
L0_current_masked = 119000
L1_one_step = 119001
L2_window_13 = 119002
L2_window_25 = 119003
L2_window_50 = 119004
L2_window_100 = 119005
L3_online_gru = 119006
L3_reset_control = alias to L3_online_gru
```

`repeat_1_seed_21761`:

```text
L0_current_masked = 2176100
L1_one_step = 2176101
L2_window_13 = 2176102
L2_window_25 = 2176103
L2_window_50 = 2176104
L2_window_100 = 2176105
L3_online_gru = 2176106
L3_reset_control = alias to same-repeat L3_online_gru
```

`repeat_2_seed_21762`:

```text
L0_current_masked = 2176200
L1_one_step = 2176201
L2_window_13 = 2176202
L2_window_25 = 2176203
L2_window_50 = 2176204
L2_window_100 = 2176205
L3_online_gru = 2176206
L3_reset_control = alias to same-repeat L3_online_gru
```

## Frozen Budget and Evaluation Policy

Training budget remains the M2170 smoke budget:

```text
total_steps = 1024
rollout_steps = 64
num_envs = 2
update_epochs = 1
minibatch_size = 128
learning_rate = 0.0001
device = cpu
```

Evaluation must reuse the same current-sim task panel and evaluation seed
policy:

```text
executable specs:
  runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json

base workload:
  runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv

M2174 reference workload:
  runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv

eval seed policy:
  preserve per-spec eval_seed_override where present;
  otherwise use the same eval seed base 217400.
```

Using the same evaluation seeds is intentional: the repeat tests training-seed
reliability, not scenario-sampling reliability.

## M2177 Materialization Target

M2177 should implement and run only repeat checkpoint/workload materialization.

Output:

```text
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/summary.json
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeat_group_rows.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/profile_checkpoint_rows.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeats/repeat_1_seed_21761/materialized_workload.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/repeats/repeat_2_seed_21762/materialized_workload.csv
```

M2177 may train exactly:

```text
2 new repeat groups x 7 trainable profiles = 14 checkpoint training commands.
```

M2177 must not train `L3_reset_control`; it must alias to the same-repeat
`L3_online_gru` checkpoint.

## Metadata Requirements

Repeat materialized workloads should add or preserve enough metadata for later
audit:

```text
training_repeat_id
training_seed_group
profile_training_seed
profile_checkpoint_source_profile
checkpoint_materialization_mode
base_workload_id
```

If the existing measured runner does not preserve these fields into episode
rows, a later measured-run design must either extend the runner metadata fields
or use workload-id parsing with an explicit audit. The preferred route is to
preserve them as first-class metadata fields before repeat measured execution.

## Pass Criteria for M2177

M2177 passes only if:

```text
repeat_group_count == 3
new_repeat_group_count == 2
new_training_command_count == 14
successful_training_command_count == 14
failed_training_command_count == 0
new_materialized_workload_count == 640
checkpoint_path_missing_count == 0
checkpoint_path_exists_count == 640
reset_control_trained_count == 0
guardrail_violation_count == 0
```

M2177 is still not a measured-execution result.

## Claim Boundary

Allowed after a clean M2177:

```text
The repeat checkpoint/workload panel is materialized for two additional
training seed groups.
```

Still not allowed:

```text
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2177 should implement the repeat materializer and run the frozen materialization
only. M2178 must audit the materialized repeat panel before any repeat measured
execution command is designed.
