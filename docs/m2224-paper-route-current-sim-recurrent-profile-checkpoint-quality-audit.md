# M2224 Paper-Route Current-Sim Recurrent Profile Checkpoint Quality Audit

- status: completed
- decision: `current_sim_recurrent_profile_checkpoint_quality_audit_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2224-paper-route-current-sim-recurrent-profile-checkpoint-quality-audit.json`
- run artifact: `runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_recurrent_profile_checkpoint_quality_audit.py`
- focused tests: `1 passed`
- compile check: `passed`
- reset in M2224: `false`
- measured execution in M2224: `false`
- policy action executed in M2224: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2224 aggregates existing M2171 checkpoint/train/eval artifacts and M2221
profile-failure metrics. It writes:

```text
runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/summary.json
runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/checkpoint_quality_summary.csv
runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/profile_failure_quality_join.csv
runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/claim_boundary.csv
runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/run_state.json
```

Summary:

```text
result_class: current_sim_recurrent_profile_checkpoint_quality_audit_pass
profile_count: 8
join_row_count: 8
l3_online_total_train_steps: 1024
l3_online_eval_return_mean: 39.381635195580216
l3_online_eval_termination_rate: 0.6
l3_online_eval_lateral_rmse_mean: 2.2316688387892
l3_online_final_train_termination_rate: 1.0
l3_online_weak_eval_flag: true
l3_online_weak_train_flag: true
l3_online_diagnostic_success_count: 0
l3_reset_checkpoint_source_profile_name: L3_online_gru
l3_reset_aliases_online_checkpoint: true
l3_reset_diagnostic_success_count: 0
l2_window_25_diagnostic_success_count: 360
l3_weak_checkpoint_plausible: true
matched_budget_training_needed: true
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

The audit now treats `L3_reset_control` as a checkpoint-source alias for quality
metrics. Its quality source is `L3_online_gru`:

```text
quality_metric_source_profile_name: L3_online_gru
quality_metric_source_mode: inherited_checkpoint_source_metrics
```

## Interpretation

M2224 supports a narrow route decision:

```text
The current L3 zero-success diagnostic is plausibly explained by a weak
smoke-scale L3 checkpoint and must not be used as a finite-window-vs-GRU
verdict.
```

The evidence:

```text
L3_online_gru:
  diagnostic_success_count: 0
  diagnostic_offtrack_count: 348
  total_train_steps: 1024
  eval_termination_rate: 0.6
  eval_lateral_rmse_mean: 2.2316688387892
  final_train_termination_rate: 1.0
  weak_eval_flag: true
  weak_train_flag: true

L3_reset_control:
  diagnostic_success_count: 0
  diagnostic_offtrack_count: 348
  aliases L3_online_gru checkpoint: true
  inherited weak_eval_flag: true
  inherited weak_train_flag: true

L2_window_25:
  diagnostic_success_count: 360
  eval_termination_rate: 0.0
  weak_eval_flag: false
```

This is not a controller-family ranking because the panel is diagnostic-only,
candidate slices overlap, all checkpoints are smoke-scale, and training quality
is not matched enough for a paper-level comparison.

## Guardrails

M2224 did not run reset, rollout, measured execution, policy-action execution,
training, replay, PPO, or checkpoint promotion. It only reads existing
train/eval/failure artifacts and writes derived diagnostic tables.

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU conclusion;
paper-level benchmark result;
level3 self-identification;
direct recurrent-profile repair without result audit;
matched-budget training without design.
```

## Verification

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit.py
python -m compileall -q src/autodrift/paper_route_current_sim_recurrent_profile_checkpoint_quality_audit.py tests/test_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit.py
PYTHONPATH=src python -m autodrift.paper_route_current_sim_recurrent_profile_checkpoint_quality_audit --checkpoint-materialization-dir runs/m2171_paper_route_current_sim_checkpoint_profile_materialization --failure-metrics runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_failure_metric_summary.csv --output-dir runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit
```

## Next Step

M2225 should audit the M2224 result before any new training. The likely route is
matched-budget checkpoint training design for the controller-family profiles:
train the L3 recurrent profile to a quality floor comparable to the best
finite-window smoke profile, then rerun only after reset/readiness gates are
re-established.
