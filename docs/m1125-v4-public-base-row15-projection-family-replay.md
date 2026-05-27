# M1125 V4 Public Base Row15 Projection Family Replay

## Purpose

M1125 runs the M1061 family-intersection public gate for the M1123 alpha `0.15`
candidate.

This milestone runs only family-intersection replay. It does not train actor
weights, run PPO, run full public gate, run fresh/OOD, run behavior gates,
promote, use private holdout, or change actor inputs.

## Candidate

```text
candidate_label: alpha_0_15
candidate_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Parent evidence:

```text
M1123 row15 unsafe-margin gate: pass
M1123 six-surface first replay: pass
```

## Result

M1125 passes:

```text
result_class: family_intersection_public_gate_pass
overall_pass: true
replay_gate_count: 3
replay_gates_passed: 3
failed_replay_gates: []
actor_inputs_changed: false
failure_types: none
```

Per-source replay:

```text
short61049 -> alpha_0_15:
  rows: 25
  baseline success drops: 25
  candidate success drops: 25
  normal_success_delta: 0.0
  normal_margin_mean_delta: 0.000224903
  margin_gap_mean_delta: -0.000055626
  gate_pass: true

short61050 -> alpha_0_15:
  rows: 27
  baseline success drops: 27
  candidate success drops: 27
  normal_success_delta: 0.0
  normal_margin_mean_delta: -0.000092834
  margin_gap_mean_delta: -0.000041571
  gate_pass: true

short61051 -> alpha_0_15:
  rows: 27
  baseline success drops: 27
  candidate success drops: 27
  normal_success_delta: 0.0
  normal_margin_mean_delta: -0.000080212
  margin_gap_mean_delta: -0.000036309
  gate_pass: true
```

## Artifacts

```text
runs/m1125_row15_projection_family_replay/summary.json
runs/m1125_row15_projection_family_replay/replay_gate_summary.csv
runs/m1125_row15_projection_family_replay/diagnostic_summary.csv
runs/m1125_row15_projection_family_replay/replay_gates/short61049_to_alpha_0_15
runs/m1125_row15_projection_family_replay/replay_gates/short61050_to_alpha_0_15
runs/m1125_row15_projection_family_replay/replay_gates/short61051_to_alpha_0_15
```

## Interpretation

Alpha `0.15` now passes:

```text
1. exact M1107 no-training projection gate;
2. row15 unsafe-margin gate;
3. target-base six-surface first replay;
4. M1061 family-intersection public gate.
```

This is meaningful proof-retention progress, but still not a promotion. The
candidate has not passed the expanded full public gate, source-diverse
diagnostics beyond M1120/M1123, fresh/OOD, behavior gates, private holdout, or
PPO continuation.

## Decision

```text
row15_projection_family_replay_pass_route_to_full_public_gate_design
```

Next milestone:

```text
m1126-v4-public-base-row15-projection-full-public-gate-design
```
