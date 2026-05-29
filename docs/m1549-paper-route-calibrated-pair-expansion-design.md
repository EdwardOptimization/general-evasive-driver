# M1549 Paper-Route Calibrated Pair-Expansion Design

## Summary

M1549 designs the first milestone in the new branch:

```text
paper_route_calibrated_pair_expansion
```

Decision:

```text
calibrated_pair_expansion_design_admit_bounded_planner
```

M1547 failed at the pair-construction layer: the calibrated terminal-boundary
sources reran cleanly, but only `2` accepted pairs were formed and both were on
one source-family edge. M1549 therefore does not design another intervention
run. It first designs a pairability-first planner that expands calibrated
terminal-boundary measured pair coverage, then audits that coverage before any
history intervention replay.

No candidate materialization, training corpus export, history intervention,
training, PPO, promotion, private holdout, actor-input change, or level3
self-identification claim is admitted.

## Design Principle

The next implementation must optimize for pairability before intervention
effects.

M1547 selected near-boundary terminal rows first and only then tried to match
pairs. That produced too few pairs. M1550 should instead treat these as joint
objectives:

```text
terminal near-boundary row
+ matched current-state / scene neighbor
+ source-family edge diversity
+ action divergence
+ window-bucket coverage
```

The planner is still no-training and public-only. It may generate and rerun
bounded calibration specs, but it must not export a training corpus or
materialize candidates for policy update.

## Inputs

Allowed inputs:

```text
docs/m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis.md
runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
runs/m1547_calibrated_terminal_boundary_history_intervention_smoke/summary.json
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

The implementation may reuse deterministic source-spec generation from M1544
and measured trace reconstruction from M1547.

Actor inputs must remain P0 human-view/no-privileged:

```text
ego kinematics / IMU-like response;
actuator state;
previous physical commands;
ego-frame road/free-space/obstacle geometry;
online recurrent state from past command-response history.
```

Forbidden actor inputs remain forbidden:

```text
mu, mass, tire stiffness, brake scale, actuator tau;
slip, tire forces, friction margin;
oracle feasibility labels;
AEB/AES/drift-required labels;
controller mode;
speed_ref, beta_target;
path error, heading error, path curvature;
TTC, required clearance, oracle stopping distance;
success/collision/progress labels.
```

## M1550 Planner Scope

M1550 should implement a bounded planner with these caps:

```text
seed: 1843
seed_count: 3
max_base_rows: 24
max_calibration_specs: 240
max_pair_candidates: 256
```

The implementation should write:

```text
runs/m1550_calibrated_pair_expansion_planner_smoke/source_spec_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/measured_trace_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/measured_snapshot_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/pair_candidate_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/pair_family_summary.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/guardrail_summary.csv
runs/m1550_calibrated_pair_expansion_planner_smoke/summary.json
```

It must not write intervention rows.

## Pairability Score

Each pair candidate should be scored before acceptance:

```text
scene_distance
ego_current_distance
anchor_window_distance
first_action_l2
terminal_margin_gap
source_family_edge
window_bucket_pair
```

Acceptance should prefer:

```text
low scene/current-state distance;
same or adjacent decision/post-decision/terminal windows;
first_action_l2 >= 0.035;
terminal_margin_gap >= 0.015 where available;
source-family edges that reduce concentration;
both same-window and cross-window buckets, as long as replay remains aligned.
```

The pair score can be a deterministic ranking rather than a learned model:

```text
score =
  + action_divergence_bonus
  + terminal_margin_gap_bonus
  + source_edge_diversity_bonus
  + window_bucket_diversity_bonus
  - scene_distance_penalty
  - ego_current_distance_penalty
  - edge_concentration_penalty
```

M1550 should report raw candidates and accepted candidates separately. A
candidate that fails one threshold can still be useful for audit, but it must
not enter accepted-pair gates.

## Source Expansion Knobs

M1550 may expand around M1544 accepted rows with bounded retargeting:

```text
obstacle x / y small offsets;
obstacle half-width / half-length small offsets;
initial speed and yaw-rate small offsets;
road curvature / boundary offset small offsets;
friction and actuator-delay hidden-profile variants only as simulator hidden
  conditions, never actor inputs;
decision-anchor and post-decision-anchor timing variants.
```

The key change from M1547 is that source generation should ask:

```text
will this row have at least one plausible matched neighbor?
```

not only:

```text
is this row near a terminal margin window?
```

## Public Gates

M1550 passes the planner smoke only if:

```text
measured_snapshot_count >= 24
pair_candidate_count >= 16
accepted_pair_count >= 8
accepted_source_family_edge_count >= 5
max_single_pair_source_edge_share <= 0.4
accepted_terminal_family_count >= 4
accepted_window_bucket_count >= 2
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_started == false
ppo_used == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
level3_self_id_claim_made == false
```

Evidence-quality targets:

```text
accepted_pair_count >= 12
accepted_source_family_edge_count >= 6
max_single_pair_source_edge_share <= 0.3
decision_window_pair_count >= 3
post_decision_or_terminal_pair_count >= 3
```

The evidence-quality targets are not promotion criteria; they decide whether
the branch should admit an intervention design after the M1550 audit.

## Follow-Up Logic

If M1550 pair gates pass:

```text
M1551 audits the pair-expanded planner result.
M1552 may design calibrated pair-expanded interventions.
```

If M1550 pair gates fail:

```text
M1551 audits scenario_sampling_failure.
No intervention design is admitted.
The branch either retunes task generation once or pivots to broader terminal
task generation.
```

If M1550 accidentally runs interventions or materializes candidates:

```text
classify as contract_violation;
do not use the artifact for research evidence.
```

## Failure Taxonomy

Use only process-v2 labels in manifests:

```text
scenario_sampling_failure
metric_artifact
contract_violation
none
```

Record narrower explanations in prose:

```text
pair bottleneck;
source edge concentration;
window-bucket concentration;
near-boundary/source mismatch;
action-divergence weak;
guardrail violation.
```

## Next

```text
m1550-paper-route-calibrated-pair-expansion-planner-implementation
```
