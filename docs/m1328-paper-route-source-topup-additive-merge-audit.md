# M1328 Paper-Route Source Top-Up Additive Merge Audit

## Summary

M1328 audits whether M1327 should be used as additive source top-up over M1322.

Decision:

```text
source_topup_additive_merge_audit_admit_merge_export_design
```

M1327 should not replace M1322, but it is useful additive source material.
The correct next step is to design a merge/export tool that combines source rows
with a source-run-prefixed identity and then reruns the corpus expansion plan.

Do not materialize source histories yet. Do not run policy objectives, PPO, or
promotion.

## Inputs

M1322 source-repair corpus export:

```text
runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv
accepted rows: 216
```

M1327 horizon-corrected top-up smoke:

```text
runs/m1327_source_repair_topup_horizon_corrected_smoke/accepted_separable_pairs.csv
accepted rows: 150
```

## Family Comparison

M1322:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

M1327:

```text
single_wheel_brake_pull: 52
load_cg_perturbation: 48
steering_actuator_fault: 38
tire_blowout_like: 8
left_right_split_mu: 2
single_wheel_grip_collapse: 2
```

M1327 contributes exactly where M1322 is thinnest:

```text
load_cg_perturbation: 6 -> 54 naive additive
single_wheel_brake_pull: 10 -> 62 naive additive
tire_blowout_like: 23 -> 31 naive additive
```

It does not help:

```text
halfshaft_torque_loss: stays 22
global_friction_step: stays 0
```

## Merge Identity Audit

Do not merge by raw `pair_id`. Pair ids are local to each source run and can
collide across runs.

Minimum safe merge identity:

```text
source_run_id
source_row_id
```

For M1322:

```text
source_run_id = m1322_source_repair_corpus_export
source_row_id = pair_id from all_accepted_source_rows.csv
```

For M1327:

```text
source_run_id = m1327_source_repair_topup_horizon_corrected_smoke
source_row_id = pair_id from accepted_separable_pairs.csv
```

This source-run-prefixed identity gives:

```text
candidate input rows: 216 + 150 = 366
```

This is still a merge-preview count, not a final exported corpus claim. M1329
must write concrete artifacts and include a semantic-duplicate audit.

## Dedupe Risk

A too-coarse semantic key can falsely collapse different source rows. For
example, omitting `scenario_id` or `seed` can merge different rows that share
fault names, obstacle geometry, and templates. That is not acceptable for the
source corpus.

M1329 should therefore report two counts:

```text
source_identity_rows:
  source_run_id + source_row_id

semantic_duplicate_groups:
  exact scenario/fault/template/action/outcome duplicates for diagnostics only
```

Semantic duplicate groups should be used for diagnostics, not to silently remove
rows before the export decision.

## Expected Merged Coverage

Naive source-run-prefixed family counts before export-tool filtering:

```text
single_wheel_grip_collapse: 64
steering_actuator_fault: 96
left_right_split_mu: 37
tire_blowout_like: 31
halfshaft_torque_loss: 22
single_wheel_brake_pull: 62
load_cg_perturbation: 54
```

Expected advantages:

```text
total candidate rows exceed the 240 target;
source family count remains 7;
load/CG, brake, and blowout-like undercoverage improve materially;
fold planner has more room to balance source families than M1323.
```

Remaining blockers:

```text
halfshaft remains below the 30-family target;
global friction remains absent;
merge/export artifacts do not yet exist;
source-history materialization has not rerun on the merged corpus.
```

## Decision

Admit one merge/export design:

```text
m1329-paper-route-source-topup-additive-merge-export-design
```

M1329 should define a tool that writes:

```text
runs/m1330_source_topup_additive_merge_export/summary.json
runs/m1330_source_topup_additive_merge_export/all_accepted_source_rows.csv
runs/m1330_source_topup_additive_merge_export/source_run_summary.csv
runs/m1330_source_topup_additive_merge_export/family_source_summary.csv
runs/m1330_source_topup_additive_merge_export/semantic_duplicate_groups.csv
runs/m1330_source_topup_additive_merge_export/inactive_or_undercovered_families.csv
```

After export, run the corpus expansion planner again. Only that plan can decide
whether materialization is admitted.

## Supported Claims

Supported:

```text
M1327 is useful additive top-up evidence for the M1322 source corpus.
```

Supported:

```text
A source-run-prefixed merge should likely exceed the 240 candidate-row target
before final export filtering.
```

## Falsified Claims

Falsified:

```text
M1327 alone is a better standalone corpus than M1322.
```

Falsified:

```text
halfshaft or global friction top-up is solved by M1327.
```

Still unsupported:

```text
merged corpus is exported;
source-history materialization is admitted;
PPO or promotion is admitted;
closed-loop self-identification is proven.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

M1327 helps some families but remains skewed and leaves halfshaft/global
friction unresolved.

Secondary risk:

```text
metric_artifact
```

Merge counts are sensitive to identity choice. The next tool must make row
identity explicit.

## Guardrails

Guardrails held:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Next Step

Admit:

```text
m1329-paper-route-source-topup-additive-merge-export-design
```

Scope:

```text
design merge/export artifacts and identity rules;
do not export yet unless the next manifest admits implementation;
do not materialize histories;
do not train;
do not run PPO;
do not promote.
```
