# M1263 Paper-Route Richer-Fault Regret-Boundary Retarget Result Audit

## Summary

M1263 audits the M1262 fixed-action obstacle-geometry retarget smoke.

Decision:

```text
regret_boundary_geometry_retarget_negative_route_to_richer_fault_branch_synthesis
```

M1262 is a valid infrastructure pass and a strict source-negative result:

```text
source_reconstruction_reliable: true
strict_accepted_count: 0
result_class: action_divergent_low_regret
```

The audit decision is to stop same-axis geometry retargeting and run a
branch-level synthesis before any further richer-fault source repair.

## Evidence

Primary artifacts:

```text
runs/m1262_richer_fault_regret_boundary_retarget_smoke/summary.json
runs/m1262_richer_fault_regret_boundary_retarget_smoke/retarget_decisions.csv
runs/m1262_richer_fault_regret_boundary_retarget_smoke/retarget_rollouts.csv
```

M1262 reconstructed the source snapshots used by M1259:

```text
pair_id,condition,snapshot_id,seed,fault,step,status
5,A,212,78049,mu_drop_extreme_preexisting,27,matched
5,B,277,78049,brake_fade_extreme_pre_emergency,33,matched
```

Run summary:

```text
selected_target_pairs: 1
selected_pair_ids: [5]
source_reconstructed_snapshot_count: 812
retarget_candidate_count: 441
retarget_rollouts: 1764
strict_accepted_count: 0
accepted_separable_pairs: 0
rejected_retarget_rows: 441
all_four_rollouts_collision_count: 193
own_branch_viability_fail_count: 207
wrong_branch_collision_count: 208
low_regret_count: 441
best_actions_diverged_pairs: 438
result_class: action_divergent_low_regret
```

Guardrails held:

```text
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
```

## Regret Finding

The core result is not that the pair lost action divergence. Action separation
survived almost everywhere:

```text
best_actions_diverged_pairs: 438 / 441
```

The core result is that action divergence did not translate into two-sided
outcome regret:

```text
own-branch viable rows: 234 / 441
min_cross_regret >= 0.004: 298 / 441
min_cross_regret >= 0.005: 0 / 441
min_cross_regret >= 0.020: 0 / 441
max min_cross_regret: 0.0043813964
```

Even near the obstacle boundary, regret stayed around the same low value:

```text
lowest own_min_margin row:
  retarget_id: 238
  own_min_margin: 0.0008728785
  min_cross_regret: 0.0043149038

source row:
  own_min_margin: 0.0337841324
  min_cross_regret: 0.0042178858
```

Interpretation:

```text
The fixed best-A and best-B sequences remain nearly equivalent in outcome under
both hidden branches. Geometry changes difficulty, but does not create a
branch-specific dominance relation for these fixed sequences.
```

## Collision-Dominance Finding

M1262 also showed that part of the geometry grid simply makes the scenario too
hard:

```text
all_four_rollouts_collision_count: 193
own_branch_viability_fail_count: 207
wrong_branch_collision_count: 208
```

This matters because a source-positive row must not be produced by making all
candidate actions fail. M1262 correctly treated these as diagnostic negatives,
not evidence.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
regret_boundary_geometry_retarget_negative
```

More specific process diagnosis:

```text
fixed_action_geometry_retarget_exhausted_for_pair5
```

Not classified as:

```text
metric_artifact
contract_violation
training_instability
proof_washout
private_holdout_contamination
promotion_gate_failure
```

## Branch-Level Context

The richer-fault branch improved source diagnostics compared with the previous
capability-separable branch:

```text
M1259 near_boundary_viability_pairs: 8
M1259 best_actions_diverged_pairs: 4
```

But the branch has not produced strict accepted source rows:

```text
M1259 accepted_separable_pairs: 0
M1262 accepted_separable_pairs: 0
```

M1262 specifically tested the most actionable M1259 row:

```text
pair 5:
  viable: yes
  action-divergent: yes
  low-regret: yes
```

and found that nearby obstacle geometry is not the missing variable.

## Decision

Do not run a larger same-axis geometry grid.

Do not lower `min_cross_regret_margin`.

Do not train.

Do not run PPO.

Do not promote.

Route to a branch synthesis:

```text
m1264-paper-route-richer-fault-capability-source-synthesis
```

The synthesis should decide whether to:

```text
close the current single-track/proxy-fault source branch,
pivot to a high-fidelity/four-wheel fault simulator branch,
or admit one explicitly new evidence variable such as source-step/fault-severity
retargeting or local teacher/optimizer-derived trajectory search.
```

Any next run must have a new evidence variable. It should not be another
geometry-only retargeting run around the same pair.
