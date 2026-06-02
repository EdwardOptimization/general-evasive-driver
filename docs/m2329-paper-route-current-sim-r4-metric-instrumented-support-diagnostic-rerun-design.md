# M2329 Paper-Route Current-Sim R4 Metric-Instrumented Support Diagnostic Rerun Design

- status: completed
- result_class: `r4_metric_instrumented_support_diagnostic_rerun_design_admit_bounded_execution`
- manifest: `experiments/manifests/m2329-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-design.json`
- parent audit: `docs/m2328-paper-route-current-sim-r4-mitigation-metric-instrumentation-result-audit.md`
- base config: `configs/paper_route_current_sim_scenario_task_family_v0.json`
- reset/rollout/policy action in M2329: `false`
- measured execution in M2329: `false`
- training/replay/PPO in M2329: `false`
- actor input changed: `false`
- reward/training objective changed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2329 freezes a bounded R4-only diagnostic rerun. The purpose is to regenerate
R4 support-policy diagnostic rows after M2327 field export, not to rank support
policies or claim mitigation performance.

R4 scenario IDs:

```text
m2277_r4_00
m2277_r4_01
m2277_r4_02
m2277_r4_03
m2277_r4_04
m2277_r4_05
m2277_r4_06
m2277_r4_07
m2277_r4_08
m2277_r4_09
m2277_r4_10
m2277_r4_11
```

Panel:

```text
scenario_count: 12
support_policies: aeb, aes, envelope_aes
support_policy_count: 3
seed_repeats: 5
expected_episode_count: 180
```

## Execution Scope For M2330

M2330 may run environment reset, rollout, policy actions, and measured execution
because it is explicitly a support diagnostic rerun. It must still forbid:

```text
training
replay
PPO
checkpoint promotion
private holdout
support-policy ranking
winner selection
paper-level claims
finite-window vs GRU conclusions
level3 self-ID claims
```

The implementation should:

```text
1. Read configs/paper_route_current_sim_scenario_task_family_v0.json.
2. Materialize an R4-only config with the 12 R4 specs.
3. Call run_feasibility_calibration with support policies aeb/aes/envelope_aes and 5 seed repeats.
4. Write episode_rows.csv preserving R4 mitigation aliases and availability flags.
5. Write metric completeness artifacts.
6. Preserve support policies as diagnostic bounds.
```

Expected output dir:

```text
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun
```

## Required Field Checks

M2330 should verify at least these fields exist in `episode_rows.csv`:

```text
impact_speed_mps
impact_speed_mps_available
time_to_collision_s
time_to_collision_s_available
collision_side_proxy
delta_v_at_impact_mps_available
post_event_speed_mps_available
recoverability_window_success_available
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
impact_severity_proxy
collision_mitigation_score
```

The audit may later decide whether true post-collision continuation is needed,
but M2330 must not change collision termination behavior.

## Claim Boundary

Allowed claim:

```text
M2329 defines a bounded non-ranking R4 support diagnostic rerun using the
exported mitigation metric fields.
```

Blocked claims:

```text
mitigation performance measured;
support policies ranked;
R4 mitigation solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up Manifest

```text
experiments/manifests/m2330-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-implementation.json
```
