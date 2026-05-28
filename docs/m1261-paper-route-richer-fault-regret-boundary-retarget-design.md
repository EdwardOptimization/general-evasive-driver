# M1261 Paper-Route Richer-Fault Regret-Boundary Retarget Design

## Summary

M1261 designs one bounded source repair after M1260 audited M1259 as strict
source-negative but identified pair 5 as a viable action-divergent low-regret
target.

Decision:

```text
regret_boundary_retarget_design_admit_bounded_implementation_smoke
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, threshold relaxation, self-identification claim,
paper-level claim, or high-fidelity physical fault claim occurs in M1261.

## Target Row

M1259 pair 5:

```text
seed: 78049
fault_family_pair: global_mu_drop->brake_authority_drop
condition_A_fault: mu_drop_extreme_preexisting
condition_B_fault: brake_fade_extreme_pre_emergency
best_action_l2: 0.7001441121
margin_A_best_A: 0.0799886482
margin_A_best_B: 0.0747198233
margin_B_best_B: 0.0337841324
margin_B_best_A: 0.0295662466
cross_regret_A: 0.0052688249
cross_regret_B: 0.0042178858
rejection_reason: insufficient_cross_regret
```

This row has:

```text
own-branch viability: yes
action divergence: yes
two-sided cross regret: too small
```

The next repair should therefore target regret, not viability.

## Design Principle

Earlier relocation stages mostly targeted:

```text
own-branch margin / viability
```

M1262 should instead target:

```text
two-sided cross-regret amplification while preserving own-branch viability
```

Strict acceptance remains unchanged:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

`asymmetric_success_drop` remains diagnostic only.

## Proposed Tool

Implement:

```text
src/autodrift/capability_separable_regret_retarget.py
tests/test_capability_separable_regret_retarget.py
```

Inputs:

```text
--source-run-dir runs/m1259_richer_fault_capability_source_smoke
--checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
--config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
--target-pair-id 5
```

The tool should reconstruct source snapshots deterministically from the config,
seed, faults, and snapshot ids recorded in M1259. If direct reconstruction is
too fragile, M1262 should stop with a compatibility report rather than
fabricating state.

## Candidate Selection

Select rows from `matched_capability_pairs.csv` where:

```text
accepted == false
best_A_success == true
best_B_success == true
best_action_l2 >= 0.12
0.0 < min(cross_regret_A, cross_regret_B) < 0.02
rejection_reason == insufficient_cross_regret
```

Default first target:

```text
pair_id: 5
```

M1262 may allow:

```text
--max-target-pairs 4
```

but should keep the first smoke focused on the top low-regret/action-divergent
rows.

## Retarget Axes

Generate deterministic public scenario perturbations around the row's relocated
obstacle geometry:

```text
body_x_delta:
  -1.00, -0.50, -0.25, 0.00, 0.25, 0.50, 1.00

body_y_delta:
  -0.30, -0.15, -0.075, 0.00, 0.075, 0.15, 0.30

half_width_delta:
  -0.08, -0.04, -0.02, -0.01, 0.00, 0.01, 0.02, 0.04, 0.08
```

Bounds:

```text
relocated_obstacle_body_x > 0.5
relocated_obstacle_half_width >= 0.1
```

M1262 should start with obstacle geometry only. Fault-severity retargeting can
be designed later if geometry retargeting cannot move regret without collapsing
viability.

## Evaluation

For each retargeted geometry:

1. Relocate both condition snapshots to the same candidate geometry.
2. Evaluate the pair's fixed best-A sequence in condition A and condition B.
3. Evaluate the pair's fixed best-B sequence in condition A and condition B.
4. Compute:

```text
margin_A_best_A
margin_A_best_B
margin_B_best_B
margin_B_best_A
cross_regret_A
cross_regret_B
best_A_success
best_B_success
A_using_B_success
B_using_A_success
symmetric_margin_accept
asymmetric_success_drop
```

The first smoke should not rerun a broad trajectory-proposal search. It should
answer a narrower question:

```text
Can the already-discovered branch-specific action pair become strictly
source-positive under a nearby public scenario boundary?
```

If fixed-action retargeting works, a later milestone may add local proposal
refinement.

## Anti-Collision-Dominance Checks

A retarget row is invalid for strict source-positive evidence if:

```text
best_A_success == false
best_B_success == false
margin_A_best_A < 0.0
margin_B_best_B < 0.0
```

The summary should also report:

```text
all_four_rollouts_collision_count
own_branch_viability_fail_count
wrong_branch_collision_count
low_regret_count
strict_accepted_count
```

This prevents declaring success by simply making all candidate actions fail.

## M1262 Bounded Smoke

M1262 should implement the tool and run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_separable_regret_retarget \
  --source-run-dir runs/m1259_richer_fault_capability_source_smoke \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --target-pair-id 5 \
  --max-target-pairs 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1262_richer_fault_regret_boundary_retarget_smoke
```

Expected artifacts:

```text
summary.json
target_pairs.csv
retarget_candidates.csv
retarget_rollouts.csv
accepted_regret_retarget_rows.csv
rejected_regret_retarget_rows.csv
model_fidelity_limits.md
```

Runtime bounds:

```text
max_target_pairs: 1
geometry candidates: at most 7 * 7 * 9 = 441 before dedup/bounds
rollouts per geometry: 4
max_continuation_steps: 18
```

If this is too slow, reduce geometry candidates first. Do not reduce accepted
source thresholds.

## Decision

Admit:

```text
m1262-paper-route-richer-fault-regret-boundary-retarget-implementation
```

The next milestone may include implementation plus a bounded no-training smoke.
It must not train or promote a checkpoint.
