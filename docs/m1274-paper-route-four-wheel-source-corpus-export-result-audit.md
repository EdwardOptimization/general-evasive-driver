# M1274 Paper-Route Four-Wheel Source Corpus Export Result Audit

## Summary

M1274 audits the M1273 stratified four-wheel source corpus export.

Decision:

```text
four_wheel_source_corpus_export_audit_route_to_branch_synthesis
```

M1273 exported a valid source corpus:

```text
all accepted rows: 108
near-boundary rows: 19
high-regret rows: 32
family-balanced rows: 63
inactive fault families: 1
```

The corpus is suitable as source material, but not ready for actor/Gym
integration without a branch-level synthesis. The `paper_route_fidelity_fault_source_design`
branch has reached its 10-milestone synthesis cadence from M1265 through M1274.
Therefore the next milestone must synthesize the branch before any new narrow
experiment.

## Evidence

Primary artifacts:

```text
runs/m1273_four_wheel_source_corpus_export/summary.json
runs/m1273_four_wheel_source_corpus_export/all_accepted_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/near_boundary_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/high_regret_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/family_balanced_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/inactive_fault_families.csv
```

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Subset Suitability

All accepted rows:

```text
rows: 108
families:
  left_right_split_mu: 28
  single_wheel_brake_pull: 59
  single_wheel_grip_collapse: 21
```

Use:

```text
source-positive evidence and broad source inventory.
```

Do not use directly as a proof corpus because the full set is margin-easy on
average.

Near-boundary rows:

```text
rows: 19
threshold: min_own_margin <= 0.20
families:
  left_right_split_mu: 7
  single_wheel_brake_pull: 2
  single_wheel_grip_collapse: 10
```

Use:

```text
best immediate material for boundary retargeting or outcome-intervention design.
```

Risk:

```text
small but not empty; brake-pull boundary coverage is thin.
```

High-regret rows:

```text
rows: 32
threshold: min_cross_regret >= 0.05
families:
  left_right_split_mu: 11
  single_wheel_grip_collapse: 21
```

Use:

```text
best material for action-divergence and wrong-action counterfactuals.
```

Risk:

```text
brake-pull is absent from high-regret rows, so use high-regret as a focused
subset rather than the only corpus.
```

Family-balanced rows:

```text
rows: 63
cap: 21 per accepted family
families:
  left_right_split_mu: 21
  single_wheel_brake_pull: 21
  single_wheel_grip_collapse: 21
```

Use:

```text
source-diverse audit/evaluation material after boundary/high-regret logic is
defined.
```

Inactive fault families:

```text
halfshaft_torque_loss->halfshaft_torque_loss
```

Use:

```text
do not include in the accepted corpus for the current brake-dominant lattice;
revisit only under a throttle-on or drive-torque source phase.
```

## Decision Logic

The corpus is not source-collapsed:

```text
three accepted fault-family pairs;
near-boundary rows span all accepted families;
family-balanced rows can equalize accepted families.
```

The corpus is not enough for driver claims:

```text
source rows are open-loop no-policy artifacts;
no actor hidden state is involved;
no Gym integration occurred;
no closed-loop driver performance is measured.
```

The next narrow technical step would likely be:

```text
source-to-intervention or boundary-retarget design using near-boundary and
high-regret subsets.
```

But the branch synthesis cadence is now active:

```text
M1265..M1274 = 10 milestones in paper_route_fidelity_fault_source_design
```

So M1274 routes to synthesis first.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Admit one branch synthesis:

```text
m1275-paper-route-fidelity-fault-source-synthesis
```

M1275 must answer:

```text
what M1265-M1274 proved;
what remains unproved;
whether the branch should continue, stop, pivot, or promote to a next branch;
whether the next branch should be source-to-intervention/materialization;
which corpus subset should be the first material if it continues.
```
