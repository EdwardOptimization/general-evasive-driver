# M2241 Paper-Route Current-Sim Training-Stability Repair Execution

- status: completed
- decision: `current_sim_training_stability_repair_pass_but_readiness_still_below_floor_route_to_result_audit`
- manifest: `experiments/manifests/m2241-paper-route-current-sim-training-stability-repair-execution.json`
- command: `PYTHONPATH=src python -m autodrift.paper_route_current_sim_training_stability_repair_execution --output-dir runs/m2241_paper_route_current_sim_training_stability_repair_execution`
- summary: `runs/m2241_paper_route_current_sim_training_stability_repair_execution/summary.json`

## Execution Result

M2241 completed the same-budget candidate-checkpoint repair execution:

```text
result_class: current_sim_training_stability_repair_execution_pass
runtime_seconds: 319.6344526479952
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The execution kept the M2240 contract:

```text
profiles: 5
seeds: 3
total_steps: 32768
checkpoint_interval_steps: 4096
candidate steps: 4096..32768
actor input contract changed: false
private holdout used: false
```

## Readiness Result

Checkpoint selection improved many seed-level results, but did not make the
panel comparison-ready:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
selected_beats_final_count: 12/15
```

Profile aggregates from selected checkpoints:

| profile | selected passing seeds | final passing seeds | selected return mean | selected termination mean | selected beats final |
| --- | ---: | ---: | ---: | ---: | ---: |
| L0_current_masked | `1/3` | `1/3` | `49.5519` | `0.40625` | `3` |
| L1_one_step | `1/3` | `1/3` | `49.0116` | `0.42708` | `1` |
| L2_window_25 | `1/3` | `1/3` | `52.0459` | `0.40625` | `3` |
| L2_window_50 | `1/3` | `1/3` | `52.6299` | `0.39583` | `2` |
| L3_online_gru | `1/3` | `0/3` | `45.9477` | `0.47917` | `3` |

The most important positive signal is L3 seed `222602`: candidate selection
recovers a readiness-passing checkpoint at step `12288`, improving from final
return/termination `35.0936 / 0.75` to selected `67.1743 / 0.28125`.

The most important negative signal is route-level: no profile reaches the
pre-registered `2/3` seed readiness floor after selection.

## Interpretation

M2241 falsifies the narrow hypothesis that final-checkpoint late regression is
the only readiness blocker:

```text
selected checkpoints beat final in 12/15 rows,
but profile_floor_pass_count remains 0.
```

This supports a more specific route:

```text
checkpoint retention is useful and should remain in future training,
but reward/task/curriculum repair is still required.
```

M2241 does not rank profiles and does not support finite-window-vs-GRU or
self-identification claims.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution from selected M2241 checkpoints
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
```

## Next

Pre-register result audit:

```text
m2242-paper-route-current-sim-training-stability-repair-result-audit
```

The audit should decide whether the next route is reward/termination repair,
task/curriculum repair, or floor-calibration support analysis. It should not
run another training job before that route decision.
