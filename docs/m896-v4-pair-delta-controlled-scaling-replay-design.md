# M896 V4 Pair-Delta Controlled Scaling Replay Design

## Purpose

M896 designs the exact-first replay/proof gate for larger existing
objective-only candidates identified by M895.

Candidates:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

Baseline:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M896 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Why Raw Candidates

M895 found that accepted alpha `0.1` is proof-safe but too small:

```text
alpha_0.1 action_l2_mean_all: ~0.00012
alpha_0.1 behavior_success_delta: 0.0
alpha_0.1 behavior_clearance_delta: ~+0.00049
```

The raw candidates are about `10x` larger:

```text
raw action_l2_mean_all: ~0.00120
```

They also improve exact objective and exact holdout metrics, but M885/M886/M891
did not allow direct raw-candidate acceptance. Therefore raw candidates must be
treated as controlled scaling probes, not accepted checkpoints.

## M897 Gate Order

M897 should execute the gate in this order.

### 1. Exact Objective Recheck

Run exact no-update recheck for both raw candidates:

```text
runs/m897_m886_raw_exact_recheck
runs/m897_m891_raw_exact_recheck
```

Pass conditions:

```text
tensor_rows_reconstructed: 247 / 247
missing_tensor_count: 0
exact_losses_finite: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
actor_parameters_changed: false
```

If either exact recheck fails, stop and route to objective artifact audit.

### 2. First Replay Gates

Before running all six surfaces, run the historically sensitive first gates:

```text
M183/M170
M267/M264
```

For each candidate:

```text
baseline_policy: m568_base
candidate_policy: m886_raw or m891_raw
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

If either candidate fails either first gate, stop and route to scaling boundary
search. Do not fallback to PPO.

### 3. Full Replay Stack

If first gates pass, run all six public replay/proof surfaces for both raw
candidates:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Use the same thresholds as M889/M893.

### 4. Behavior Seeds

If the full replay stack passes, run behavior retention for seeds:

```text
9505
9506
```

Policies:

```text
m568_base
m886_raw
m886_raw_zero_all
m891_raw
m891_raw_zero_all
heuristic
random
```

Behavior pass condition:

```text
raw candidate success_rate >= m568_base success_rate
raw candidate termination_rate <= m568_base termination_rate
```

Clearance and return are diagnostic unless success/termination regress.

## Failure Routing

```text
exact recheck failure
  -> objective artifact audit

first replay failure
  -> controlled scaling boundary search design

full replay failure
  -> proof-washout audit

behavior regression after replay pass
  -> behavior-retention audit

full pass for both raw candidates
  -> effect-size continuation audit before any PPO or promotion
```

## Decision

Decision:

```text
controlled_scaling_replay_design_admit_m897
```

Next:

```text
m897-v4-pair-delta-raw-candidate-controlled-scaling-gate
```

M897 may execute exact recheck and replay/proof gates for the two raw
candidates. It must not run PPO, train, change actor inputs, mutate the
residual head, or promote a checkpoint.
