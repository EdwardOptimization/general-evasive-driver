# M2373 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Implementation Design

- status: completed
- decision: `bounded_repair_implementation_design_route_to_outcome_localization_branch_synthesis`
- manifest: `experiments/manifests/m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design.json`
- parent audit: `docs/m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit.md`
- audited spec summary: `runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json`
- reset/rollout/measured execution in M2373: `false`
- policy action executed in M2373: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair claims: `false`

## Design Goal

M2373 turns the audited M2371 repair specs into a bounded implementation route.
It does not execute the route. The next implementation, after branch synthesis,
should materialize repair-plan artifacts from these spec surfaces:

```text
repair_spec_rows.csv
ordinary_offtrack_repair_spec_rows.csv
mixed_guarded_repair_spec_rows.csv
collision_guardrail_spec_rows.csv
r4_guardrail_spec_rows.csv
diagnostic_guardrail_spec_rows.csv
claim_boundary.csv
```

## Source Surfaces

Accepted M2371 source counts:

```text
repair_spec_row_count: 320
ordinary offtrack specs: 36
mixed guarded offtrack specs: 18
collision guardrail specs: 28
R4 mitigation semantics guardrail specs: 48
diagnostic no-ranking guardrail specs: 190
```

Ordinary offtrack and mixed guarded axes:

```text
ordinary:
  hidden_dynamics_bucket: 3
  obstacle_longitudinal_timing_bucket: 1
  role_family: 3
  role_family+hidden_dynamics_bucket: 9
  role_family+obstacle_lateral_offset_bucket: 8
  role_family+obstacle_longitudinal_timing_bucket: 7
  sampled_obstacle_label: 2
  scenario_family_id: 3

mixed guarded:
  hidden_dynamics_bucket: 1
  obstacle_lateral_offset_bucket: 2
  role_family: 1
  role_family+hidden_dynamics_bucket: 6
  role_family+obstacle_lateral_offset_bucket: 2
  role_family+obstacle_longitudinal_timing_bucket: 4
  sampled_obstacle_label: 1
  scenario_family_id: 1
```

This supports a spec-driven implementation route, not a profile-specific route.
The design must operate over repair families and source axes, not over a
controller winner or config pack winner.

## Implementation Surfaces

The bounded materializer should produce artifacts only. It should not edit the
active training config, run training, run reset, or run rollout.

Required output families:

```text
repair_implementation_plan.json:
  top-level manifest of source spec counts, allowed levers, blocked levers,
  guardrail constraints, and claim boundary.

reward_delta_rows.csv:
  candidate offtrack_margin_reward, recovery_window_reward, and
  boundary_overshoot_penalty deltas by repair_family and source_slice_axis.

curriculum_weight_rows.csv:
  candidate sampling weights by repair_spec_id, source_slice_axis,
  priority_tier, and guardrail state.

guardrail_constraint_rows.csv:
  collision, R4, and diagnostic constraints that every later repair candidate
  must preserve.

mixed_guarded_constraint_rows.csv:
  guarded offtrack targets with collision_rate_not_worse constraints attached.

claim_boundary.csv:
  no ranking, no winner, no paper-level claim, no finite-window-vs-GRU
  conclusion, no level3 self-ID, no scenario-redesign-executed claim, and no
  training-repair-success claim.
```

## Lever Policy

Allowed lever names remain implementation-design artifacts only:

```text
offtrack_margin_reward:
  strengthen road-boundary margin sensitivity for ordinary offtrack specs.

recovery_window_reward:
  reward recovery back into the bounded corridor after near-limit maneuvers.

boundary_overshoot_penalty:
  penalize offtrack overshoot severity, not just terminal offtrack events.

curriculum_sampling_weight:
  increase sampling weight for source-axis target categories without
  selecting a profile or pack winner.

collision_guardrail_weight:
  enforce not-worse collision behavior for mixed and collision-only specs.

r4_mitigation_metric_guard:
  keep unavoidable mitigation semantics separate from ordinary avoidance.
```

Blocked levers remain:

```text
actor_input_change
hidden_oracle_feature_injection
profile_specific_tuning
support_policy_ranking
controller_family_ranking
winner_selection
active_scenario_config_overwrite
r4_ordinary_avoidance_repair
collision_blind_offtrack_objective
scenario_redesign_executed_claim
training_repair_success_claim
```

## Guardrail Policy

The implementation route should be lexicographic:

```text
1. preserve actor input contract and no-oracle boundary;
2. preserve collision guardrails on mixed and collision-only specs;
3. preserve R4 mitigation semantics as guardrail-only;
4. preserve diagnostic/profile/pack/global rows as no-ranking guardrails;
5. materialize ordinary offtrack repair deltas only after guardrail rows exist;
6. keep active config overwrite, training, replay, and PPO blocked.
```

Mixed guarded specs are admissible only if their output rows include:

```text
collision_guardrail_required: true
guardrail_metric: collision_rate_not_worse
collision_guardrail_weight: present
collision_blind_offtrack_objective: blocked
```

R4 specs are admissible only if:

```text
r4_mitigation_semantics_guardrail: true
r4_ordinary_avoidance_repair: blocked
target_metric: not offtrack_rate_down as an ordinary repair target
```

Diagnostic specs are admissible only if:

```text
diagnostic_no_ranking_guardrail: true
ranking_admissible: false
winner_selected: false
```

## Future Materializer Pass Gates

A later implementation materializer should pass only if:

```text
input_repair_spec_row_count == 320
ordinary_offtrack_source_count == 36
mixed_guarded_source_count == 18
collision_guardrail_source_count == 28
r4_guardrail_source_count == 48
diagnostic_guardrail_source_count == 190
reward_delta_row_count > 0
curriculum_weight_row_count > 0
guardrail_constraint_row_count >= 266
profile_specific_tuning_count == 0
actor_input_change_count == 0
hidden_oracle_feature_injection_count == 0
collision_blind_mixed_repair_count == 0
r4_ordinary_repair_count == 0
ranking_admissible_count == 0
winner_selected_count == 0
active_config_overwritten == false
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
training_started == false
replay_started == false
ppo_used == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
guardrail_violation_count == 0
```

The `guardrail_constraint_row_count >= 266` threshold covers the non-negotiable
collision, R4, and diagnostic guardrail families:

```text
28 collision + 48 R4 + 190 diagnostic = 266 hard-minimum rows
28 collision + 48 R4 + 190 diagnostic + 18 mixed guarded = 284 expected rows
```

The lower bound leaves room for implementation to collapse duplicate
constraints, but not to drop guardrail families. Mixed guarded constraints
should appear explicitly unless the materializer can prove they are already
represented by an equivalent collision guardrail row.

## Synthesis Decision

M2373 admits a bounded implementation route, but it should not route directly
to another narrow materializer. The current outcome-localization branch has
accumulated a long sequence of design, materialization, and audit milestones
from M2364 through M2373. Before producing a new implementation artifact, the
harness should synthesize the branch.

Next milestone:

```text
m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis
```

M2374 should answer whether the M2364-M2373 branch:

```text
1. meaningfully advanced task-quality evidence;
2. reduced or increased workflow/local-search risk;
3. should continue to artifact-only repair-plan materialization;
4. should pivot to scenario/task-quality synthesis, complexity pruning, or
   measured validation planning;
5. still blocks ranking, paper, finite-window-vs-GRU, and self-ID claims.
```

## Claim Boundary

M2373 may claim only:

```text
A bounded offtrack guardrail repair implementation route has been designed
from audited repair-spec artifacts.
```

Still blocked:

```text
repair execution
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
```

## Next

Pre-registered follow-up:

```text
m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis
```
