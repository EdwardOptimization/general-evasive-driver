# M2247 Paper-Route Current-Sim Task/Curriculum Readiness Branch Synthesis

- status: completed
- synthesis decision: `continue`
- manifest: `experiments/manifests/m2247-paper-route-current-sim-task-curriculum-readiness-branch-synthesis.json`
- synthesis window: `M2236-M2246`
- primary failure taxonomy: `scenario_sampling_failure`
- secondary failure taxonomy: `training_instability`
- reset/rollout/measured execution in M2247: `false`
- policy actions executed in M2247: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

The branch started after matched-budget short and medium profile training both
completed cleanly but failed readiness floors:

```text
short-v0 quality_floor_profile_pass_count: 0
medium-v1 quality_floor_profile_pass_count: 0
```

M2238 diagnosed this as more than undertraining:

```text
row_diagnosis_count: 30
training_plateau_row_count: 30
late_regression_row_count: 18
fail_to_pass transitions from short to medium: 0
```

M2241 checkpoint retention was useful but insufficient:

```text
completed runs: 15 / 15
candidate checkpoints: 120
selected checkpoints: 15
selected beats final: 12 / 15
selected_checkpoint_profile_floor_pass_count: 0
```

M2244 converted the blocker from unknown aggregate weakness into failure-mode
evidence:

```text
episodes: 480
success: 277 / 480
offtrack: 110 / 480
collision: 93 / 480
max-step noncompletion: 0 / 480
dominant failure mode: offtrack_dominated_failure
```

M2246 then designed a bounded repair route:

```text
do not widen track_width as primary repair
do not change actor input contract
add default-preserving road-margin/offtrack reward hooks
materialize a matched repaired 5-profile x 3-seed config matrix
keep collision/clearance as guardrail
```

## Supported Claims

Supported:

```text
The matched-budget training and candidate-checkpoint infrastructure is clean.
Another blind budget increase is not the right next step.
Checkpoint retention should remain in the recipe, but it is not sufficient.
The current selected checkpoints fail mainly through road containment.
The next useful repair mechanism is a bounded road-margin/offtrack reward extension.
```

## Falsified Claims

Falsified or blocked for this branch:

```text
Medium-v1 training alone makes the panel comparison-ready.
Best-checkpoint selection alone makes the panel comparison-ready.
The current selected-checkpoint panel can rank controller families.
The current selected-checkpoint panel can support a finite-window-vs-GRU verdict.
The current selected-checkpoint panel proves level3 self-identification.
```

Still unsupported:

```text
paper-level benchmark result
controller-family winner
private-holdout generalization
strong recurrent-belief advantage
high-fidelity validation readiness
```

## Failure Taxonomy Summary

```text
training_instability:
  late regression appears in 18/30 traces and checkpoint retention helps 12/15 rows.

scenario_sampling_failure:
  the selected-checkpoint panel is still below readiness and offtrack dominated.

seed_fragility:
  profile-seed rows vary strongly; several rows are success-supported but the
  route-level 2/3 profile floor is not met.

metric_artifact:
  avoided in this branch by keeping diagnostic-only flags and blocking ranking.
```

## Public Gate Overfit Risk

Risk is medium:

```text
The branch uses public seeds and public selected-checkpoint localization.
The offtrack repair target is derived from a fixed panel.
Repeated local tuning on these rows would overfit the panel.
The repair must therefore materialize one bounded shared recipe, not a
profile-specific or row-specific patch.
```

Mitigation:

```text
keep the 5-profile x 3-seed matrix matched
preserve old reward behavior by default
track collision as a guardrail
require later execution to improve global outcome, not just selected rows
run another synthesis if reward-extension materialization or execution fails
```

## Next Branch Decision

Selected:

```text
continue:
  paper_route_current_sim_task_curriculum_readiness_diagnosis
```

The branch can continue because M2246 produced a concrete new repair mechanism
instead of another local checkpoint or budget loop. The next milestone must be
infrastructure/materialization only:

```text
m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization
```

M2248 should implement the default-preserving road-containment reward hooks and
materialize the matched repaired config matrix. It must not train, run rollout,
rank profiles, select a winner, use private holdout, claim paper-level evidence,
claim a finite-window-vs-GRU verdict, or claim level3 self-identification.
