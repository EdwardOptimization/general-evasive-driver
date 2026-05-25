# M832 V4 Near-Boundary Wrong-History Pair Mining Implementation

## Purpose

M832 implements the no-training near-boundary wrong-history pair-mining route
admitted by M831.

The experiment question is:

```text
If matched different-fault pairs are mined after boundary bracketing, does
wrong-cross-fault hidden injection create stronger action or margin degradation
than the wide-margin M828 pair set?
```

M832 is implementation/data-route only:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_near_boundary_wrong_history_pair_mining.py
```

New tests:

```text
tests/test_v4_near_boundary_wrong_history_pair_mining.py
```

The implementation reuses:

```text
M814 boundary bracketing helpers
M828 wrong-cross-fault hidden replay semantics
M825 source rows and candidate plans
```

The route:

1. reconstructs M825 source snapshots;
2. brackets each source over obstacle lateral, timing, and half-width axes;
3. accepts finite non-collision boundary rows with margin `<= 0.05`;
4. pairs only after boundary search, requiring different fault families and
   action divergence;
5. replays normal/reset/zero/shift/delay/wrong-hidden variants;
6. keeps zero-command evidence separate from wrong-history evidence;
7. writes source, boundary, pair, replay, accepted, rejected, diversity, gate,
   and summary artifacts.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_near_boundary_wrong_history_pair_mining \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m832_v4_near_boundary_wrong_history_pair_mining \
  --device cpu
```

## Result

Run directory:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining
```

Summary:

```text
result_class: v4_near_boundary_wrong_history_pair_mining_pair_sparse
source_requests: 64
reconstructed_snapshot_rows: 64
boundary_replay_rows: 94
accepted_boundary_rows: 39
near_boundary_pair_rows: 60
wrong_history_replay_rows: 420
accepted_primary_wrong_history_rows: 0
accepted_mitigation_rows: 0
zero_command_accepted_like_rows: 0
```

Checksums stayed unchanged:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

## Boundary Evidence

M832 fixed the M828 boundary-slack problem for source rows:

```text
accepted_boundary_rows: 39
boundary_margin_min:    0.000049393596228464176
boundary_margin_median: 0.00995198136524511
boundary_margin_threshold: 0.05
strict_margin_threshold:   0.02
```

Boundary diversity:

```text
unique_seed_count:        4
unique_source_group_count: 20
unique_fault_family_pair_count: 7
unique_warmup_mode_count: 4
unique_boundary_axis_count: 3
max_boundary_axis_dominance: 0.512821
```

This is an important improvement over M828's pair set, where normal margins
were all `>= 0.217669`.

## Pair Evidence

The near-boundary pair set remained sparse:

```text
near_boundary_pair_rows: 60
min_pair_rows: 80
unique_fault_family_pair_count: 13
unique_left_seed_count: 4
unique_right_seed_count: 4
unique_warmup_pair_count: 4
unique_onset_pair_count: 9
```

Main pair rejections:

```text
obstacle_distance_too_large: 389
action_gap_too_small:       177
same_fault_family:          115
```

The pair source is therefore not broad enough to pass the pre-registered pair
gate.

## Wrong-History Evidence

All variants replayed successfully:

```text
normal:                  60
reset_hidden_each_step:  60
reset_hidden_then_normal:60
zero_command_obs:        60
command_shift_obs:       60
response_delay_obs:      60
wrong_cross_fault_hidden:60
```

Wrong-hidden effects remain too small:

```text
wrong gap min:    -0.000018269493832656636
wrong gap median: -0.000006635818858624631
wrong gap max:     0.000036904085711997325
wrong gap mean:   -0.0000007583329090824857

wrong action min:    0.0034050077858099404
wrong action median: 0.004996883584620381
wrong action max:    0.006654849690777518
wrong action mean:   0.0052446763925260926
```

The action threshold remains:

```text
action_l2_threshold: 0.014
```

So M832 does not support primary wrong-history proof.

## Interpretation

M832 supports:

- the implementation can reconstruct M825 source snapshots;
- boundary-first mining can create genuinely near-boundary current states;
- the route writes complete no-training artifacts;
- actor and M761 residual-head contracts remain clean.

M832 does not support:

- source-diverse accepted wrong-history rows;
- hidden-only wrong-history outcome degradation;
- PPO admission;
- checkpoint promotion;
- threshold relaxation.

The key scientific update is:

```text
Boundary slack was real and is partly fixed, but hidden-only wrong-history
injection is still too weak on the current M568/M761 source family.
```

## Failure Taxonomy

### scenario_sampling_failure

Primary label. Boundary rows exist, but near-boundary matched pairs are below
the `80` row gate and only span `4` left/right seeds.

### metric_artifact

Near-boundary pair construction and action divergence are useful diagnostics,
but accepted wrong-history rows remain zero.

### not contract_violation

Checksums are unchanged and no training, PPO, or promotion occurred.

## Decision

Decision:

```text
v4_near_boundary_wrong_history_pair_mining_pair_sparse
```

Next:

```text
m833-v4-near-boundary-wrong-history-pair-mining-audit
```

M833 should audit whether the next control variable is broader boundary/source
coverage, full wrong-history observation replay, or pivoting away from
hidden-only injection. PPO and promotion remain blocked.
