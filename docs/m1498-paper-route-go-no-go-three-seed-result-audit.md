# M1498 Paper-Route Go/No-Go Three-Seed Result Audit

## Summary

M1498 audits the M1497 full 12-profile three-seed public pilot before any
further standard-profile scaling.

Decision:

```text
go_no_go_three_seed_audit_stop_standard_profile_scaling_pivot_to_decisive_history_tasks
```

This milestone does not train, run PPO, run replay, promote, use private
holdout, export corpus, change actor inputs, or claim profile superiority,
paper-level evidence, recurrent-belief advantage, or level3 self-identification.

## Completion Audit

M1497 completed its process objective:

```text
profile_count: 12
main_profile_count: 7
diagnostic_profile_count: 5
total_seed_runs: 36
completed_seed_runs: 36
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
```

So the result is a valid public trend pilot. It is not a promotion or
private-holdout result.

## Stop-Rule Evaluation

M1496 pre-registered this stop rule:

```text
If M1497 repeats both patterns:
1. L2 current-tiled controls remain close to L2 normal;
2. L3 online does not beat corrected reset-control;
then M1498 must stop standard profile-scaling and route to decisive T4/T5 task
evidence, L3 training-recipe repair, or a negative/conditional standard-profile
verdict.
```

M1497 repeats both patterns.

### L2 Normal Versus Current-Tiled

```text
L2_window_13 success:              0.166667
L2_window_13_current_tiled:        0.151042
success delta:                     0.015625

L2_window_25 success:              0.182292
L2_window_25_current_tiled:        0.130208
success delta:                     0.052083

L2_window_50 success:              0.182292
L2_window_50_current_tiled:        0.130208
success delta:                     0.052083

L2_window_100 success:             0.182292
L2_window_100_current_tiled:       0.130208
success delta:                     0.052083
```

For 25/50/100 windows, normal L2 is modestly better than current-tiled on
success and margin. The gap is not a decisive history-necessity result. For the
13-step window, current-tiled has higher mean margin while normal has only a
small success edge.

M1498 classification:

```text
finite_window_history_necessity_on_standard_profile: not_supported
current_frame_substitution_risk: high
```

### L3 Online Versus Corrected Reset

```text
L3_online_gru success/collision/margin:       0.286458 / 0.640625 / 0.480487
L3_reset_control success/collision/margin:    0.317708 / 0.604167 / 0.502408

online - reset success delta:                 -0.031250
online - reset collision delta:                0.036458
online - reset mean-margin delta:             -0.021921
```

L3 online does not beat corrected reset-control on success, collision, or mean
margin. Online has a slightly better p10 margin, but the aggregate trend does
not support recurrent hidden-state advantage.

M1498 classification:

```text
online_gru_hidden_advantage_on_standard_profile: not_supported
level3_self_identification_on_standard_profile: not_supported
```

## Synthesis

The standard fixed-budget profile branch has now produced enough evidence for a
branch decision:

```text
M1495 one-seed plumbing: completed, negative/non-conclusive trend.
M1496 audit: admitted exactly one three-seed public pilot with stop rule.
M1497 three-seed pilot: completed, repeated the stop-rule pattern.
```

Continuing to scale the same standard profile pilot would mostly test optimizer
variance and public-row tuning. It would not directly answer whether older
action-response history is necessary. The next paper-route evidence should
instead construct tasks where current frame and short recent windows are
insufficient by design.

M1498 therefore closes the standard profile-scaling branch and pivots to
decisive T4/T5 task evidence.

## Supported Claims

M1498 supports only these claims:

```text
1. The full 12-profile public matrix can run reproducibly across three seeds.
2. On the current standard profile distribution, L2 current-tiled controls
   remain close enough that finite-window history necessity is not supported.
3. On the current standard profile distribution, L3 online GRU does not beat
   corrected reset-control.
4. Further standard profile scaling is not the highest-leverage route for
   proving self-identification.
```

## Falsified Or Unsupported Claims

M1498 does not support:

```text
finite-window history is necessary on the standard profile distribution;
online GRU hidden state improves the standard profile distribution;
level3 recurrent self-identification has been demonstrated;
M1497 provides private-holdout or paper-level architecture ranking evidence.
```

## Failure Taxonomy

M1498 records the branch-level issue as:

```text
scenario_sampling_failure
```

The failure is not a runtime failure or contract violation. The standard profile
distribution does not create a strong enough need for older-history evidence to
separate current response, finite-window, and recurrent controllers.

## Next Route

Route to:

```text
m1499-paper-route-decisive-history-task-matrix-design
```

The next branch should design T4/T5 decisive tasks:

```text
T4: same-current, same-recent-window, different-older-history tasks.
T5: terminal-boundary near-constraint tasks where correct early belief changes
    final clearance or collision outcome.
```

This is preferred over immediate L3 recipe repair because the current standard
distribution has not shown that older-history information is required. Recipe
repair can return later if T4/T5 proves that the task demands history but L3
training fails to exploit it.

## Guardrails

```text
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
profile_specific_tuning: false
actor_input_contract_changed: false
training_corpus_exported: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
standard_profile_scaling_continues: false
next_branch: paper_route_decisive_history_task_matrix
```
