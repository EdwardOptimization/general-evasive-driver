# M2502 Engineering Controller Source-Only Baseline Comparison Result Audit

- status: completed
- decision: `accept_source_only_baseline_comparison_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2502-engineering-controller-source-only-baseline-comparison-result-audit.json`
- audited summary: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json`
- audited telemetry rows: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv`
- audited controller-role metric panel: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv`
- next milestone: `m2503-engineering-controller-source-only-metric-panel-branch-synthesis`
- external high-fidelity simulation installed/imported/executed in M2502: `false`
- new policy action/measured validation/training/replay/PPO/ranking/winner selection in M2502: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Audit Decision

M2502 accepts M2501 as a completed source-only diagnostic baseline comparison
preflight.

Accepted summary:

```text
result_class: engineering_controller_source_only_baseline_comparison_preflight_pass
status_pass: true
comparison_subject_count: 3
comparison_subjects:
  m1154_policy_actor
  coast_open_loop
  straight_full_brake_open_loop
role_count: 3
reset_count: 9
expected_reset_count: 9
telemetry_row_count: 900
expected_telemetry_row_count: 900
role_subject_panel_row_count: 9
expected_role_subject_panel_row_count: 9
```

Checkpoint admission:

```text
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
```

Reset digest audit:

```text
role_reset_digests_match_across_subjects: true
role_reset_digests_differentiated: true
unique_role_reset_observation_digest_count: 3
stable_aes: be74fec0227f041e
drift_required_recovery: ca4fed8c6285ef14
unavoidable_mitigation: eff1d7f164d537cb
```

CSV artifact audit:

```text
telemetry_rows.csv data rows: 900
controller_role_metric_panel.csv data rows: 9
comparison_subjects:
  coast_open_loop: 300 telemetry rows
  m1154_policy_actor: 300 telemetry rows
  straight_full_brake_open_loop: 300 telemetry rows
roles:
  stable_aes: 300 telemetry rows
  drift_required_recovery: 300 telemetry rows
  unavoidable_mitigation: 300 telemetry rows
observation_shape:
  72 on every telemetry row
action_shape:
  3 on every telemetry row
action_finite/action_within_bounds:
  true on every telemetry row
backend_status:
  running on every telemetry row
diagnostic_wheel_force_count:
  4 on every telemetry row
parameterized_fixture:
  true on every telemetry row
diagnostic_only:
  true on every telemetry and panel row
```

Blocked execution/claim flags:

```text
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
measured_validation_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
controller_family_verdict_computed: false
driver_performance_claim_made: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Supported Claims

Supported:

```text
M2501 implements the M2500 comparison protocol and writes diagnostic telemetry
for the admitted checkpoint and two open-loop action baselines over identical
parameterized source-only role reset specs.

The comparison artifact preserves the 72-observation / 3-action contract, uses
finite bounded actions, and keeps hidden diagnostics and success labels out of
actor input.

The artifact can be used in a branch synthesis to decide the next engineering
route.
```

## Rejected Interpretations

M2501/M2502 do not support:

```text
driver performance
role-specific success or recovery quality
success-rate improvement
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

The source-only comparison shows diagnostic trajectory/action envelopes only.
It is not a ranking between the policy actor, coast, and full-brake baselines.

## Failure Taxonomy

Resolved:

```text
metric_artifact / missing_source_only_baseline_protocol:
  resolved for diagnostic comparison telemetry. M2501 now has a bounded panel
  with fixed row counts and explicit rejected interpretations.
```

Controlled:

```text
contract_violation:
  controlled. Checkpoint admission and all observation/action gates pass.

lineage_invalid:
  controlled. M2500 design, M2501 artifacts, docs, review, queue, status, and
  scoreboard are present.

scenario_sampling_failure:
  controlled for this source-only panel because reset digest gates verify same
  role reset across subjects and differentiated role resets across roles.
```

Unresolved:

```text
behavior_regression:
  not decided. The panel compares envelopes but does not define success,
  recovery quality, or outcome labels.

objective_overfit:
  medium. The branch has produced useful engineering diagnostics, but the
  engineering source-only metric panel branch has reached synthesis cadence.
```

## Route Decision

M2502 routes to:

```text
m2503-engineering-controller-source-only-metric-panel-branch-synthesis
```

The branch should synthesize M2493-M2502 before any further source-only metric,
comparison, repair, performance, or validation milestone. The synthesis should
decide whether to stop, continue with a bounded engineering artifact, pivot to
high-fidelity backend work, or promote to a new branch.
