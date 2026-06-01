# M2254 Paper-Route Current-Sim Offtrack/Recovery/Corridor Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- manifest: `experiments/manifests/m2254-paper-route-current-sim-offtrack-recovery-corridor-branch-synthesis.json`
- synthesis artifact: `docs/m2254-paper-route-current-sim-offtrack-recovery-corridor-branch-synthesis.md`
- synthesis window: `M2246-M2253`

## Evidence Summary

This branch tested a bounded offtrack/recovery/corridor reward repair after
M2244 localized the selected-checkpoint panel as offtrack dominated:

```text
M2244 baseline selected panel:
  success: 277/480
  offtrack: 110/480
  collision: 93/480
  max-step noncompletion: 0/480
```

M2246 designed a default-preserving road-margin/offtrack reward extension.
M2248 materialized the repaired 5-profile x 3-seed matrix. M2250 trained it
cleanly:

```text
completed_run_count: 15
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 15/15
selected_checkpoint_profile_floor_pass_count: 0
```

M2250 improved selected aggregate return for all five profiles, but M2253
showed that the outcome distribution did not improve:

```text
M2253 repaired selected panel:
  success: 269/480
  offtrack: 118/480
  collision: 93/480
  max-step noncompletion: 0/480
  mean return delta vs M2244: +14.37612
```

The core result is:

```text
return improved, but offtrack got worse and collision stayed unchanged.
```

## Supported Claims

- The repaired reward hooks and matrix execution infrastructure are clean.
- Candidate-checkpoint selection remains valuable.
- Scalar return can improve while actual safety outcome gets worse.
- The current selected-checkpoint failure mode remains globally offtrack
  dominated.
- A simple bounded road-margin/offtrack scalar reward repair is insufficient
  for comparison-ready current-sim driving.

## Falsified Claims

- Falsified: the M2248 reward extension repairs the offtrack blocker.
- Falsified: selected return improvement is enough to infer task repair.
- Falsified: another identical repaired training run is justified before new
  evidence.
- Still unsupported: any controller-family ranking, finite-window-vs-GRU
  conclusion, paper-level result, or level3 self-identification claim.

## Failure Taxonomy Summary

Primary failure type:

```text
objective_overfit
```

Reason: the objective improved scalar return without improving the intended
outcome distribution.

Secondary failure types:

```text
scenario_sampling_failure
training_instability
behavior_regression
seed_fragility
metric_artifact
```

These remain active because the weak profile-seed rows still fail mainly
through offtrack, while `L3_online_gru` also has a collision-dominated local
row.

## Public Gate Overfit Risk

Risk is high. The branch already includes:

```text
M2244 outcome localization
M2246 reward design
M2248 materialization
M2250 repaired training
M2253 repaired outcome localization
```

Continuing with another similar reward tweak would likely optimize the local
public panel rather than answer a new scientific question. The next branch must
change evidence axis.

## Next Branch Decision

Pivot to:

```text
paper_route_current_sim_offtrack_failure_slice_diagnosis
```

Next task:

```text
m2255-paper-route-current-sim-offtrack-failure-slice-diagnosis-design
```

The new branch should use existing M2244 and M2253 episode rows before any new
training. It should identify which failure slices worsened:

```text
early offtrack vs late offtrack
offtrack overshoot severity
clearance-negative collision-adjacent failures
profile/seed-specific failure roles
L3 collision-dominated local row
high-sideslip and recovery timing
```

Only after that slice diagnosis should the project choose between:

```text
stronger recovery/corridor curriculum
termination/recovery objective redesign
collision/clearance guardrail repair
task distribution redesign
stopping this current-sim repair branch
```

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
another blind budget escalation
another similar reward-extension run before slice diagnosis
```

## Next

Pre-register:

```text
m2255-paper-route-current-sim-offtrack-failure-slice-diagnosis-design
```
