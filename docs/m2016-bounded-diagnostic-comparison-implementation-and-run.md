# M2016 Bounded Diagnostic Comparison Implementation And Run

- status: completed
- decision: `bounded_diagnostic_comparison_pass_route_to_result_audit`
- result class: `bounded_diagnostic_comparison_pass`
- implementation: `src/autodrift/bounded_diagnostic_comparison.py`
- focused tests: `2 passed`
- compileall: `passed`
- summary: `runs/m2016_bounded_diagnostic_comparison/summary.json`
- selected candidate: `success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible`
- environment reset/rollout in M2016: `false`
- policy action execution in M2016: `false`
- measured rollout in M2016: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_bounded_diagnostic_comparison.py
```

Result:

```text
2 passed
```

No-rerun diagnostic comparison:

```bash
PYTHONPATH=src python -m autodrift.bounded_diagnostic_comparison \
  --admitted-candidates runs/m2014_bounded_comparison_candidate_qualification/admitted_candidates.csv \
  --episode-rows runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv \
  --output-dir runs/m2016_bounded_diagnostic_comparison \
  --next-blocker m2017-bounded-diagnostic-comparison-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

M2016 passes:

```text
result_class: bounded_diagnostic_comparison_pass
admitted_candidate_count: 1
matched_episode_count: 60
profile_row_count: 12
profile_group_row_count: 4
guardrail_violation_count: 0
```

No environment or actor execution occurred:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Profile Group Diagnostic

The admitted stable-AES slice contains all profile groups:

```text
L0:  4 / 5 success, collision 1 / 5, offtrack 0 / 5
L1:  3 / 5 success, collision 0 / 5, offtrack 2 / 5
L2:  0 / 40 success, collision 1 / 40, offtrack 39 / 40
L3: 10 / 10 success, collision 0 / 10, offtrack 0 / 10
```

Profile-level highlights:

```text
L3_online_gru: 5 / 5 success
L3_reset_control_corrected: 5 / 5 success
L0_current_masked: 4 / 5 success
L1_one_step: 3 / 5 success
all L2 profiles: 0 success
```

This is a useful diagnostic table. It is not a finite-window-vs-GRU conclusion:
the evidence is one public stable-AES slice with no private holdout and no
source-diverse repetition.

## Claim Boundary

Allowed claim:

```text
M2016 completed a no-rerun bounded diagnostic comparison on one admitted
stable-AES public slice.
```

Forbidden claims:

```text
controller-family ranking
finite-window-vs-GRU conclusion
paper-level benchmark result
level3 self-identification
```

## Next

Next milestone:

```text
m2017-bounded-diagnostic-comparison-result-audit
```

M2017 should decide whether to:

```text
design a source-diverse bounded comparison expansion,
route to task-quality support repair,
or synthesize/stop this singleton diagnostic branch.
```
