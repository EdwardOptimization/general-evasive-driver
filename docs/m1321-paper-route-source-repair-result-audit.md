# M1321 Paper-Route Source Repair Result Audit

## Summary

M1321 audits the M1320 `source_repair_v1` smoke and chooses the next source
route.

Decision:

```text
source_repair_result_audit_route_to_updated_corpus_export_with_global_friction_blocker
```

M1320 is strong enough to export as a new source corpus candidate:

```text
accepted_separable_pairs: 216
accepted_fault_family_pairs: 7
source_positive: true
strict thresholds preserved: true
```

But it is not a complete solution because global friction remains inactive:

```text
global_friction_step accepted rows: 0 / 300
```

The next source route should therefore be:

```text
export the M1320 seven-family source corpus candidate;
keep global friction as an explicit blocker;
do not run PPO or source-history objective tuning yet.
```

## Evidence

Primary artifacts:

```text
runs/m1320_inactive_source_family_repair_smoke/summary.json
runs/m1320_inactive_source_family_repair_smoke/family_source_summary.csv
runs/m1320_inactive_source_family_repair_smoke/inactive_fault_families.csv
runs/m1320_inactive_source_family_repair_smoke/accepted_template_summary.csv
docs/m1320-paper-route-inactive-source-family-repair-smoke.md
```

M1320 guardrails held:

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

## Corpus Readiness

M1320 clears the near-term source-repair criteria:

```text
accepted_separable_pairs: 216 >= 160
accepted_fault_family_pairs: 7 >= 6
halfshaft accepted rows: 22 > 4
steering actuator accepted rows: 58
load/CG accepted rows: 6
inactive families exported separately: true
```

Accepted family counts:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

This is broad enough to justify a new source-corpus export. It is still not
broad enough to justify policy training. Export is only the next data-management
step.

## Global Friction Blocker

Global friction remains inactive:

```text
matched_pairs: 300
accepted_pairs: 0
rejected_pairs: 300
best_actions_too_close: 119
best_candidate_not_viable: 181
```

Interpretation:

Uniform friction changes are not a good fit for the current paired open-loop
action separability test. They may need:

- dynamic friction-onset response histories;
- a stopping/envelope source miner rather than same-family action-pair miner;
- a longer corridor task;
- or a later simulator/source-search extension.

This blocker should remain explicit in the exported corpus metadata and in the
next plan builder. Do not merge global friction into split-mu or tire-blowout
labels.

## Route Decision

Reject direct PPO:

```text
source-generation success is not driver performance.
```

Reject direct source-history objective tuning:

```text
the source corpus has not yet been exported, stratified, or planned into
pair-disjoint source-history folds.
```

Admit updated source corpus export:

```text
m1322-paper-route-source-repair-corpus-export
```

M1322 should use the existing source corpus export tool on:

```text
runs/m1320_inactive_source_family_repair_smoke
```

Required outputs:

```text
runs/m1322_source_repair_corpus_export/summary.json
runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv
runs/m1322_source_repair_corpus_export/near_boundary_source_rows.csv
runs/m1322_source_repair_corpus_export/high_regret_source_rows.csv
runs/m1322_source_repair_corpus_export/family_balanced_source_rows.csv
runs/m1322_source_repair_corpus_export/inactive_fault_families.csv
```

M1322 should remain no-policy and source-only.

## Next After Export

If M1322 export is clean, the likely next step is a new corpus expansion plan
against the exported M1322 source corpus:

```text
planned_source_pairs
planned_pair_probe_groups
source_fault_family_count
fold balance
global-friction blocker count
```

Only after that plan is admissible should source-history materialization resume.

## Claim Limits

Allowed claim:

```text
M1320 provides a seven-family strict source-positive corpus candidate with a
separate global-friction blocker.
```

Not allowed:

```text
global friction is solved;
source-history self-identification is proven;
policy performance improved;
PPO is admitted;
checkpoint promotion is admitted;
paper-level source coverage is complete.
```
