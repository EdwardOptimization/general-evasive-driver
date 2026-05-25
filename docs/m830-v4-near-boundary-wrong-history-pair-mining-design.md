# M830 V4 Near-Boundary Wrong-History Pair Mining Design

## Purpose

M830 designs the next no-training pair-mining route after M828/M829 showed that
the first wrong-cross-fault hidden injection was implemented correctly but
evaluated on pairs that were too far from terminal boundary.

The design question is:

```text
Can we mine matched different-fault pairs that are simultaneously visible-state
matched, action-divergent, and near normal-history terminal boundary, so that
wrong-history injection has a fair chance to create outcome-level evidence?
```

M830 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## M829 Diagnosis

M828 reconstructed wrong-history pairs cleanly:

```text
selected_pair_rows: 108
reconstructed_pairs: 108
wrong_history_replay_rows: 756
actor_backbone_changed: false
residual_head_changed: false
```

The blocker was not implementation or contract failure. The blocker was pair
boundary slack:

```text
normal margin min:    0.21766916668222658
normal margin median: 1.0287735657138812
normal margin <=0.05: 0 / 108
```

Wrong hidden state moved actions in the expected direction:

```text
wrong_history_closer_to_right_action: 108 / 108
max first-action L2: 0.006900976889874039
max margin gap:      0.00002602146853414311
```

but the effect was too small on wide-margin pairs. M830 therefore must not
relax wrong-history thresholds or call wide-margin action divergence proof. It
must change the data source.

## Design Summary

M831/M832 should not pair first and then hope the pair is near boundary.

The intended implementation order is:

```text
1. generate or reconstruct source snapshots with hidden-dynamics diversity;
2. bracket each source snapshot to near-boundary normal-history outcome;
3. only then match different-fault snapshots by visible ego/scene distance;
4. retain only pairs where both sides are near boundary under their own normal
   history and the preferred first/prefix actions differ;
5. run wrong-cross-fault hidden replay on that boundary-aware pair corpus.
```

This changes the active variable from:

```text
matched action-divergent pair
```

to:

```text
near-boundary matched action-divergent pair
```

The route remains no-training and uses the frozen M568 actor and M761 residual
head as behavior generators.

## Required Inputs

The implementation should start from current artifacts:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv
runs/m828_v4_wrong_cross_fault_history_intervention/wrong_history_replay_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

If those artifacts cannot provide enough boundary coverage, the implementation
may regenerate source snapshots with the same frozen checkpoint/residual head
and the same scenario config. It must log regenerated rows as new source data,
not overwrite M825.

## Boundary Mining Procedure

For each eligible source snapshot, M832 should run deterministic boundary
search over axes that preserve the current-model/proxy-fault boundary:

```text
obstacle_lateral_offset
obstacle_longitudinal_distance / timing
obstacle_half_width
fault_activation_step neighborhood
source_step neighborhood
fault_severity neighborhood when parameterized and available
```

The primary accepted boundary row should satisfy:

```text
normal_success == true
normal_collision == false
0.0 <= normal_margin <= 0.05
```

The strict near-boundary band for primary proof candidates should be:

```text
0.0 <= normal_margin <= 0.02
```

The ultra-strict diagnostic band should be:

```text
0.0 <= normal_margin <= 0.005
```

Rows outside `0.05` may be retained only as diagnostics and must not count as
primary wrong-history proof.

## Pair Matching

Boundary rows should be paired only after boundary search. Each pair must use
different hidden-dynamics families:

```text
left_fault_family != right_fault_family
```

and must satisfy visible matching constraints:

```text
ego_response_distance <= 0.25
obstacle_geometry_distance <= 0.05
same or compatible warm-up mode unless explicitly tagged cross_warmup
source-step distance <= implementation horizon tolerance
both sides finite non-collision normal margin
```

Action divergence should be measured before wrong-history replay:

```text
first_action_l2 >= 0.014
or prefix_l2_mean >= 0.010
```

Action divergence alone is diagnostic. It becomes proof-relevant only if
wrong-history replay creates margin or success degradation.

## Pair Ranking

Candidate pairs should be ranked lexicographically:

```text
1. both sides inside the strict near-boundary band;
2. lower max(left_normal_margin, right_normal_margin);
3. larger first_action_l2 or prefix_l2_mean;
4. lower visible ego/context distance;
5. source/fault/warm-up/onset diversity contribution;
6. lower dominance risk for already-selected source groups.
```

The implementation should keep rejected pair rows with explicit reasons:

```text
not_near_boundary
same_fault_family
visible_distance_too_large
obstacle_distance_too_large
action_gap_too_small
normal_collision
source_balance_limit
future_only_fidelity
missing_snapshot
replay_error
```

## Wrong-History Replay Gate

The follow-up replay should reuse the M828 intervention semantics:

```text
env = left near-boundary relocated env
obs_t = left current observation
hidden_t = right recurrent hidden
rollout continues in left env
```

Required variants:

```text
normal
wrong_cross_fault_hidden
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
command_shift_obs
response_delay_obs
```

The wrong-history evidence must remain separate from zero-command evidence. A
row where only zero-command succeeds as an ablation is not a wrong-history row.

Primary wrong-history accepted rows require:

```text
normal_success == true
normal_collision == false
wrong_history_closer_to_right_action == true
wrong_first_action_l2_vs_normal >= 0.014
wrong_margin_gap_from_normal >= 0.01
or success_drop_from_normal == true
normal_margin <= 0.05
```

Mitigation rows may be retained separately if both histories fail but wrong
history materially worsens finite margin:

```text
normal_collision == true
wrong_collision == true
wrong_margin_gap_from_normal >= 0.02
```

Mitigation rows do not count as primary self-identification proof.

## Diversity Gates

M832 should pass only if the primary wrong-history set is not a singleton:

```text
accepted_primary_wrong_history_rows >= 80
unique_left_seeds >= 8
unique_source_groups >= 24
unique_fault_family_pairs >= 6
unique_warmup_modes >= 2
unique_onset_buckets >= 3
max_seed_share <= 0.25
max_source_group_share <= 0.15
max_fault_pair_share <= 0.35
```

If the route produces fewer than `80` rows but at least `20` rows with good
diversity, it should be classified as a sparse positive diagnostic, not as a
promotion or PPO admission.

## Required Artifacts

The implementation should write:

```text
boundary_source_rows.csv
boundary_replay_rows.csv
near_boundary_pair_rows.csv
wrong_history_replay_rows.csv
accepted_primary_wrong_history_rows.csv
accepted_mitigation_rows.csv
rejected_boundary_rows.csv
rejected_pair_rows.csv
diversity_summary.json
gate_summary.csv
summary.json
```

Every summary must include:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

## Failure Taxonomy

Expected classifications:

```text
scenario_sampling_failure:
  no source-diverse near-boundary matched pairs are found

metric_artifact:
  action divergence exists but margin/success degradation does not

objective_overfit:
  boundary rows are found only by one public geometry axis or one source group

contract_violation:
  any actor input includes hidden fault labels or oracle feasibility
```

## Workflow Decision

M830 admits the design, but not immediate implementation under the same branch.
The branch has reached the post-M820 cadence boundary:

```text
M821-M830 are ten non-synthesis milestones after M820.
```

Therefore the next milestone should be a process synthesis:

```text
m831-v4-low-margin-new-data-route-second-branch-synthesis
```

That synthesis should decide whether to:

```text
continue into M832 near-boundary wrong-history pair-mining implementation;
pivot to a new branch name for near-boundary wrong-history mining;
or stop this low-margin route if the accumulated evidence is too narrow.
```

PPO, actor training, residual-head training, learned gating, checkpoint
promotion, and threshold relaxation remain blocked.

## Decision

Decision:

```text
near_boundary_wrong_history_pair_mining_design_ready_synthesis_required
```

Next:

```text
m831-v4-low-margin-new-data-route-second-branch-synthesis
```
