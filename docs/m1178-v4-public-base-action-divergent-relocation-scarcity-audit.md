# M1178 V4 Public Base Action-Divergent Relocation Scarcity Audit

## Purpose

M1178 audits why M1177 failed after source budget and bounded relocation replay
both ran successfully.

This milestone audits existing artifacts only. It does not run relocation
replay, run mining, train actor weights, run PPO, promote, use private holdout,
convert rows into a proof corpus, or change actor inputs.

## Inputs

```text
runs/m1177_action_divergent_bounded_relocation_seed117700/summary.json
runs/m1177_action_divergent_bounded_relocation_seed117700/boundary_relocation_rows.csv
runs/m1177_action_divergent_bounded_relocation_seed117700/balanced_accepted_wrong_history_rows.csv
runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv
runs/m1169_row15_promoted_target_microgrid_seed116100/balanced_accepted_wrong_history_rows.csv
```

## Question 1: Is M1177 The Old Active Set?

Yes.

M1169 accepted rows:

```text
rows: 6
physical_pairs:
  116117:36:116124:15
  116117:39:116124:15
left_steps: 36, 39
target: future_yaw_response
checkpoints: row15_current
```

M1177 balanced accepted rows:

```text
rows: 38
physical_pairs:
  116117:36:116124:15
  116117:39:116124:15
left_steps: 36, 39
target: future_yaw_response
checkpoints:
  previous_m1078_base
  row15_current
  row15_previous_alpha015
  short61050
  short61051
```

M1177 increased accepted row count and checkpoint coverage, but it did not add
a new physical-pair active set.

## Question 2: Did Candidate Scoring Predict New Materializable Pairs?

No.

M1175 selected:

```text
candidate physical pairs: 17
selected rows: 240
```

M1177 accepted pairs:

```text
accepted physical pairs: 2
candidate rows on accepted pairs: 30
candidate rows on non-accepted pairs: 210
```

Accepted-pair candidates:

```text
action_divergent_score_mean: 2.897256
margin_gap_mean: 0.005393
first_action_distance_mean: 0.205752
trajectory_distance_mean: 0.301917
targets: future_yaw_response only
```

Non-accepted-pair candidates:

```text
action_divergent_score_mean: 2.221285
action_divergent_score_max: 5.719664
margin_gap_mean: 0.009402
margin_gap_max: 0.043220
first_action_distance_mean: 0.186313
trajectory_distance_mean: 0.121557
targets:
  future_yaw_response
  future_lateral_accel_response
  future_braking_deceleration
```

The accepted pairs have strong trajectory-action divergence, but non-accepted
pairs include higher score and larger margin-gap candidates. Therefore the
M1175 score is useful for finding action-divergent candidates, but not enough
to predict source-diverse relocation materialization.

## Question 3: Is Source Geometry A Limiting Artifact?

Yes for artifact-only expansion.

M1175 `candidate_outcomes.csv` only contains these obstacle-related fields:

```text
obstacle_completed
min_obstacle_clearance
obstacle_collision_radius
source_obstacle_bucket
```

`source_obstacle_bucket` is:

```text
x=nan|y=nan
```

for all selected rows. The existing outcome artifact cannot source-balance or
score candidates by original obstacle geometry. M1177 relocation rows later
materialize source/relocated obstacle geometry, but by then the candidate
selection step has already been made.

This does not invalidate M1177; it limits what artifact-only replay can prove.

## Classification

M1177 failure mechanism:

```text
old_active_set_dominance: true
candidate_scoring_insufficient_for_materialization: true
source_geometry_deficiency_for_artifact_only_selection: true
source_budget_failure: false
runtime_failure: false
actor_contract_violation: false
```

Harness failure type:

```text
scenario_sampling_failure
```

## Supported Claims

```text
M1175/M1177 action-divergent filtering increases accepted row count on the old active set.
M1177 does not produce a source-diverse wrong-history proof surface.
Existing M1161/M1175 artifact-only expansion is not enough for broad wrong-history materialization.
```

## Falsified Claims

```text
M1175 action-divergent candidate export alone is sufficient to break the two-pair collapse.
High action-divergent score alone predicts relocation-materializable source-diverse wrong-history rows.
The current artifact-only path can continue by simply rerunning bounded relocation with the same inputs.
```

## Decision

Stop the current narrow artifact-only action-divergent relocation path and route
to branch synthesis.

The next synthesis should decide whether to pivot to richer source artifact
generation / new scenario mining that records source obstacle geometry and
covers more extreme hidden dynamics, rather than continuing to rescore the
same M1161 outcome table.

## Guardrail

No relocation replay, mining, actor training, PPO, promotion, private holdout,
row conversion, threshold weakening, or actor-input change occurred.

## Next

```text
decision: action_divergent_relocation_scarcity_audit_route_to_branch_synthesis
next: m1179-v4-public-base-stronger-wrong-history-construction-synthesis
```
