# M2233 Paper-Route Current-Sim Matched-Budget Medium Training Config Materialization

- status: completed
- decision: `current_sim_matched_budget_medium_training_config_materialization_pass_route_to_execution`
- manifest: `experiments/manifests/m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization.json`
- run artifact: `runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_matched_budget_medium_training_configs.py`
- focused tests: `2 passed`

## Result

M2233 materializes the M2232 medium-v1 design without starting reset, rollout,
measured execution, replay, PPO, training, or policy action execution.

Key fields:

- result_class: `current_sim_matched_budget_medium_training_config_materialization_pass`
- stage: `matched_budget_medium_v1`
- source_stage: `matched_budget_short_v0`
- expected_config_count: `15`
- generated_config_count: `15`
- training_matrix_row_count: `15`
- source_missing_count: `0`
- budget_signature_count: `1`
- budget_matched: `true`
- medium_total_steps_count: `15`
- contract_violation_count: `0`
- guardrail_violation_count: `0`
- ranking_admissible_count: `0`
- winner_selected: `false`
- training_started: `false`
- policy_action_executed: `false`
- environment_reset_started: `false`
- environment_rollout_started: `false`
- measured_rollout_started: `false`
- finite_window_vs_gru_conclusion_made: `false`
- paper_level_claim_made: `false`
- level3_self_id_claim_made: `false`

Generated config directory:

```text
configs/paper_route_profiles/m2233_matched_budget_medium_v1/
```

Run artifacts:

```text
runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/summary.json
runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/training_matrix.csv
runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/claim_boundary.csv
runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/run_state.json
```

The matrix points to:

```text
runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution
```

## Interpretation Boundary

This is config materialization only. It does not produce new checkpoint quality
evidence, controller-family ranking evidence, finite-window-vs-GRU evidence,
paper-level evidence, or self-identification evidence.

It does prove that the medium-v1 training panel is structurally ready to run:
same five profiles, same three seeds, one budget signature, `32768` steps in
all generated configs, and no actor-input or guardrail violation.

## Next

Pre-register:

```text
m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run
```

M2234 may adapt the focused M2230 runner for expected `32768`-step matrices and
run the 15 medium-v1 train_ppo jobs. Interpretation must remain blocked until
a later result audit.
