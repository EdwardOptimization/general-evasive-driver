# M2225 Paper-Route Current-Sim Recurrent Profile Checkpoint Quality Result Audit

- status: completed
- decision: `current_sim_checkpoint_quality_audit_route_to_matched_budget_training_design`
- manifest: `experiments/manifests/m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit.json`
- parent result: `runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/summary.json`
- reset in M2225: `false`
- measured execution in M2225: `false`
- policy action executed in M2225: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2224 is complete and claim-safe:

```text
result_class: current_sim_recurrent_profile_checkpoint_quality_audit_pass
profile_count: 8
join_row_count: 8
l3_online_total_train_steps: 1024
l3_online_eval_termination_rate: 0.6
l3_online_final_train_termination_rate: 1.0
l3_online_weak_eval_flag: true
l3_online_weak_train_flag: true
l3_online_diagnostic_success_count: 0
l3_reset_aliases_online_checkpoint: true
l3_reset_diagnostic_success_count: 0
l2_window_25_diagnostic_success_count: 360
l3_weak_checkpoint_plausible: true
matched_budget_training_needed: true
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

The claim boundary is clean: M2224 blocks controller-family ranking, winner
selection, finite-window-vs-GRU conclusion, paper-level benchmark result, and
level3 self-identification.

## Decision

M2225 admits a matched-budget training design branch.

The route is not:

```text
directly retrain only L3;
directly rerun M2209;
declare finite-window superior;
declare GRU/self-ID negative;
promote any checkpoint.
```

The route is:

```text
design a fair controller-family training matrix with matched budgets, seeds,
reward/task distribution, input contract, quality floors, and admission gates.
```

The reason is straightforward: the current L3 recurrent checkpoint is too weak
and too smoke-scale to support any finite-window-vs-GRU verdict. Because
`L3_reset_control` intentionally aliases the same weak online checkpoint,
M2221/M2224 zero-success is a checkpoint-quality blocker before it is a
controller-family comparison result.

## Design Requirements For M2226

M2226 should freeze a training-design document, not run training.

It should specify:

```text
profile set:
  L0_current_masked
  L1_one_step
  L2_window_25
  L2_window_50
  L3_online_gru
  L3_reset_control as alias/eval control only
  optionally L2_window_13 and L2_window_100 as diagnostic side profiles

budget fairness:
  same total environment steps by trained profile;
  same seed count and seed policy;
  same train/eval scenario distribution;
  same reward and termination configuration;
  no profile-specific tuning after seeing comparison results.

quality admission:
  per-profile training completes;
  checkpoint paths exist;
  eval termination and return clear minimum floors;
  L3 checkpoint is not admitted if it remains obviously smoke-weak;
  reset-control alias is regenerated from the admitted L3 checkpoint.

post-training route:
  materialize checkpoints;
  run no-rollout contract/readiness checks;
  run reset/runtime smoke before measured execution;
  only then design measured rerun.
```

The design must remain consistent with the paper-route plans:

```text
finite-window may win;
GRU is not assumed to be final;
matched L0/L1/L2/L3 evidence is required before ranking;
self-ID claims require later history-intervention evidence.
```

## Next Step

M2226 should write the matched-budget profile training design. It should not
train, reset, rollout, rank, or make paper/self-ID claims.
