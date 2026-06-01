# M2235 Paper-Route Current-Sim Matched-Budget Medium Training Execution Result Audit

- status: completed
- decision: `current_sim_medium_training_below_floor_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2235-paper-route-current-sim-matched-budget-medium-training-execution-result-audit.json`
- parent result: `runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/summary.json`
- parent aggregate: `runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution/profile_aggregate.csv`

## Audit Result

M2234 is a clean execution result:

- result_class: `current_sim_matched_budget_profile_training_execution_pass`
- expected_total_steps: `32768`
- completed_run_count: `15`
- failed_run_count: `0`
- all_selected_metrics_finite: `true`
- budget_signature_count: `1`
- budget_matched: `true`
- contract_violation_count: `0`
- config_budget_violation_count: `0`
- guardrail_violation_count: `0`
- private_holdout_used: `false`
- profile_specific_tuning: `false`
- winner_selected: `false`
- ranking_admissible_count: `0`

M2234 is still not comparison-ready:

- quality_floor_profile_pass_count: `0`
- every profile remains below the pre-registered `2/3` seed readiness floor.
- downstream measured execution remains blocked.
- controller-family ranking remains blocked.
- finite-window-vs-GRU conclusion remains blocked.
- self-identification claims remain blocked.

## Short-v0 vs Medium-v1

This audit does not rank profiles. It compares only the route-level readiness
state:

| item | M2230 short-v0 | M2234 medium-v1 |
| --- | ---: | ---: |
| total steps per seed | `8192` | `32768` |
| completed runs | `15/15` | `15/15` |
| failed runs | `0` | `0` |
| finite metrics | `true` | `true` |
| contract violations | `0` | `0` |
| quality_floor_profile_pass_count | `0` | `0` |

Medium-v1 improved some aggregate returns and termination rates, but it did not
change the route-level decision: the current profile panel is still below the
readiness floor.

## Classification

This is repeated training-readiness floor failure, not an implementation
failure:

```text
short-v0 and medium-v1 both execute cleanly,
but neither produces comparison-ready checkpoints under the registered floor.
```

Blindly increasing the budget again would now be local search. The next step
should synthesize the matched-budget branch and choose a new evidence axis,
most likely task/curriculum/reward/readiness diagnosis.

## Decision

Route to branch synthesis:

```text
m2236-paper-route-current-sim-matched-budget-training-branch-synthesis
```

The synthesis should decide whether to pivot to:

- task/curriculum readiness diagnosis;
- reward/termination/floor calibration audit;
- targeted training recipe repair;
- or a stop/negative-result record for this profile-training panel.

## Blocked Claims

M2235 does not admit:

```text
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
measured execution from M2234 checkpoints
private holdout
another blind budget escalation
```

## Next

Pre-register:

```text
m2236-paper-route-current-sim-matched-budget-training-branch-synthesis
```
