# M983 V4 Public Base Post Repair Surface Refresh Synthesis

## Evidence Summary

M979-M982 tested whether the newly promoted M974 public-gate base exposes a
fresh, source-diverse wrong-history outcome-sensitive surface before any more
PPO continuation.

Results:

```text
M979: designed no-PPO post-repair surface refresh.
M980: found 30 accepted wrong-history rows, but all from one OOD left seed.
M981: expanded fresh/OOD seeds and found zero accepted rows.
M982: returned to the M980 OOD range with higher candidate coverage and again found the same 30 rows only.
```

The important quantitative line is:

| Milestone | Candidate rows | Accepted rows | Left seeds | Physical pairs | Conclusion |
| --- | ---: | ---: | ---: | ---: | --- |
| M980 | 12000 | 30 | 1 | 2 | narrow positive |
| M981 | 30000 | 0 | 0 | 0 | expanded seeds do not reproduce pocket |
| M982 | 24000 | 30 | 1 | 2 | candidate coverage does not expand pocket |

## Supported Claims

The M974 public-gate base has at least one real wrong-history outcome-sensitive
OOD pocket. It is not just an action-level artifact: in M980/M982, wrong-history
continuations collide while normal-history continuations pass.

The pocket is deterministic enough to reproduce when the same OOD seed family is
mined again with higher candidate coverage.

The current fresh/OOD public scenario family is not sufficient to produce a
source-diverse proof corpus under the pre-registered thresholds.

## Falsified Claims

The M980 pocket is not a source-diverse proof surface.

The M980 source narrowness was not mainly caused by the M980 candidate-pair cap.
M982 increased candidate coverage and still found the same isolated source
shape.

Ordinary expanded seed mining in the same fresh/OOD config family is not enough.
M981 produced strong action separation but no wrong-history outcome degradation.

## Failure Taxonomy Summary

Primary taxonomy:

```text
scenario_sampling_failure
```

This is not a training failure, actor-input contract failure, or PPO washout.
The current sampling family has too little outcome-sensitive wrong-history
coverage for a durable corpus.

## Public Gate Overfit Risk

Public-gate overfit risk remains `moderate` for the M974 public-gate base.

The result is not a regression in the base checkpoint. It is a limitation of the
current proof-surface evidence. The project should avoid converting the isolated
M980/M982 pocket into another fixed public row target.

## Next Branch Decision

Decision:

```text
pivot
```

Open a new branch:

```text
v4_public_base_extreme_scenario_family_generation
```

The next branch should generate richer scenario families before mining again.
Use currently supported hidden simulator knobs first:

```text
mu_range
friction_step.mu_range / step_range
mass_scale_range
cg_shift_range
inertia_scale_range
tire_stiffness_scale_range
drive_scale_range
brake_scale_range
actuator_tau_scale_range
obstacle distance / width / label filters
speed_range
```

Planned families:

```text
low_mu_drop
brake_authority_loss
lateral_authority_loss
heavy_cg_delay
high_speed_close_obstacle
```

Current simulator boundary:

```text
The single-track model can approximate global tire/brake/drive/actuator failures.
It cannot yet represent split-mu, individual tire puncture, half-shaft breakage,
or corner-specific brake loss without a dynamics extension.
```

The next implementation milestone should create those configs and run a small
no-PPO config/sampling smoke before full source mining.
