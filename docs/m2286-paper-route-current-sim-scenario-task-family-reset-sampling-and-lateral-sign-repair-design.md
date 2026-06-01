# M2286 Paper-Route Current-Sim Scenario Task-Family Reset-Sampling And Lateral-Sign Repair Design

- status: completed
- decision: `current_sim_scenario_task_family_reset_repair_design_admit_combined_implementation`
- manifest: `experiments/manifests/m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design.json`
- parent audit: `docs/m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit.md`
- reset execution in M2286: `false`
- rollout/measured execution in M2286: `false`
- policy actions executed in M2286: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2286 freezes a combined repair for the two M2284/M2285 blockers:

```text
1. R1-R5 reset-sampling failure:
   60/60 non-R0 rows fail obstacle sampling.

2. lateral sign mismatch:
   successful R0 left/right rows show left_offset and right_offset use the
   opposite sign from the M2279/M2280 frame convention.
```

The repair must keep the P0 human-view actor contract unchanged. It may repair
generation metadata and config sampling ranges, but it must not add role labels,
feasibility labels, hidden parameters, or oracle values to actor input.

## Repair Principle

Do not solve this by only raising `max_sample_attempts`.

The current failure means many materialized rows are outside the current
sampler's feasible label region. The repair should make generation
sampler-aware:

```text
scenario role target
  -> deterministic classifier feasibility check
  -> narrow reset-valid env_config ranges
  -> materialized config pack
  -> reset-only validation
```

The deterministic precheck should use the same label semantics as the
environment sampler:

```text
classify_obstacle_scenario(
  speed=speed_ref,
  mu=sampled_or_center_mu,
  obstacle_distance=distance,
  obstacle_half_width=half_width,
  config=obstacle.scenario_config(...)
)
```

This keeps the repair aligned with the actual `aeb_feasible`, `aes_feasible`,
`drift_required`, and `unavoidable` definitions.

## Lateral Sign Repair

M2287 must correct the materializer convention:

```text
centerline -> 0.0
left_offset -> +1.2
right_offset -> -1.2
```

This matches the environment placement:

```text
obstacle_position = path_position
                  + tangent * obstacle_distance
                  + normal_left * obstacle_lateral_offset
```

and the M2279/M2280 convention:

```text
positive obstacle_lateral_offset -> frame-left
negative obstacle_lateral_offset -> frame-right
```

The reset validator should remain strict:

```text
left_offset requires actual_obstacle_lateral_offset >= +0.5
right_offset requires actual_obstacle_lateral_offset <= -0.5
centerline requires abs(actual_obstacle_lateral_offset) <= 0.05
```

## Sampler-Aware Role Repair

M2287 should add a small scenario-feasibility helper inside the materialization
module instead of hand-tuning one row at a time.

Required helper behavior:

```text
for each role family and hidden bucket:
  enumerate candidate speed, mu, distance, and half-width centers;
  classify each candidate with classify_obstacle_scenario;
  require the candidate label to match the role's allowed labels;
  require AEB-infeasible roles not to classify as aeb_feasible;
  prefer candidates with margin away from the label boundary;
  emit narrow ranges around the selected candidate.
```

The emitted ranges can be intentionally narrow for this v0 reset-valid
diagnostic pack. Broader distribution coverage can be added after reset validity
is proven.

Role constraints:

```text
R0_stable_avoidable:
  target label aeb_feasible; keep current behavior unless sign repair affects
  lateral rows.

R1_aeb_infeasible_stable_aes:
  target label aes_feasible; require aeb infeasible; avoid candidates near
  aeb_feasible or drift_required boundaries.

R2_handling_limit_drift_capable_avoidance:
  target label drift_required; require conventional lateral capacity below
  required offset but drift capacity above it.

R3_recovery_after_limit:
  target label drift_required; preserve finish_on_pass=false and recovery-window
  metadata, but use sampler-aware drift_required geometry.

R4_unavoidable_mitigation:
  target label unavoidable; choose close/wide/low-authority candidates where
  drift lateral capacity remains below required offset.

R5_hidden_dynamics_robustness:
  preserve same-scene group ids and at least four hidden dynamics buckets; use
  sampler-aware geometry that resets under allowed labels aes_feasible or
  drift_required for each selected hidden bucket.
```

## M2287 Implementation Scope

M2287 may edit:

```text
src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py
tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py
```

It may also add focused helper tests if needed. It should reuse the M2284 reset
validator without changing the pass semantics except for bug fixes discovered by
tests.

M2287 must not change:

```text
src/autodrift/env.py actor observation fields
P0 actor contract
role labels as metadata-only values
reset-validation signed lateral convention
```

## M2287 Commands

M2287 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py \
  tests/test_paper_route_current_sim_scenario_task_family_reset_validation.py \
  tests/test_obstacle_lateral_offset_instrumentation.py
```

Then rerun repaired materialization:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/materialization \
  --next-blocker m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation
```

Then run reset-only validation:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_reset_validation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation \
  --eval-seed-base 228700 \
  --target-spec-count 72 \
  --expected-observation-dim 72 \
  --next-blocker m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit
```

## M2287 Pass Gates

M2287 passes only if:

```text
materialization result_class == current_sim_scenario_task_family_config_materialization_pass
scenario_spec_count == 72
unsupported_execution_blocker_count == 0
actor_contract_violation_count == 0
labels_enter_actor_input_count == 0
ranking_admissible_count == 0
guardrail_violation_count == 0

reset result_class == current_sim_scenario_task_family_reset_validation_pass
reset_attempt_count == 72
reset_success_count == 72
reset_failure_count == 0
observation_dimension_failure_count == 0
actor_contract_violation_count == 0
label_not_allowed_count == 0
single_label_exact_mismatch_count == 0
lateral_offset_numeric_mismatch_count == 0
lateral_bucket_mismatch_count == 0
reset guardrail_violation_count == 0
```

If M2287 fails, it must still write both materialization and reset-validation
artifacts and route to result audit. It must not do another repair/rerun inside
the same milestone.

## Claim Boundary

If M2287 passes, it may claim only:

```text
the repaired 72-spec role-family pack is materialized and reset-valid under the
current simulator and P0 actor contract.
```

It still cannot claim:

- rollout success;
- measured execution success;
- training result;
- controller-family ranking;
- winner selection;
- finite-window vs GRU conclusion;
- paper-level result;
- level3 self-identification.

## Next

Pre-register:

```text
m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation
```
