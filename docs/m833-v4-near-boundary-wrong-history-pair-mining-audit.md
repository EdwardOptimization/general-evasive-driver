# M833 V4 Near-Boundary Wrong-History Pair Mining Audit

## Purpose

M833 audits the M832 near-boundary wrong-history pair-mining result before any
new implementation.

The audit question is:

```text
Did M832 fail because boundary-aware pair mining is still too sparse, or
because hidden-only wrong-history injection is the wrong control variable?
```

M833 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/summary.json
runs/m832_v4_near_boundary_wrong_history_pair_mining/diversity_summary.json
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/wrong_history_replay_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/gate_summary.csv
docs/m832-v4-near-boundary-wrong-history-pair-mining-implementation.md
```

M832 result class:

```text
v4_near_boundary_wrong_history_pair_mining_pair_sparse
```

## Artifact Consistency

M832 produced complete no-training artifacts:

```text
source_requests: 64
reconstructed_snapshot_rows: 64
boundary_replay_rows: 94
accepted_boundary_rows: 39
near_boundary_pair_rows: 60
wrong_history_replay_rows: 420
```

All replay variants are present for all selected pairs:

```text
normal: 60
reset_hidden_each_step: 60
reset_hidden_then_normal: 60
zero_command_obs: 60
command_shift_obs: 60
response_delay_obs: 60
wrong_cross_fault_hidden: 60
```

This is not a runtime failure.

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

M832 preserved the P0 actor-input contract. Fault labels were used only as
source-selection and logging metadata.

## Boundary Audit

M832 materially improves the boundary state relative to M828.

M828 pair margins:

```text
normal margin min: 0.21766916668222658
normal margin <=0.05: 0 / 108
```

M832 accepted boundary margins:

```text
accepted_boundary_rows: 39
boundary_margin_min:    0.000049393596228464176
boundary_margin_median: 0.00995198136524511
boundary_margin_threshold: 0.05
strict_margin_threshold:   0.02
```

Boundary diversity is not perfect but is nontrivial:

```text
unique_seed_count: 4
unique_source_group_count: 20
unique_fault_family_pair_count: 7
unique_warmup_mode_count: 4
unique_boundary_axis_count: 3
max_source_group_dominance: 0.076923
max_boundary_axis_dominance: 0.512821
```

Conclusion:

```text
M832 solved the specific "all pairs are wide-margin" problem.
```

## Pair Audit

The near-boundary pair set is still below the pre-registered gate:

```text
near_boundary_pair_rows: 60
min_pair_rows: 80
```

Pair diversity:

```text
unique_fault_family_pair_count: 13
unique_left_seed_count: 4
unique_right_seed_count: 4
unique_warmup_pair_count: 4
unique_onset_pair_count: 9
max_left_seed_dominance: 0.566667
max_right_seed_dominance: 0.400000
```

Main pair rejections:

```text
obstacle_distance_too_large: 389
action_gap_too_small:       177
same_fault_family:          115
```

So pair coverage is not strong enough for a source-diverse corpus claim.

## Hidden-Only Wrong-History Audit

The important negative finding is that near-boundary margins did not amplify
hidden-only wrong-history sensitivity enough.

Wrong-hidden first-action drift:

```text
min:    0.0034050077858099404
median: 0.004996883584620381
max:    0.006654849690777518
mean:   0.0052446763925260926
threshold: 0.014
```

Wrong-hidden margin gaps:

```text
min:    -0.000018269493832656636
median: -0.000006635818858624631
max:     0.000036904085711997325
mean:   -0.0000007583329090824857
threshold: 0.01
```

Accepted rows:

```text
accepted_primary_wrong_history_rows: 0
accepted_mitigation_rows: 0
zero_command_accepted_like_rows: 0
```

The hidden-only result is not merely a sample-size issue. Even on the 60
near-boundary pairs, the wrong-hidden action and margin effects are far below
threshold.

## Failure Taxonomy

### scenario_sampling_failure

Still present. The pair corpus has only `60` rows against the `80` row gate and
is seed-concentrated.

### metric_artifact

Boundary rows and near-boundary pairs are useful diagnostics, but they do not
prove wrong-history self-identification because accepted wrong-history rows are
zero.

### not contract_violation

No training or forbidden actor input occurred.

## Supported Claims

M832 supports:

- boundary-first mining can fix the wide-margin problem;
- current artifacts can reconstruct and replay near-boundary pairs;
- hidden-only wrong-history injection remains weak on the M568/M761 family;
- this branch is still not ready for PPO or promotion.

## Unsupported Claims

M832 does not support:

- source-diverse wrong-history proof;
- outcome-level hidden-history dependence;
- threshold relaxation;
- more hidden-only pair mining as the first next step;
- driver promotion.

## Decision

The next control variable should not be "more of the same hidden-only pair
mining" as the immediate step.

The sharper diagnostic is to test whether the actor depends primarily on the
explicit current response/action stream rather than the recurrent hidden alone:

```text
wrong_cross_fault_hidden_only      # M832 baseline
wrong_cross_fault_response_only    # right response/action stream + left hidden
wrong_cross_fault_response_hidden  # right response/action stream + right hidden
wrong_action_history_only          # right previous commands only
wrong_ego_response_only            # right ego response only
```

This keeps the actor input contract unchanged because these are offline
counterfactual interventions on deployable observation fields, not new inputs.

Decision:

```text
admit_full_wrong_history_response_intervention_design
```

Next:

```text
m834-v4-full-wrong-history-response-intervention-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and threshold relaxation remain blocked.
