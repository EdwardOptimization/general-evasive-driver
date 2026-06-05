# M2727 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight`
- manifest: `experiments/manifests/m2727-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-design.json`
- design doc: `docs/m2727-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-design.md`
- parent audit: `docs/m2726-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-result-audit.md`
- parent candidate pack: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight.json`
- next: `m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight`

## Design Premise

M2726 accepts M2725 as complete and claim-safe artifact-only repair candidate
materialization. The accepted candidate pack contains:

```text
candidate target rows: 31
shared repair overlay rows: 15
guardrail rows: 17
actor contract rows: 9
claim-boundary rows: 23
gate rows: 17
```

The M2725 candidate rows are the only execution-admissible rows for the next
preflight. Collision caution rows, diagnostic success context rows, and
protected exclusion rows remain guardrails and must not be converted into
ordinary execution or denominator rows.

M2727 is design-only. It does not reset, step, run policy action, train, replay,
run PPO, overwrite active configs, or execute repair.

## Execution Surface

M2728 should consume:

```text
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/summary.json
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/candidate_target_rows.csv
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/shared_repair_overlay_rows.csv
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/guardrail_rows.csv
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/actor_contract_rows.csv
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/claim_boundary_rows.csv
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/gate_matrix.csv
```

The admitted execution set is:

```text
31 candidate target rows
task families: T4, T5
profiles: L0_current_masked, L2_window_50_current_tiled, L3_online_gru, L3_reset_control_corrected
repair overlay: shared road-containment overlay
guardrail overlay: shared collision-clearance guardrail
```

M2728 must reject or record a failure row if any candidate row lacks a source
workload id, profile, task source id, target row id, or shared overlay binding.
It must not expand beyond the 31 M2725 candidate target rows.

## Temporary Overlay Application

M2728 may apply the M2725 overlay only as an in-memory per-run configuration
patch. It must not overwrite committed configs, active baseline configs, or
parent artifacts.

The overlay must be applied uniformly across all 31 candidate rows:

```text
env.track_cost_scale = 2.8
env.heading_cost_scale = 0.25
env.road_margin_cost_scale = 1.2
env.road_margin_warning_fraction = 0.65
env.off_track_penalty = 6.0
env.termination_penalty = 8.0
obstacle.collision_penalty = 25.0
obstacle.dense_clearance_margin_reward_scale = 0.5
obstacle.dense_clearance_margin_reward_window = 10.0
obstacle.dense_clearance_margin_reward_clip = 0.25
obstacle.clearance_margin_reward_scale = 1.0
obstacle.clearance_margin_reward_clip = 0.25
obstacle.stable_aes_sideslip_penalty = preserve unless already configured
geometry fields = preserve parent values
```

Required handling:

```text
write repaired config snapshots under the M2728 run directory only
record overlay_applied true/false per execution row
record active_config_overwritten false in summary and gate rows
record profile_specific_tuning false for every row
record parent geometry preserved for every row
```

If the runner cannot apply the overlay without active config overwrite or
profile-specific tuning, M2728 must stop and write failure rows rather than
execute a compromised repair.

## Output Artifacts

M2728 should write:

```text
runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/summary.json
repair_execution_rows.csv
candidate_execution_failure_rows.csv
profile_aggregate.csv
anchor_aggregate.csv
repair_overlay_application_rows.csv
guardrail_audit_rows.csv
actor_contract_join_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight.md
```

The execution rows may include diagnostic metrics such as termination reason,
collision flag, offtrack flag, clearance margin, return, episode length, and
finite-metric checks. Those values are diagnostic only. They must not become
ranking, validation, success-rate verdict, driver-performance, paper,
current-sim, high-fidelity, full-driver, or self-ID claims.

## Guardrail Handling

M2728 must carry the 17 guardrail rows into `guardrail_audit_rows.csv`:

```text
2 collision caution rows
3 diagnostic success context rows
12 protected exclusion rows
```

Guardrail requirements:

```text
collision caution rows remain non-target guardrails
diagnostic success rows remain context not wins
protected exclusion rows remain not executed
protected rows remain outside ordinary success denominators
guardrail labels remain actor-invisible
guardrail outcomes do not become ranking denominators
```

If a repair execution row collides, leaves the road, or violates finite metric
checks, M2728 should record it plainly and route to result audit. It must not
hide failed rows or silently drop them from aggregates.

## Actor And Claim Boundary

M2728 must preserve:

```text
observation_shape: 72
action_shape: 3
no hidden/oracle actor input
no target labels actor-visible
no profile labels actor-visible
no protected labels actor-visible
no route/gate/progress/success/verdict labels actor-visible
no actor input or deployed action contract change
```

M2728 may use the existing M2655 checkpoint only as the policy under test. It
must not promote, train, fine-tune, replay, run PPO, use private holdout, or
profile-specific tune.

## Gate Matrix

M2728 passes only if all of these hold:

```text
M2725 summary status_pass true
31 candidate target rows accounted
15 shared overlay rows accounted
17 guardrail rows accounted
overlay application rows written
repair execution rows plus failure rows account for all 31 candidate rows
active_config_overwritten false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
target_labels_actor_visible false
protected rows executed false
protected rows in success denominator false
profile_specific_tuning false
ranking winner promotion success-rate verdict false
all required artifacts present
one result-audit follow-up manifest registered
```

If execution itself fails for some rows but failure rows are complete and
guardrails remain clean, M2728 may still pass as an artifact-complete bounded
execution preflight. Behavioral success is not the pass criterion.

## Follow-Up

M2727 admits:

```text
m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight
```

M2728 may execute reset, step, rollout, and policy action only for the 31 M2725
candidate target rows under the temporary overlay. It must register a separate
M2729 result audit before interpretation.

## Claim Boundary

Allowed M2727 claim:

```text
M2727 defines a bounded actor-safe execution protocol for the audited M2725
offtrack repair candidate pack and admits one separately pre-registered
execution preflight.
```

Rejected claims:

```text
repair execution result
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
protected mitigation preservation result
full ideal driver completion
level3 self-identification
```
