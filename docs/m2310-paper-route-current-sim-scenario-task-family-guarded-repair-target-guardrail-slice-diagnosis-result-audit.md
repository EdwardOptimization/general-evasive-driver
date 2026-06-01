# M2310 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Target/Guardrail Slice Diagnosis Result Audit

- status: completed
- decision: `guarded_repair_slice_diagnosis_audit_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2310-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-result-audit.json`
- parent summary: `runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/summary.json`
- parent slice rows: `runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/slice_delta_rows.csv`
- reset/rollout/policy action in M2310: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Artifact Completeness

M2309 is complete enough for an audit:

```text
result_class: current_sim_scenario_task_family_guarded_repair_slice_diagnosis_pass
input_episode_count_baseline: 1080
input_episode_count_candidate: 1080
slice_delta_row_count: 31
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
guardrail_violation_count: 0
```

The diagnosis is artifact-only. It did not run environment reset, rollout,
policy action, measured execution, replay, PPO, training, private holdout, or
profile ranking.

## Repair Gate Audit

The guarded-v2 repair gate fails:

```text
repair_gate_pass: false
global_offtrack_policy_pass: false
global_collision_policy_pass: false
offtrack_target_policy_pass: false
collision_guardrail_policy_pass: false
```

Global deltas versus M2293 are negative for the repair route:

```text
baseline_global_offtrack_count: 785
candidate_global_offtrack_count: 786
global_offtrack_delta: +1

baseline_global_collision_count: 209
candidate_global_collision_count: 218
global_collision_delta: +9
```

Target and guardrail slices also fail:

```text
offtrack_target_nonincrease_count: 9 / 20
offtrack_target_increase_count: 11 / 20
collision_guardrail_nonincrease_count: 4 / 11
collision_guardrail_increase_count: 7 / 11
```

Largest offtrack target increases:

```text
early_far: +10
mid: +5
R0_stable_avoidable: +4
aeb_feasible: +4
left_offset: +4
right_offset: +4
nominal: +4
tire_stiffness_shift: +2
R3_recovery_after_limit: +2
off_track outcome/termination: +1 / +1
```

Largest collision guardrail increases:

```text
late_close: +15
centerline: +10
low_mu: +8
collision_failure: +9
obstacle_collision: +9
drift_required: +4
right_offset: +3
```

## Interpretation

M2310 accepts the M2309 negative result. The guarded-v2 branch produced clean
execution artifacts, but it did not improve the actual target/guardrail policy:

- global offtrack worsened by `+1`;
- global collision worsened by `+9`;
- offtrack target slices worsened in `11 / 20` cases;
- collision guardrail slices worsened in `7 / 11` cases.

This is not a single-slice anomaly and not a ranking problem. It is broad enough
to trigger the local-search guard. Another scalar reward tweak, another
same-family guarded repair run, or another selected-checkpoint ranking pass
would keep the branch in local search without changing the paper-route evidence
axis.

## Failure Taxonomy

```text
behavior_regression:
  guarded-v2 selected checkpoints worsened global offtrack/collision versus
  M2293.

scenario_sampling_failure:
  the current role-family pack exposes broad offtrack and collision failures
  that the repair route did not resolve.

objective_overfit:
  training-selection artifacts and target pressure did not transfer to measured
  target/guardrail outcomes.

metric_artifact:
  selected-checkpoint training metrics and candidate counts are insufficient
  repair evidence.

seed_fragility:
  selected rows were execution-clean but did not pass outcome floors across the
  fixed 1080-episode panel.
```

## Public Gate Overfit Risk

Risk is high if the branch continues locally. The M2298 target/guardrail pack
has now been used for:

```text
guarded repair config materialization;
15-run selected checkpoint training;
1080-episode measured execution;
target/guardrail slice diagnosis.
```

The next step must be synthesis, not another same-support repair. If the route
continues after synthesis, it must change the evidence axis or materially
change the repair mechanism before execution.

## Next Route

Route to branch synthesis:

```text
m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis
```

M2311 should synthesize M2300-M2310 and decide whether to pivot away from
guarded-v2 scalar repair, stop the branch, or admit a clearly different
non-local route. It must not train, rollout, rank profiles, select a winner,
claim finite-window vs GRU, claim paper-level evidence, or claim level3
self-identification.

## Follow-Up

Pre-registered:

```text
experiments/manifests/m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.json
```
