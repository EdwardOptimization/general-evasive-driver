# M2263 Paper-Route Current-Sim Midcourse Corridor-Containment Training Execution Result Audit

- status: completed
- decision: `current_sim_midcourse_corridor_containment_training_audit_route_to_selected_checkpoint_outcome_localization_design`
- manifest: `experiments/manifests/m2263-paper-route-current-sim-midcourse-corridor-containment-training-execution-result-audit.json`
- parent result: `runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/summary.json`

## Audit Result

M2262 is a clean training execution artifact:

```text
result_class: current_sim_training_stability_repair_execution_pass
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

It is not comparison-ready:

```text
selected_checkpoint_profile_floor_pass_count: 0
final_checkpoint_profile_floor_pass_count: 0
selected_readiness_floor_pass_count: 4/15
selected_beats_final_count: 11/15
```

Compared with the generic M2250 repair:

```text
M2250 selected return mean: 64.21352
M2262 selected return mean: 58.81669
M2250 selected termination mean: 0.43958
M2262 selected termination mean: 0.42083
```

So the targeted containment panel did not improve the training-readiness floor
or selected return, but it slightly reduced aggregate termination rate. This is
not enough to claim repair success because the target failure was a
midcourse/mild offtrack slice, not scalar return.

## Interpretation

M2262 answers only one question:

```text
The M2259 targeted containment config matrix is runnable and produces complete
candidate-checkpoint evidence.
```

It does not answer:

```text
whether mid_offtrack_delta <= 0
whether mild_overshoot_delta <= 0
whether global_offtrack_count < 110
whether collision_count <= 107
whether the repair changed offtrack into collision
```

Those are exactly the M2258 acceptance metrics, and they require an
M2244/M2253-style selected-checkpoint outcome localization run.

## Route Decision

Route to:

```text
m2264-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-design
```

M2264 should freeze a non-ranking localization protocol over the `15` M2262
selected checkpoints, using the same public `480`-episode shape used by M2244
and M2253. It should compare M2262 against M2244 as the base and M2253 as the
generic-repair reference, but only as repair-route evidence.

The localization must report at least:

```text
success/offtrack/collision/global deltas
mid_offtrack_delta
mild_overshoot_delta
safe-clearance offtrack delta
collision delta
max-step noncompletion count
profile/seed local regressions
```

## Blocked Routes

Blocked for now:

```text
another training run before localization
ranking profiles by selected return
accepting lower termination rate as repair success
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification claim
```

## Next

Pre-register:

```text
m2264-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-design
```
