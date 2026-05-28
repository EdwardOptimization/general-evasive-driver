# M1324 Paper-Route Source Repair Corpus Plan Result Audit

## Summary

M1324 synthesizes the M1314-M1323 source-history corpus expansion branch.

Decision:

```text
source_repair_corpus_plan_synthesis_promote_to_topup_generation_branch
```

The branch made a real source-coverage improvement:

```text
M1315 planned source pairs: 108
M1323 planned source pairs: 216

M1315 planned pair-probe groups: 216
M1323 planned pair-probe groups: 432

M1315 source families: 3
M1323 source families: 7

M1315 max source-family fold share: 0.5789473684
M1323 max source-family fold share: 0.3260869565
```

But M1323 still misses the original M1314 pair-count target and leaves global
friction absent:

```text
planned_source_pairs: 216 / 240
planned_pair_probe_groups: 432 / 480
global_friction_step: 0 / 30
```

Do not materialize source histories yet. Close the expansion-planning branch and
open a bounded targeted top-up source-generation branch.

## Evidence Summary

M1314 set the expansion targets:

```text
planned_source_pairs >= 240
planned_pair_probe_groups >= 480
source_fault_family_count >= 6
pair_disjoint_folds: true
max_source_family_fold_share <= 0.40
pair_specific_weight_used: false
```

M1315 showed that old artifacts were insufficient:

```text
planned_source_pairs: 108
planned_pair_probe_groups: 216
source_fault_family_count: 3
max_source_family_fold_share: 0.5789473684
unsupported_or_undercovered_family_count: 7
```

M1317 added new source-generation profiles and produced partial coverage:

```text
accepted_separable_pairs: 128
accepted_fault_family_pairs: 5
```

M1320 repaired inactive families enough to create a new corpus candidate:

```text
accepted_separable_pairs: 216
accepted_fault_family_pairs: 7
global_friction_step accepted rows: 0 / 300
```

M1322 exported the source-repair corpus:

```text
exported_accepted_rows: 216
near_boundary_rows: 39
high_regret_rows: 154
family_balanced_rows: 121
```

M1323 planned the exported corpus into folds without stale materialized-history
matches:

```text
planned_source_pairs: 216
planned_pair_probe_groups: 432
source_fault_family_count: 7
corner_or_side_variant_count: 22
materialized_source_pair_count: 0
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share: 0.3260869565
pair_specific_weight_used: false
```

## Supported Claims

Supported:

```text
The source-history corpus expansion branch fixed the largest diversity and fold
balance defects from M1315.
```

Supported:

```text
M1322/M1323 provide a clean seven-family source corpus plan with pair-disjoint
folds and no stale M1280 materialized-history reuse.
```

Supported:

```text
The next work should be source-data construction, not another policy objective
run on the old narrow source-history corpus.
```

## Falsified Claims

Falsified:

```text
The M1323 corpus fully meets the M1314 240-pair / 480-group target.
```

Falsified:

```text
Uniform global friction is represented by the current same-family action-pair
source miner.
```

Falsified:

```text
The source-repair corpus can be materialized immediately without auditing
coverage gaps.
```

Still unsupported:

```text
policy performance improved;
PPO is admitted;
checkpoint promotion is admitted;
closed-loop self-identification is proven;
the source corpus is paper-complete.
```

## Failure Taxonomy Summary

Primary failure type:

```text
scenario_sampling_failure
```

Reason:

```text
The remaining gaps are family and source-construction coverage gaps, not
optimizer failures or actor-input problems.
```

Secondary risk:

```text
objective_overfit
```

Reason:

```text
If we materialize and tune on the 216-row seven-family corpus now, the next
policy-side objective could overfit active families while global friction and
undercovered source families remain weak.
```

No evidence of:

```text
contract_violation
private_holdout_contamination
training_instability
promotion_gate_failure
```

## Public Gate Overfit Risk

Risk level:

```text
medium
```

M1323 is much less concentrated than M1315, but the corpus is still generated
from public construction rules and still under target in four active families:

```text
halfshaft_torque_loss: 22 / 30
load_cg_perturbation: 6 / 30
single_wheel_brake_pull: 10 / 30
tire_blowout_like: 23 / 30
```

Global friction is not merely underweighted; it is absent:

```text
global_friction_step: 0 / 30
```

The next branch must therefore improve source coverage before source-history
materialization or policy-side objective tuning.

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_source_history_corpus_expansion
```

Opened branch:

```text
paper_route_source_repair_topup_generation
```

Next milestone:

```text
m1325-paper-route-source-repair-topup-generation-design
```

M1325 should design a bounded top-up source-generation pass for:

```text
halfshaft_torque_loss
load_cg_perturbation
single_wheel_brake_pull
tire_blowout_like
```

Global friction remains an explicit blocker. It can be probed in M1325 only as a
separate diagnostic source path; it must not be merged into split-mu,
tire-blowout-like, or other labels to fake coverage.

## Guardrails

M1324 performed no policy-side work:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

Allowed claim:

```text
M1324 closes the corpus expansion branch and opens targeted source top-up
generation.
```

Not allowed:

```text
driver performance improved;
closed-loop self-identification is proven;
the corpus is ready for PPO;
the corpus is ready for checkpoint promotion;
global friction is solved.
```
