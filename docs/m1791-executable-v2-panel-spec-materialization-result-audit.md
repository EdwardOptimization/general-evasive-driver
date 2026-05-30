# M1791 Executable V2 Panel Spec Materialization Result Audit

- status: completed
- decision: `executable_v2_materialization_audit_admit_reset_feasibility_adapter`
- audited summary: `runs/m1790_executable_v2_panel_spec_materialization_preflight/summary.json`
- no reset in audit: true
- no rollout in audit: true
- training/replay/PPO: false

## Summary

M1791 audits the M1790 executable v2 panel spec materialization before any reset
feasibility run. The materialization passes the schema and guardrail audit:

```text
result_class: executable_v2_panel_spec_materialization_preflight_pass
v2_panel_spec_count: 312
role_surface_count: 6
profile_control_count: 12
reset_ready_spec_count: 312
labels_enter_actor_input_count: 0
environment_reset_scheduled_count: 0
environment_rollout_scheduled_count: 0
training_scheduled_count: 0
profile_specific_tuning_count: 0
missing_config_count: 0
missing_checkpoint_count: 0
ranking_admissible_by_default: false
diagnostic_only_no_ranking_claim_count: 312
guardrail_violation_count: 0
```

The executable specs are ready for a reset-only feasibility preflight in
principle. The existing M1773 reset feasibility helper, however, reads the old
bounded-panel schema. M1790 writes `executable_v2_panel_specs.json` with the key
`executable_v2_panel_specs`. A small v2 adapter is therefore needed before the
reset run.

## Artifact Audit

Required M1790 artifacts exist:

```text
summary.json
executable_v2_panel_specs.json
executable_v2_panel_specs.csv
executable_v2_panel_matrix.csv
v2_role_surface_summary.csv
v2_field_contract.csv
v2_reuse_mapping.csv
v2_claim_boundary.csv
```

Role surface balance:

```text
stable_avoidance_aes: 72 specs
drift_required_recovery: 36 specs
hidden_robust_aes_feasible: 36 specs
hidden_robust_drift_required: 72 specs
hidden_robust_unavoidable_mitigation: 60 specs
unavoidable_mitigation: 36 specs
```

Each role surface preserves all twelve profile controls and keeps ranking
blocked by default.

## Adapter Need

The next step should not force the old bounded-panel reset helper to parse a
different schema. M1792 should implement a v2 reset-feasibility adapter that:

- reads `executable_v2_panel_specs.json`;
- iterates `executable_v2_panel_specs`;
- uses each row's `env_config` directly;
- checks reset success only;
- preserves v2 fields in output rows;
- records sampling failures by `v2_panel_spec_id`, `v2_role_surface_id`,
  `profile_name`, `v2_task_label`, and `hidden_dynamics_bucket`;
- writes no rollout, training, replay, PPO, ranking, or promotion artifacts.

## Route Decision

Route to M1792 executable v2 reset-feasibility adapter implementation. After
the adapter is tested, a later milestone can run the 312-row reset-only
feasibility preflight.

## Guardrails

- environment reset started in audit: `false`
- environment rollout started in audit: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1790 executable v2 specs pass artifact and guardrail audit;
- a v2 reset-feasibility adapter is admitted.

Unsupported:

- reset feasibility result;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.
