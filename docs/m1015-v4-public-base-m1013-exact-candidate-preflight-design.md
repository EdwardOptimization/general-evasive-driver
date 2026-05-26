# M1015 V4 Public Base M1013 Exact-Candidate Preflight Design

## Purpose

M1015 designs a minimal replay-calibrated trust audit for M1013.

This is design-only. It does not train, run PPO, run the full public replay
stack, use private holdout, change actor inputs, or promote a checkpoint.

## Why This Audit Is Needed

M1013 found:

```text
exact temporal candidates: 10
exact + M1011 branch-trust candidates: 0
```

M1014 classified this as:

```text
proof_washout / exact_branch_active_set_conflict
```

Before changing thresholds or designing a new scalar objective, we need to know
whether M1011 branch trust is too conservative or correctly predicts M267/M264
preflight failure.

## Candidate Set

M1016 should materialize these exact-but-branch-unsafe candidates from the M1013
raw actor_mean checkpoints by interpolation from M974 base.

Candidate A:

```text
name: m1013_lam0001_a020
raw checkpoint:
  runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_001/raw_actor_mean_update.pt
alpha: 0.2
reason: lowest branch loss among exact candidates
total improvement: 0.001338
branch trust loss: 1.325315
row 6 contribution: 0.467241
row 15 contribution: 0.721845
```

Candidate B:

```text
name: m1013_lam0030_a050
raw checkpoint:
  runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_03/raw_actor_mean_update.pt
alpha: 0.5
reason: best exact candidate from strongest branch-trust coefficient
total improvement: 0.001894
branch trust loss: 6.986220
row 6 contribution: 2.774867
row 15 contribution: 3.847220
```

Candidate C:

```text
name: m1013_lam0001_a050
raw checkpoint:
  runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_001/raw_actor_mean_update.pt
alpha: 0.5
reason: stronger temporal improvement on the same low-lambda direction
total improvement: 0.003304
branch trust loss: 8.282467
row 6 contribution: 2.918419
row 15 contribution: 4.512955
```

Reference rows:

```text
M974 base:
  expected M267/M264 success-drop count: 17/17

M1002 alpha 0.01:
  known M267/M264 success-drop count: 15/17
  lost rows: 6, 15
  use existing M1004 artifact as reference, not as a new pass/fail gate
```

## Materialization Contract

M1016 must:

```text
1. Load M974 base checkpoint.
2. Load each M1013 raw actor_mean checkpoint.
3. Interpolate only actor_mean tensors.
4. Save candidate checkpoints.
5. Verify non-actor checksum equals M974 base.
6. Verify actor input config equals M974 base.
```

No training or optimizer should start.

## Preflight Scope

Run only M267/M264 boundary outcome replay:

```text
corpus:
  runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv

max_continuation_steps: 60
env_config: configs/m121_human_view_zero_obstacle_relvel.json
```

Do not run:

```text
six public replay surfaces
behavior seeds
fresh/OOD eval
private holdout
promotion audit
PPO
```

## Preflight Metrics

For each candidate, record:

```text
success_drop_count
failed_success_drop_rows
normal_success_delta
normal_margin_mean_delta
margin_gap_mean_delta
row 6 normal/wrong margins
row 15 normal/wrong margins
row 16 normal/wrong margins
gate_pass
```

Use the M1003 preflight criteria:

```text
success_drop_count == 17
max_success_drop_count_regression == 0
max_normal_success_drop == 0.0
max_normal_margin_regression <= 0.005
max_margin_gap_regression <= 0.001
```

## Decision Rule

If Candidate A fails rows `6` or `15`:

```text
M1011 branch trust is likely necessary.
Route to projection/line-search repair design or branch synthesis before any
trainable-surface widening.
```

If Candidate A passes M267/M264:

```text
M1011 strict threshold is too conservative.
Route to replay-calibrated trust threshold redesign, using Candidate A as the
upper bound for acceptable branch trust.
```

If Candidate A fails but B or C passes:

```text
The trust metric ordering is not aligned with replay outcome.
Route to metric-artifact audit before any threshold change.
```

If all fail:

```text
Do not run full public replay. Route to projection/line-search or synthesis.
```

## Decision

```text
m1013_exact_candidate_preflight_design_admit_m1016_implementation
```

Next:

```text
m1016-v4-public-base-m1013-exact-candidate-preflight
```
