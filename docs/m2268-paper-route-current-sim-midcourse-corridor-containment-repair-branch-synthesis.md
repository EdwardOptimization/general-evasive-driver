# M2268 Paper-Route Current-Sim Midcourse Corridor-Containment Repair Branch Synthesis

- status: completed
- synthesis decision: `continue`
- manifest: `experiments/manifests/m2268-paper-route-current-sim-midcourse-corridor-containment-repair-branch-synthesis.json`
- synthesis artifact: `docs/m2268-paper-route-current-sim-midcourse-corridor-containment-repair-branch-synthesis.md`
- synthesis window: `M2258-M2267`

## Evidence Summary

This branch tested a targeted repair after M2256/M2257 localized the generic
reward repair failure as:

```text
midcourse_mild_boundary_containment_regression
```

M2258 froze a targeted containment repair:

```text
track_cost_scale: 3.0
heading_cost_scale: 0.30
road_margin_cost_scale: 2.6
road_margin_warning_fraction: 0.50
off_track_penalty: 8.0
```

M2259 materialized `15` configs with target mismatch `0`, contract violation
`0`, track-width widening `0`, and guardrail violation `0`. M2262 trained the
panel cleanly:

```text
completed_run_count: 15
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 11/15
selected_checkpoint_profile_floor_pass_count: 0
```

M2265 localized selected-checkpoint outcomes:

```text
M2244 base: success/offtrack/collision/max-step = 277/110/93/0
M2253 generic repair: success/offtrack/collision/max-step = 269/118/93/0
M2265 targeted containment: success/offtrack/collision/max-step = 278/110/92/0
```

The core result is:

```text
targeted containment fixes the M2253 aggregate regression, but strict offtrack
improvement below M2244 is not proven.
```

## Supported Claims

- The targeted containment config, training, and localization pipeline is
  executable and guardrail clean.
- Targeted containment is materially better than the generic M2253 reward
  repair at aggregate outcome level.
- Aggregate outcome alone is insufficient because M2265 offtrack count equals
  M2244 (`110`), not below it.
- The next useful evidence is no-rerun slice diagnosis over existing episode
  rows, not another reward tweak or training run.

## Falsified Claims

- Falsified: the generic M2250/M2253 reward repair improved outcome mode.
- Still unsupported: targeted containment strictly repairs the M2256
  midcourse/mild slice.
- Still unsupported: selected return or termination movement is enough for
  repair success.
- Still blocked: controller-family ranking, finite-window-vs-GRU conclusion,
  paper-level result, and level3 self-identification claim.

## Failure Taxonomy Summary

Active failure types:

```text
objective_overfit
behavior_regression
scenario_sampling_failure
metric_artifact
seed_fragility
```

The branch reduced aggregate regression versus M2253, so this is no longer a
simple outcome-worse reward tweak. The unresolved issue is evidence granularity:
M2265 lacks the M2258-required `mid_offtrack` and `mild_overshoot` slice
deltas.

## Public Gate Overfit Risk

Risk is medium to high. The branch has already used the same public M2244/M2253
episode support repeatedly. Continuing with another reward or training tweak
would likely become local search. A no-rerun slice diagnosis is still justified
because it changes the evidence axis from aggregate outcome to failure slices.

## Next Branch Decision

Continue the branch exactly one step:

```text
m2269-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-implementation
```

M2269 may implement/run the no-rerun M2244/M2253/M2265 slice diagnosis designed
in M2267. It must:

```text
read existing episode rows only
use accurate panel labels baseline_m2244 targeted_m2265 generic_m2253
emit mid_offtrack and mild_overshoot deltas
emit generic-vs-targeted repair-delta evidence
keep ranking/paper/self-ID claims blocked
```

After M2269/M2270, if slice evidence still does not support targeted repair,
the branch should synthesize or pivot rather than try another scalar reward
adjustment.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another reward/training iteration before slice diagnosis
```

## Next

Pre-register:

```text
m2269-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-implementation
```
