# M3003 Engineering Controller Route A Post-Residual-Stop Source-Axis Expansion Evidence Surface Design

## Metadata

- status: completed
- decision: `admit_m3004_post_residual_stop_source_axis_expansion_materialization_preflight`
- manifest: `experiments/manifests/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design.json`
- design artifact: `docs/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design.md`
- parent synthesis: `docs/m3002-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-synthesis.md`
- governing route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-preflight.json`
- next: `m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-preflight`

M3003 is design-only. It does not run reset, step, rollout, replay,
validation, training, PPO, private holdout, source build, adapter probe,
external simulation, ranking, winner selection, checkpoint mutation,
checkpoint promotion, or success-rate verdict computation.

## Design Premise

M3002 closes the M2998-M3001 residual-head branch because the only closed-loop
diagnostic result was behavior-neutral. M3000 produced complete diagnostic rows
over the fixed M2996 denominator, but every parent/candidate outcome bucket
matched. Another actor-head-delta residual-head repair over the same surface is
therefore local-search drift, not new evidence.

M3003 originally asked for a fresh source-diverse Route A diagnostic
denominator. The live audit finds that the old interpretation, "fresh unused
M1690 L3 task_source rows," is no longer available. The correct next route is
to stop treating M1690 L3 row selection as the source of freshness and require
a no-execution source-axis expansion materialization before any later
diagnostic execution.

## Evidence Audit

The audited denominator is the M1690 executable workload:

```text
M1690 executable workload rows: 864
L3_online_gru rows: 72
L3_online_gru unique task_source_id values: 72
L3 task_source_id range: m1680-spec-0000 through m1680-spec-0071
```

The prior Route A surfaces already cover the full M1690 L3 task_source-id
space at the identity level:

```text
M2737 unique task_source_id values: 9
M2746 unique task_source_id values: 8
M2807 unique task_source_id values: 12
M2816 unique task_source_id values: 12
M2828 unique task_source_id values: 16
M2838 unique task_source_id values: 16
M2868 unique task_source_id values: 24
M2877 unique task_source_id values: 11
M2916 candidate/source unique task_source_id values: 32
M2919 bounded execution unique task_source_id values: 21
M3000 candidate/parent unique task_source_id values: 21

union across audited prior surfaces: 72
unused M1690 L3 task_source_id values: 0
surface ids outside M1690 L3: 0
```

The residual branch also lacks source freshness relative to the dependency-facing
surface:

```text
M2919 vs M3000 candidate task_source_id delta:
  only M2919: 0
  only M3000 candidate: 0
  intersection: 21

M2919 vs M3000 parent task_source_id delta:
  only M2919: 0
  only M3000 parent: 0
  intersection: 21
```

This means M3000 is a useful behavior-neutral diagnostic result, but it is not
a fresh source-diverse denominator relative to M2919 at the task_source-id
granularity.

## Exhausted Surface Finding

M3003 rejects this candidate route:

```text
select_unused_m1690_l3_rows_for_next_diagnostic_surface
```

Reason:

```text
all 72 M1690 L3 task_source_id values are already represented by prior audited
Route A surfaces, and M2876/M2877 already consumed the last 11 remaining L3
task_source ids after the earlier exclusion set.
```

M3003 also rejects these substitutes:

```text
reuse_m2996_m3000_residual_head_denominator
reuse_m2919_dependency_facing_execution_rows
rerun_m1690_l3_rows_under_only_a_new_eval_seed
continue_actor_head_delta_residual_fitting_without_new_source_axis
count_prior protected or stale fixed-source guardrails as ordinary candidates
```

A new eval seed can be a repeatability guard later, but it is not by itself a
fresh source-diverse evidence surface. Freshness must come from a source-axis
change that is distinct from the fixed M1690 L3 task_source-id denominator.

## Design Decision

M3003 admits one follow-up route:

```text
m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-preflight
```

M3004 must be a no-execution materialization preflight. Its job is to convert
the exhausted-surface finding into machine-checkable inventory, exclusion,
candidate-axis, actor-contract, claim-boundary, and gate artifacts. It must not
execute a policy or environment and must not claim repair success, validation,
performance, paper evidence, high-fidelity evidence, finite-window-vs-GRU
evidence, full-driver evidence, or self-ID evidence.

## Source-Axis Expansion Contract

M3004 may inspect existing artifacts only as source inventory and guardrail
context:

```text
runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight/
runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/
runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight/
runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/
runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight/
runs/m3000_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_diagnostic_validation_preflight/
docs/m3002-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-synthesis.md
docs/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design.md
docs/post-m2470-route-plan.md
```

M3004 must classify candidate expansion axes before any execution:

```text
admissible candidate axis:
  creates or admits source rows outside the exhausted M1690 L3 task_source-id
  denominator, or defines a source-generation axis whose row identity is not
  merely one of m1680-spec-0000 through m1680-spec-0071.

supporting guard axis:
  repeats or perturbs already-audited rows only to preserve accounting,
  regression context, or repeatability guards.

rejected same-surface axis:
  changes only eval_seed, report label, wrapper label, residual-head artifact,
  row ordering, or diagnostic tag while keeping the same M1690 L3 fixed
  task_source denominator as the proposed evidence surface.
```

The source-axis expansion may use route-local source generators or source
inventory already present in the repository, but M3004 itself must not run a
source build, external dependency probe, reset, rollout, validation, training,
or benchmark. If no admissible axis exists, M3004 must materialize an explicit
stop route instead of fabricating freshness.

## Required M3004 Artifacts

M3004 should write artifacts under:

```text
runs/m3004_engineering_controller_route_a_post_residual_stop_source_axis_expansion_materialization_preflight/
```

Required artifact families:

```text
summary.json
source_inventory_rows.csv
exhausted_m1690_l3_surface_rows.csv
prior_surface_identity_rows.csv
source_axis_candidate_rows.csv
rejected_same_surface_rows.csv
supporting_guard_axis_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-preflight.md
experiments/manifests/m3005-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-result-audit.json
```

Minimum gate requirements:

```text
status_pass: true only if all required artifacts are present
exhausted_m1690_l3_confirmed: true
unused_m1690_l3_task_source_count: 0
same_surface_reuse_rejected: true
actor_observation_shape: 72
action_shape: 3
hidden_oracle_actor_inputs: false
execution_performed: false
training_performed: false
validation_claim: false
performance_claim: false
paper_claim: false
high_fidelity_claim: false
self_id_claim: false
follow_up_manifest_registered: true
```

## Actor And Claim Boundary

The actor contract remains unchanged:

```text
actor observation shape: 72
action shape: 3
hidden/oracle/source/target/route/outcome/success/progress/verdict labels in
actor input: false
```

M3003 and M3004 may use source-family, task-family, route, outcome, failure,
and prior-surface labels only as evaluator-side accounting columns. Those
labels must not become actor inputs, reward inputs, hidden dynamics shortcuts,
target labels, progress labels, ranking groups, or paper/self-ID verdict
labels.

M3003 supports only this claim:

```text
the fixed M1690 L3 task_source-id row space is exhausted for fresh Route A
denominator selection, so the next legal step is a no-execution source-axis
expansion materialization preflight or an explicit stop.
```

Forbidden interpretations:

```text
repair success
validation result
driver performance
current-sim verdict
high-fidelity validation result
finite-window-vs-GRU conclusion
paper evidence
full ideal driver completion
level3 self-identification evidence
checkpoint ranking or promotion
```
