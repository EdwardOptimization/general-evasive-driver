# M857 V4 Boundary-New-To-M844 Bracket Trace Implementation

## Purpose

M857 implements the M856 no-training trace-first diagnostic for the M854/M855
boundary-new-to-M844 blocker.

The implementation question is:

```text
Why did M854 fail to bracket boundary-new-to-M844 source axes?
```

M857 does not train or promote anything:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Implementation

Added:

```text
src/autodrift/v4_boundary_new_to_m844_bracket_trace.py
tests/test_v4_boundary_new_to_m844_bracket_trace.py
```

The runner selects M854 `boundary_new_to_m844` targets as primary rows and
includes a small recovered existing-boundary control set. For each source-axis
it logs every initial and extended grid replay over:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

Each trace row is classified as:

```text
safe_boundary
safe_wide
negative
ambiguous
```

Each source-axis is then assigned a no-bracket cause such as:

```text
accepted_boundary_found_initial
accepted_boundary_found_extended
bracket_found_initial
bracket_found_extended
all_safe_wide
all_collision_or_negative
mixed_no_adjacent_bracket
ambiguous_or_nonfinite
reconstruction_error
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_boundary_new_to_m844_bracket_trace \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --m854-target-source-rows runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv \
  --m854-rejected-rows runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv \
  --m854-accepted-boundary-rows runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m857_v4_boundary_new_to_m844_bracket_trace \
  --device cpu
```

## Artifacts

```text
runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/target_trace_source_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/source_trace_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/cause_summary.json
runs/m857_v4_boundary_new_to_m844_bracket_trace/candidate_expansion_plan_rows.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/gate_summary.csv
runs/m857_v4_boundary_new_to_m844_bracket_trace/rejected_rows.csv
```

## Result

M857 completed and preserved frozen parameters:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
checkpoint_promoted: false
```

Trace completeness passed:

```text
target_boundary_new_to_m844_sources: 44
control_existing_boundary_sources: 8
reconstructed_snapshot_rows: 52
snapshot_rejection_rows: 0
traced_source_axis_rows: 132
all_traced_source_axis_rows: 156
bracket_trace_rows: 1924
cause_classified_source_axis_share: 1.0
```

Primary boundary-new-to-M844 causes:

```text
all_safe_wide: 114 / 132 = 0.863636
all_collision_or_negative: 18 / 132 = 0.136364
accepted_boundary_found_extended: 0
bracket_found_extended: 0
ambiguous_or_nonfinite: 0
mixed_no_adjacent_bracket: 0
```

Result class:

```text
v4_boundary_new_to_m844_bracket_trace_all_safe_wide
```

## Gate Summary

Passed:

```text
target_boundary_new_to_m844_sources: 44 >= 40
traced_source_axis_rows: 132 >= 100
bracket_trace_rows: 1924 >= 1000
cause_classified_source_axis_share: 1.0 >= 0.95
actor/residual checksums unchanged
pair_delta_sequence_replay_blocked: true
ppo_blocked: true
```

Actionable extended-boundary gate did not pass:

```text
accepted_boundary_found_extended_source_axes: 0 < 12
accepted_boundary_found_extended_source_groups: 0 < 6
accepted_boundary_found_extended_fault_families: 0 < 4
```

## Interpretation

M857 rules out a simple "slightly wider range would open new boundaries" story
for the M854 primary boundary-new-to-M844 rows. The dominant primary cause is:

```text
all_safe_wide
```

That means the current boundary-new-to-M844 sources are generally too far from
the successful non-collision low-margin boundary under the tested grids. A
bounded axis expansion over the same sources is not the best next step.

The smaller all-collision subset is also informative:

```text
all_collision_or_negative: 18 source-axis rows
```

Those may need safer-side bracketing or source-step shifts, but they are not
the majority blocker.

The recovered existing-boundary controls did show expected bracket/accept
signals, which is useful as a sanity check. They cannot satisfy primary M857
claims because controls are not boundary-new-to-M844 sources.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. The boundary-new-to-M844 sources are mostly wide-safe rather
than near-boundary. The next data route should generate or retarget closer
obstacle/source states rather than continue blind axis widening.

### metric_artifact

Secondary risk. Trace and pairability artifacts remain offline diagnostics;
they do not prove learned self-ID.

### not contract_violation

Checksums stayed fixed, no optimizer/PPO ran, and no actor input contract was
changed.

## Tests

Focused tests:

```bash
python -m compileall -q src/autodrift/v4_boundary_new_to_m844_bracket_trace.py tests/test_v4_boundary_new_to_m844_bracket_trace.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_boundary_new_to_m844_bracket_trace.py
```

Result:

```text
5 passed
```

## Decision

Decision:

```text
v4_boundary_new_to_m844_bracket_trace_all_safe_wide
```

Next:

```text
m858-v4-boundary-new-to-m844-bracket-trace-audit
```

M858 should audit the all-safe-wide result before designing closer
obstacle/source generation. Pair-delta replay, objective training, PPO,
promotion, actor mutation, and residual-head mutation remain blocked.
