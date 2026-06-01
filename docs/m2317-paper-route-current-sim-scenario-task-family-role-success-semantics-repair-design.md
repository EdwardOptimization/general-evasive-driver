# M2317 Paper-Route Current-Sim Scenario Task-Family Role Success Semantics Repair Design

- status: completed
- decision: `role_success_semantics_repair_design_admit_artifact_rescore_implementation`
- manifest: `experiments/manifests/m2317-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-design.json`
- parent audit: `docs/m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit.md`
- reset/rollout/policy action in M2317: `false`
- training/replay/PPO in M2317: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2317 freezes a bounded role-success semantics repair before implementation.
The repair addresses the M2315/M2316 result:

```text
R0_stable_avoidable:
  r0_safe_stop_scenario_count: 12
  r0_aeb_safe_stop_episode_count: 60
  min/mean/max safe-stop clearance: 10.96082732487428 / 25.993928793681416 / 43.58735902844862

Residual support-blocked:
  residual_support_blocked_scenario_count: 18
```

The repair must not reinterpret driver capability, rank support policies, or
turn support policies into deployable candidates. It only fixes the current
success label semantics used by current-sim scenario task-family diagnostics.

## Role-Success Contract

Existing obstacle-pass success remains valid:

```text
obstacle-pass success:
  outcome_bucket == success_obstacle_pass
  OR raw success == true
  OR obstacle_completed == true and collision == false
```

Add a bounded R0 safe-stop success:

```text
safe-stop success is true iff:
  role_family == R0_stable_avoidable
  termination_reason == speed_too_low
  min_clearance_margin > 0.0
  collision == false
  offtrack == false
```

Role success:

```text
role_success = obstacle-pass success OR R0 safe-stop success
```

This rule is intentionally not global. For R2/R3 drift-required, R4 mitigation,
and R5 hidden-dynamics robustness rows, `speed_too_low` with positive clearance
remains diagnostic evidence, not automatic success. Those roles need separate
support/semantics design after the R0 repair is rescored.

## Implementation Boundary

M2318 should add a reusable helper module instead of copying success logic into
each runner:

```text
src/autodrift/paper_route_current_sim_scenario_task_family_role_success_semantics.py
```

Minimum helper API:

```text
raw_obstacle_pass_success(row) -> bool
is_collision(row) -> bool
is_offtrack(row) -> bool
is_r0_safe_stop_success(row) -> bool
role_success(row) -> bool
role_success_reason(row) -> str
```

M2318 should update the duplicated current-sim task-family success call sites to
use the helper:

```text
src/autodrift/paper_route_current_sim_scenario_task_family_feasibility_calibration.py
src/autodrift/paper_route_current_sim_scenario_task_family_measured_execution.py
src/autodrift/paper_route_current_sim_scenario_task_family_failure_slice_diagnosis.py
```

M2318 should preserve source rows by adding role-success fields rather than
silently overwriting the original terminal metrics where practical:

```text
raw_success
role_success
role_success_reason
role_success_outcome_bucket
```

If a legacy aggregate only has a `success` column, it may use role success after
the repair, but artifact rows should expose enough fields to audit the change.

## Artifact-Only Rescore

Before any new rollout, M2318 must rescore the existing M2313 artifacts:

```text
input:
  runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv
  configs/paper_route_current_sim_scenario_task_family_v0.json

output:
  runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/summary.json
  runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv
  runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/scenario_support_labels_rescored.csv
  runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/role_support_summary_rescored.csv
  runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/claim_boundary.csv
```

The rescore should not run environment reset, rollout, policy actions, measured
execution, training, replay, PPO, or private holdout.

## Expected Rescore Gates

M2318 passes only if the R0 repair is visible and bounded:

```text
result_class == current_sim_scenario_task_family_role_success_semantics_repair_pass
input_episode_count == 1080
rescored_episode_count == 1080
guardrail_violation_count == 0
R0 role_success_support_clear_count == 12
R0 aeb_role_success_count >= 60
R0 safe_stop_success_count >= 60
R0 metric_conflict_count == 0
```

The expected global support-label direction is:

```text
support_clear increases by at least 12 versus M2313
metric_conflict decreases by at least 12 versus M2313
```

This does not mean R2-R5 are solved. The rescore must still report residual
support-blocked or mixed rows separately.

## Required Tests

Focused tests should cover:

```text
R0 speed_too_low with positive clearance and no collision/offtrack -> role_success true
R0 speed_too_low with collision -> role_success false
R0 speed_too_low with offtrack -> role_success false
R0 speed_too_low with nonpositive clearance -> role_success false
R2/R3/R4/R5 speed_too_low with positive clearance -> not safe-stop success
legacy obstacle-pass success remains true
rescore converts R0 support labels to support_clear without ranking policies
```

## M2318 Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_role_success_semantics.py
```

Artifact-only rescore:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics_repair \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --episode-rows runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv \
  --output-dir runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair \
  --target-episode-count 1080 \
  --target-scenario-spec-count 72 \
  --next-blocker m2319-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-result-audit
```

## Claim Boundary

Allowed claim:

```text
M2317 defines a bounded role-success semantics repair for R0 safe-stop rows and
an artifact-only rescore route.
```

Blocked claims:

```text
driver performance improvement;
support-policy/controller-family ranking;
checkpoint promotion;
paper-level current-sim result;
finite-window vs GRU conclusion;
level3 self-identification evidence;
R2-R5 support solved.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2318-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-implementation.json
```
