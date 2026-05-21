# M74 Active-Probe Outcome-Bound Scenario Sweep

M73 created the first large wrong-history margin gaps under strong active
probing, but the high-gap rows were invalid: normal history already collided or
strict context matching failed. M74 tests whether obstacle geometry can be swept
around those near misses to create valid cases:

```text
normal probing history succeeds or has positive near-boundary margin
wrong probing history collides or loses >= 0.01 m margin
strict visible response/context matching still passes
```

## Candidate Seeds

Saved near-miss seeds:

```text
experiments/m74_active_probe_near_miss_seeds.csv
```

Seeds:

| Seed | Source |
| ---: | --- |
| 8108 | strongest M73 strong-probe low-friction margin-gap near miss |
| 8119 | second M73 strong-probe low-friction margin-gap near miss |
| 8110 | third M73 strong-probe low-friction margin-gap near miss |

## Sweep Commands

All sweeps use:

```text
--seed-csv experiments/m74_active_probe_near_miss_seeds.csv
--nominal-friction-mu-range 0.85,1.15
--perturbed-friction-mu-range 0.25,0.35
--probe-strategy steer_brake
--probe-steer-amplitude 0.25
--probe-brake-level 0.20
--probe-period-steps 20
--min-margin-gap 0.01
--max-normal-margin 0.20
```

### Easier Geometry

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m74_active_probe_near_miss_seeds.csv \
  --seed 8200 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-distance-range 12,25 \
  --obstacle-half-width-range 0.45,0.80 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 16 \
  --target-obstacle-distances 8,10,12,14 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.35 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.25 \
  --probe-brake-level 0.20 \
  --probe-period-steps 20 \
  --top-k 20 \
  --run-dir runs/m74_active_probe_sweep_easy_friction_seed8200
```

### Medium Geometry

```text
runs/m74_active_probe_sweep_medium_friction_seed8201
```

Changes:

```text
--obstacle-distance-range 8,18
--obstacle-half-width-range 0.80,1.20
```

### Hard Geometry

```text
runs/m74_active_probe_sweep_hard_friction_seed8202
```

Changes:

```text
--obstacle-distance-range 3,12
--obstacle-half-width-range 0.80,1.20
--target-obstacle-distances 6,8,10,12
```

### Default Geometry With Dense Target Distances

```text
runs/m74_active_probe_sweep_default_friction_seed8203
```

Changes:

```text
default obstacle distance / width ranges
--target-obstacle-distances 6,7,8,9,10,11,12
```

## Results

| Sweep | Candidates | Visible Matches | Margin-Gap Rows | Accepted Outcome-Sensitive | Max Margin Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| easy | 12 | 8 | 0 | 0 | 0.001431 |
| medium | 12 | 10 | 0 | 0 | 0.002826 |
| hard | 12 | 11 | 0 | 0 | 0.001620 |
| default dense target | 21 | 4 | 7 | 0 | 0.045526 |

The default dense-target sweep reproduces and slightly increases the M73 signal,
but the high-gap rows remain invalid:

- strict visible rows have only millimeter-scale gaps;
- high-gap rows fail context matching;
- perturbed normal history is already a collision, so the wrong-history
  collision is not a valid degradation proof.

## Interpretation

M74 is negative.

Sweeping obstacle geometry through reset-level env configuration is not enough.
Changing the obstacle sampling range changes the whole rollout and often removes
the high-gap active-probe history. Keeping the original geometry preserves the
gap, but the valid strict-visible rows remain collision-to-collision or too weak.

The failure is useful: the next sweep should not resample the whole environment.
It should mutate obstacle geometry at the snapshot level while preserving the
same ego state, hidden state, and probing history.

## Next Step

M75 should build a snapshot-level obstacle relocation sweep:

```text
collect an active-probe snapshot
deep-copy the same env/history
move only obstacle position and half-width in the copied env
replay normal and wrong probing histories
search for normal-success / wrong-history-loss boundary cases
```

This directly tests the missing condition without destroying the active-probe
history that created the M73 margin gap.
