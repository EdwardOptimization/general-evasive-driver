# M1337 Paper-Route Materialized Source-History Objective Corpus Export Audit

## Summary

M1337 audits the M1336 active/quarantine export before any objective evaluator,
objective update, PPO, or promotion.

Decision:

```text
materialized_source_history_objective_corpus_export_audit_pass_route_to_evaluator_design
```

The export is admissible as a no-policy substrate for the next design step.

## Evidence

Primary source:

```text
runs/m1336_materialized_source_history_objective_corpus_export/summary.json
```

Active corpus counts:

```text
active_source_pair_rows: 344
active_history_prefix_rows: 1376
active_history_frame_rows: 33024
active_history_intervention_rows: 1376
active_wrong_history_pair_rows: 1376
active_source_family_count: 6
active_zero_response_l2_prefix_count: 0
active_response_l2_ge_0_01_count: 1376
active_max_source_family_fold_share: 0.2985074627
```

Quarantine counts:

```text
quarantine_source_pair_rows: 22
quarantine_history_prefix_rows: 88
quarantine_history_frame_rows: 2112
quarantine_history_intervention_rows: 88
quarantine_wrong_history_pair_rows: 88
quarantine_family_rows: 2
```

Identity:

```text
source_identity_duplicate_count: 0
source_identity_metadata_preserved: true
```

Guardrails:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
labels_enter_actor_input: false
```

## Active Semantics

The active corpus contains only history-distinguishable non-halfshaft source
pairs. Every active prefix has nonzero response evidence above the M1336
threshold:

```text
active_response_l2_ge_0_01_count: 1376 / 1376
active_zero_response_l2_prefix_count: 0
```

This means the next evaluator can treat active rows as command-response history
rows with a measurable correct-history versus wrong-history difference. It does
not mean the current actor uses those histories correctly.

## Family And Fold Balance

Active source-family counts:

```text
left_right_split_mu: 37
load_cg_perturbation: 54
single_wheel_brake_pull: 62
single_wheel_grip_collapse: 64
steering_actuator_fault: 96
tire_blowout_like: 31
```

Active fold balance:

```text
fold 0: 71 pairs, 6 families, top share 0.2253521127
fold 1: 70 pairs, 6 families, top share 0.2857142857
fold 2: 68 pairs, 6 families, top share 0.2941176471
fold 3: 68 pairs, 6 families, top share 0.2941176471
fold 4: 67 pairs, 6 families, top share 0.2985074627
```

The active corpus is source-diverse enough for evaluator design. The fold
balance is below the `0.40` cap, so no source-cap repair is needed before the
no-update evaluator design.

## Quarantine Semantics

Quarantine family rows:

```text
halfshaft_torque_loss->halfshaft_torque_loss:
  quarantine_reason: halfshaft_probe_silent
  source_pair_rows: 22

global_friction_step->global_friction_step:
  quarantine_reason: global_friction_missing
  source_pair_rows: 0
```

Halfshaft is correctly excluded from the active corpus because current
brake/lift histories do not excite drive-side torque-loss differences. Global
friction is correctly kept as a missing-family diagnostic instead of being
fabricated into active evidence.

## Supported Claims

Supported:

```text
M1336 exports a clean active materialized source-history objective corpus and
explicit quarantine artifacts.
```

Supported:

```text
The active export can advance to no-update source-history objective evaluator
design.
```

Still unsupported:

```text
policy objective improvement;
actor update;
PPO continuation;
promotion;
halfshaft self-identification;
global friction coverage;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```

## Failure Taxonomy

Failure type:

```text
none
```

Retained blockers:

```text
halfshaft_probe_silent
global_friction_missing
```

These are source-coverage limitations, not software failures in the M1336
export.

## Public Gate Risk

Risk:

```text
medium
```

The active corpus is public and has already shaped the branch. It is appropriate
for objective evaluator design and public proof work, but it is not private
paper-level generalization evidence.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not modify actor inputs.

Admit one design milestone:

```text
m1338-paper-route-materialized-source-history-objective-evaluator-design
```

M1338 should design a no-update full-corpus evaluator over the M1336 active
rows. It should measure correct-history versus wrong-history action-likelihood
and action-distance residuals without mutating checkpoint weights.
