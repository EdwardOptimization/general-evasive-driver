# M2272 Paper-Route Current-Sim Task-Quality Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- manifest: `experiments/manifests/m2272-paper-route-current-sim-task-quality-branch-synthesis.json`
- synthesis artifact: `docs/m2272-paper-route-current-sim-task-quality-branch-synthesis.md`
- synthesis window: `M2236-M2271`

## Evidence Summary

This branch asked whether the current-sim profile panel could become
comparison-ready through fair matched-budget training, checkpoint selection, and
bounded task/reward repair.

The main evidence is:

```text
M2236:
  short-v0 and medium-v1 matched-budget training both complete cleanly, but
  quality_floor_profile_pass_count remains 0.

M2238-M2239:
  artifact-only readiness diagnosis rejects another blind budget increase and
  routes to training-stability/task-curriculum repair.

M2241-M2244:
  same-budget candidate checkpoint selection is useful, but selected-checkpoint
  outcome localization remains offtrack dominated:
    M2244 success/offtrack/collision = 277/110/93.

M2250-M2257:
  generic road-margin/offtrack reward repair improves return but worsens
  outcome distribution:
    M2253 success/offtrack/collision = 269/118/93.
  M2256 localizes the regression to midcourse/mild boundary containment:
    mid_offtrack +14, mild_overshoot +11.

M2258-M2270:
  targeted containment repair recovers the intended slices and beats M2253:
    M2265 success/offtrack/collision = 278/110/92.
    generic_vs_targeted offtrack_delta = -8.
    mid_offtrack_delta_vs_M2244 = -8.
    mild_overshoot_delta_vs_M2244 = -2.
  But it remains aggregate-neutral on global offtrack versus M2244:
    110 -> 110.
```

## Supported Claims

- The current-sim research harness is able to execute fair profile/seed panels,
  candidate checkpoint selection, outcome localization, no-rerun slice
  diagnosis, branch synthesis, and process validation.
- Candidate checkpoint selection improves over final checkpoints and should
  remain part of future current-sim evaluation.
- Scalar training return and termination metrics are insufficient safety
  proxies; M2253 improved return while worsening offtrack.
- Generic offtrack/recovery/corridor scalar repair is not enough.
- Targeted midcourse containment repair is more precise than generic repair and
  recovers the diagnosed M2256 slices.
- The current blocker is task/scenario quality and role-specific metric design,
  not simply another PPO budget or another scalar road-margin reward tweak.

## Falsified Claims

- Falsified: short-v0 or medium-v1 matched-budget training makes the profile
  panel comparison-ready under the registered readiness floor.
- Falsified: blind budget escalation is a sufficient strategy.
- Falsified: selected return improvement implies safety-outcome improvement.
- Falsified: generic road-margin/offtrack scalar repair fixes the current-sim
  outcome blocker.
- Not proven: targeted containment is a strict global offtrack repair versus
  M2244.
- Not proven: the current-sim profile panel supports controller-family ranking,
  finite-window-vs-GRU conclusions, paper-level claims, or level3
  self-identification.

## Failure Taxonomy Summary

Primary active failures:

```text
scenario_sampling_failure
objective_overfit
metric_artifact
seed_fragility
training_instability
```

Interpretation:

- `scenario_sampling_failure`: the public task mix remains offtrack dominated
  and does not yet separate role-specific driver capabilities cleanly.
- `objective_overfit`: scalar reward/return moved without reliable outcome
  improvement.
- `metric_artifact`: readiness floors and returns alone can misrepresent
  current-sim task quality.
- `seed_fragility`: no profile reached the pre-registered `2/3` seed readiness
  floor.
- `training_instability`: longer budget and checkpoint selection help locally
  but do not make the panel robust.

## Public Gate Overfit Risk

Risk is high if the branch continues as another local reward repair. The public
M2244/M2253/M2265 rows have already been used for:

```text
outcome localization
generic reward repair
failure-slice diagnosis
targeted containment repair
slice recovery audit
```

Continuing to tune scalar reward values on this same support would likely
optimize the known public rows instead of producing a stronger current-sim
benchmark. The next branch must change the evidence axis.

## Paper-Route Axis Classification

```text
engineering driver performance:
  partial. The selected-checkpoint panel has nontrivial success, and targeted
  containment recovers slices, but readiness floors remain below comparison
  standard.

mechanism evidence for history dependence:
  no new support. This branch does not run wrong-history, reset-hidden, or
  finite-window-vs-GRU tests.

scenario/task-quality evidence:
  strong negative/diagnostic. The current task mix and scalar rewards are not
  yet adequate for controller-family comparison.

high-fidelity validation readiness:
  not ready. Current-sim verdict and benchmark pack are not frozen.

workflow or complexity reduction:
  positive. The branch stops local reward search and routes to a broader
  task-quality redesign.
```

## Next Branch Decision

Decision:

```text
pivot
```

New branch:

```text
paper_route_current_sim_scenario_task_quality_redesign
```

Next milestone:

```text
m2273-paper-route-current-sim-scenario-task-quality-redesign-design
```

M2273 should design a new evidence axis before any more training:

```text
role-specific scenario/task families
role-specific metrics and readiness floors
failure-mode taxonomy tied to AES/stable/drift/mitigation roles
public-vs-future-holdout policy
artifact-only support audit before new rollouts
acceptance criteria for comparison readiness
```

The branch should not start by changing reward scalars. It should first define
what task distribution and role-specific outcomes are needed for a paper-grade
current-sim benchmark pack.

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
another scalar reward tweak before scenario/task-quality redesign
high-fidelity validation as a primary route
```

## Next

Pre-register:

```text
m2273-paper-route-current-sim-scenario-task-quality-redesign-design
```
