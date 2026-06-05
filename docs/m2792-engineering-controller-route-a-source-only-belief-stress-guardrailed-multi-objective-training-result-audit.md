# M2792 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Multi-Objective Training Result Audit

## Metadata

- status: completed
- decision: `accept_m2791_route_to_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel`
- manifest: `experiments/manifests/m2792-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-result-audit.json`
- audit doc: `docs/m2792-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-result-audit.md`
- parent summary: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/summary.json`
- parent gate matrix: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/gate_matrix.csv`
- parent checkpoint manifest: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoint_manifest.json`
- parent behavior-retention gates: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/behavior_retention_gate_rows.csv`
- parent candidate checkpoint: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt`
- follow-up manifest: `experiments/manifests/m2793-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-preflight.json`
- next: `m2793-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-preflight`

## Audit Result

M2792 accepts M2791 as complete and claim-safe preflight evidence:

```text
M2791 status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
failed_gate_ids: none
training_objective_rows: 18
training_run_rows: 54
proof_holdout_probe_rows: 36
proof_gate_rows: 13
generalization_gate_rows: 6
behavior_retention_gate_rows: 7
promotion_guard_rows: 4
actor_guard_rows: 6
mitigation_guard_rows: 8
claim_rows: 11
gate_matrix_rows: 30
candidate_checkpoint_written: true
checkpoint_behavior_changed: true
checkpoint_promoted: false
```

Checkpoint lineage is auditable:

```text
source checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
source checkpoint hash:
  e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
base candidate checkpoint:
  runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt
base candidate checkpoint hash:
  96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
M2791 candidate checkpoint:
  runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt
M2791 candidate checkpoint hash:
  32b001944b688162ba9afb379aa6ed54f59920261d3a10ec8572d6e2da769651
```

M2791 wrote a bounded source-only guardrailed update artifact and a new
candidate checkpoint. This is accepted as auditable engineering preflight
evidence only. It is not validation, ranking, promotion, success-rate verdict,
driver-performance evidence, paper evidence, current-sim verdict, high-fidelity
validation, full-driver evidence, or self-ID evidence.

## Behavior-Retention Audit

M2791 preserved the M2787 fresh-holdout guard baseline and kept obstacle
clearance as the hard guard before objective interpretation:

```text
M2787 paired delta rows: 72
M2787 obstacle-clearance negative rows: 29
M2787 obstacle-clearance positive rows: 43
M2787 road-margin positive rows: 72/72
M2787 yaw-rate lower rows: 60/72
M2787 throttle/brake conflict zero rows: 72/72
obstacle_clearance_regression_guard_required: true
obstacle_clearance_guard_hard_before_objectives: true
mean_action_delta_l1_from_base: 0.00001813857670640573
```

M2792 accepts the guard structure but does not interpret the new checkpoint as
better. Road-margin, yaw-rate, final-speed, throttle/brake conflict, and
action-delta movement remain subordinate to obstacle-clearance retention and
must be tested in a fresh closed-loop panel before any stronger claim.

## Actor Boundary

M2791 preserved the deployed actor contract:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input required: false
actor-visible stress/admission/curriculum labels: false
actor-visible role/dynamics/outcome/success/progress/route/verdict labels: false
finite observation/action gates: pass
```

The training objective, stress family, role family, dynamics axis, guard,
admission, outcome, success, progress, route, and verdict fields remain
evaluator metadata only. M2792 makes no actor input or action-contract change.

## Gate Separation

M2791 separated gate tiers:

```text
proof gates:
  13/13 pass

generalization gates:
  6/6 pass

behavior-retention gates:
  7/7 pass

promotion guards:
  4/4 pass, blocking promotion/selection/verdict
```

The proof, generalization, and behavior-retention rows establish artifact
completeness and guarded preflight consistency. They do not establish a
validated driver or a promotable checkpoint.

## Mitigation And Claim Boundary

M2791 mitigation reference rows are guarded:

```text
mitigation guard rows: 8
ordinary denominator allowed: false
included in training rows: false
included in proof denominator: false
included in promotion denominator: false
```

M2791 claim rows reject:

```text
validation result
ranking result
winner selection
checkpoint promotion
success-rate verdict
driver performance
paper result
current-sim verdict
high-fidelity validation
level3 self-identification
```

M2792 accepts only the allowed claim that M2791 bounded guardrailed preflight
artifacts are complete and claim-safe.

## Route Decision

M2792 routes to M2793: a source-only fresh-holdout triad closed-loop delta
panel over the M2655 source checkpoint, the M2782 base candidate, and the M2791
candidate. M2793 should use fresh seed indices outside M2784 seed_index 0..3 and
M2787 seed_index 4..7, keep horizon longer than the M2787 120-step surface, and
write source/base/candidate execution rows with candidate-minus-source and
candidate-minus-base deltas.

M2793 must keep obstacle-clearance retention as a hard guard before road-margin
or yaw-rate interpretation. It must not validate, rank, select a winner,
promote, compute success-rate verdicts, claim repair success, claim driver
performance, claim paper evidence, claim current-sim verdict, claim
high-fidelity validation, claim full ideal driver completion, or claim level3
self-identification.

## Rejected Claims

M2792 does not support:

```text
repair success
driver performance
validation readiness
validation result
ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```
