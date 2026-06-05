# M2789 Engineering Controller Route A Source-Only Belief-Stress Fresh-Holdout Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_guardrailed_multi_objective_belief_stress_training_design`
- manifest: `experiments/manifests/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis.json`
- synthesis artifact: `docs/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis.md`
- parent audit: `docs/m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit.md`
- parent fresh-holdout panel: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json`
- prior branch synthesis: `docs/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design.json`
- next: `m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design`

## Evidence Summary

M2786-M2788 completed a source-only Route A fresh-holdout belief-stress branch:

```text
M2786 synthesis:
  decision: pivot_to_route_a_source_only_belief_stress_fresh_holdout_delta_panel
  accepted M2778-M2785 as complete claim-safe source-only belief-stress evidence
  preserved M2782 candidate checkpoint lineage
  rejected ranking, promotion, validation, performance, paper, high-fidelity,
  full-driver, and self-ID interpretation

M2787 fresh-holdout panel:
  status_pass: true
  required_artifacts_present: true
  gate_matrix_pass: true
  failed_gate_ids: []
  seed_start_index: 4
  seed_count: 4
  fresh_holdout_seed_indices: [4, 5, 6, 7]
  m2784_seed_indices: [0, 1, 2, 3]
  fresh_holdout_seed_indices_disjoint_from_m2784: true
  horizon_steps: 120
  m2784_horizon_steps: 80
  curriculum_row_count: 18
  paired_execution_rows: 144
  paired_delta_rows: 72
  proof_gates: 13
  generalization_holdout_gates: 8
  promotion_guards: 4
  actor_guards: 7
  mitigation_guards: 8
  claim_rows: 11
  gate_rows: 25

M2788 audit:
  accepted M2787 completeness and claim safety
  rejected direct interpretation
  routed to branch synthesis before another same-axis panel or training update
```

Checkpoint lineage remains:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
candidate_checkpoint_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
```

M2787 fresh-holdout deltas:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  mean: 0.00035927758389157286
  median: 0.0012294839614694908
  min: -0.0037394441382763155
  max: 0.005563442547770414
  positive rows: 43
  negative rows: 29

candidate_minus_source_minimum_road_margin_m:
  mean: 0.003045548777864837
  median: 0.003106116556409022
  min: 0.0017406585947428166
  max: 0.004875049267406784
  positive rows: 72
  negative rows: 0

candidate_minus_source_final_speed_mps:
  mean: 0.0026159244394306303
  median: 0.0033156956468582965
  min: -0.004601285240803277
  max: 0.005643853462414361
  positive rows: 63
  negative rows: 9

candidate_minus_source_max_abs_yaw_rate:
  mean: -0.00017877287320032365
  median: -0.00024961173037246764
  min: -0.0010484951493790473
  max: 0.0017912210375098936
  positive rows: 7
  negative rows: 60
  zero rows: 5

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72

mean_action_delta_l1:
  mean: 0.000330366297728483
  positive rows: 72
```

The branch changed the evidence state because it moved from same-seed M2784
diagnostics to a disjoint fresh-holdout seed surface with a longer horizon. The
road-margin and yaw-rate directions persisted. However, obstacle-clearance
deltas remain mixed and the action movement is tiny, so this branch is not
promotion, ranking, validation, driver-performance, or self-ID evidence.

## Supported Claims

M2789 supports these bounded claims:

```text
M2786-M2788 form a complete claim-safe source-only belief-stress fresh-holdout
diagnostic branch.

M2787 produced fresh closed-loop paired source-vs-candidate diagnostic rows
outside the M2784 seed surface while preserving actor 72/action 3 and no
hidden/oracle actor input.

The M2782 candidate shows persistent source-only road-margin and yaw-rate
directional movement on M2787 holdout seeds.

The same M2787 evidence also shows mixed obstacle-clearance effects and tiny
action deltas, so the branch cannot support promotion or performance claims.

The branch is strong enough to justify designing a guarded multi-objective
training/update recipe that explicitly protects obstacle clearance while trying
to preserve road-margin/yaw-rate gains.
```

These claims support a next-route decision only. They do not support repair
success, driver performance, validation readiness, validation result, ranking,
winner selection, checkpoint promotion, success-rate verdict, paper evidence,
finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation,
full ideal driver completion, or level3 self-identification.

## Falsified Claims

The following claims are rejected or not admitted:

```text
M2787 proves the candidate is better than the source: false
M2787 admits checkpoint ranking: false
M2787 admits winner selection: false
M2787 admits checkpoint promotion: false
M2787 admits validation readiness: false
M2787 proves repair success: false
M2787 proves driver performance: false
M2787 proves paper-level evidence: false
M2787 proves finite-window-vs-GRU evidence: false
M2787 proves current-sim or high-fidelity validation: false
M2787 proves level3 self-identification: false
M2787 completes the full ideal driver gate: false
another same-axis fresh-holdout panel is the right immediate next action: false
```

The branch also rejects a wording shortcut: persistent road-margin/yaw-rate
deltas cannot be promoted into a result while obstacle clearance remains mixed
and no validation/promotion gate was run.

## Failure Taxonomy Summary

Controlled failures and risks:

```text
contract_violation:
  controlled. The branch preserves P0 observation 72, action 3, no hidden/oracle
  actor input, and no actor-visible labels.

lineage_invalid:
  controlled. Source and candidate checkpoint hashes are recorded and distinct.

scenario_sampling_failure:
  controlled for this branch. M2787 uses seed indices 4-7 disjoint from M2784
  0-3 and covers all ordinary role, dynamics, and stress buckets.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators.

objective_overfit:
  reduced but not eliminated. Fresh holdout rows reduce same-seed overfit risk,
  but the branch would overfit if road-margin-only positives drove promotion.
```

Active failures and risks:

```text
behavior_regression:
  active. Obstacle-clearance deltas are mixed with 29 negative rows.

metric_artifact:
  active. The action deltas are small and source-only.

local_search:
  active if the next milestone is another same-axis diagnostic or audit rather
  than a new training objective, broader evidence axis, or stop.

high_fidelity_dependency:
  active. The branch does not address Route C high-fidelity dependency.

self_id_gap:
  active. The branch does not run controller-family history necessity tests and
  cannot establish level3 self-identification.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is medium if the next action:

```text
repeats M2787 with another adjacent seed block and no new training objective
uses road-margin-only positives as a promotion criterion
ignores 29 negative obstacle-clearance rows
treats tiny source-only action deltas as driver-quality evidence
continues process-only docs without a new evidence-producing branch
```

Risk is reduced by the next route only if it:

```text
defines obstacle-clearance regression guards explicitly
uses multi-objective guardrails rather than single-metric road-margin tuning
keeps proof, generalization, behavior-retention, and promotion guards separate
keeps actor inputs unchanged and labels actor-invisible
registers a future fresh closed-loop training/evaluation preflight before any
promotion or ranking
```

## Next Branch Decision

Decision:

```text
pivot_to_guardrailed_multi_objective_belief_stress_training_design
```

M2789 pivots from source-only fresh-holdout delta interpretation to a bounded
design for a stronger, guardrailed training/update recipe:

```text
next milestone:
  m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design

next evidence axis:
  source_only_belief_stress_guardrailed_multi_objective_training_design

required design constraints:
  preserve actor P0 observation 72 and action 3
  expose no hidden/oracle actor features or evaluator labels to actor input
  make obstacle-clearance regression a first-class guard, not a post-hoc note
  retain road-margin/yaw-rate gains only if obstacle-clearance guards pass
  separate proof, generalization, behavior-retention, and promotion gates
  forbid checkpoint promotion before a later proof/generalization audit
  keep mitigation reference rows outside ordinary denominators
  route to a future execution/training preflight or stop

forbidden interpretation:
  no ranking, winner, promotion, validation, success-rate verdict, performance,
  paper, current-sim, high-fidelity, full-driver, or self-ID claim
```

This pivot is aligned with the post-M2470 Route A objective: keep building a
deployable engineering-controller driver under the human-view/no-privileged
actor contract, but stop converting small source-only diagnostics into claims.
If the guardrailed design cannot produce a bounded future training/evaluation
manifest, the branch should stop or pivot to a broader scenario/architecture
axis rather than repeating same-surface panels.
