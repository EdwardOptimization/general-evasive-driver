# M73 Active-Probing Warm-Up Harness

M72 proved that passive warm-up reveal is not enough. M73 adds safety-bounded
active probing during the obstacle-hidden phase and keeps the same
outcome-sensitive acceptance rule:

```text
strict visible match
normal history succeeds
wrong probing history lowers success or clearance margin
```

## Harness Update

`outcome_sensitive_corpus` now supports a probing warm-up before snapshot
collection:

```text
--probe-strategy none|steer_sine|brake_tap|steer_brake
--probe-steer-amplitude VALUE
--probe-brake-level VALUE
--probe-throttle-level VALUE
--probe-period-steps STEPS
--probe-until-step STEP
--probe-until-distance DISTANCE
```

The model recurrent hidden is still updated from deployable observations. During
probing steps the harness executes a small fixed action instead of the model's
chosen action; the next observation carries the actual executed action and
vehicle response, so the recurrent state can encode the probe-response evidence.

The harness records:

```text
active_probe_strategy
nominal_active_probe_steps
nominal_active_probe_steer_abs_mean
nominal_active_probe_brake_mean
perturbed_active_probe_steps
perturbed_active_probe_steer_abs_mean
perturbed_active_probe_brake_mean
```

## Tests

Focused tests cover:

- probe action bounds and pedal-level mapping;
- probing until obstacle reveal, step threshold, or distance threshold;
- summary probe-step aggregation.

Command:

```text
conda run -n autodrift pytest -q tests/test_outcome_sensitive_corpus.py
```

Result:

```text
9 passed
```

## Smoke Runs

All runs use the M67-E checkpoint and M72 obstacle reveal:

```text
--obstacle-perception-reveal-step 20
--obstacle-perception-reveal-distance 14
--target-obstacle-distances 8,10,12
```

### Mild Weak-Brake Probe

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7900 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --perturbed-randomization brake_scale_range=0.50,0.60 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 14 \
  --target-obstacle-distances 8,10,12 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.12 \
  --probe-brake-level 0.10 \
  --probe-period-steps 20 \
  --top-k 20 \
  --run-dir runs/m73_active_probe_brake_smoke_seed7900
```

| Metric | Value |
| --- | ---: |
| Candidates | 60 |
| Paired candidates | 54 |
| Accepted visible matches | 49 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.000881 |
| Mean probe steps | 22.72 |

### Mild Low-Friction Probe

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 8000 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 14 \
  --target-obstacle-distances 8,10,12 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.12 \
  --probe-brake-level 0.10 \
  --probe-period-steps 20 \
  --top-k 20 \
  --run-dir runs/m73_active_probe_friction_smoke_seed8000
```

| Metric | Value |
| --- | ---: |
| Candidates | 60 |
| Paired candidates | 57 |
| Accepted visible matches | 35 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.008426 |
| Mean probe steps | 20.39 |

### Strong Low-Friction Probe

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 8100 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 14 \
  --target-obstacle-distances 8,10,12 \
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
  --run-dir runs/m73_active_probe_strong_friction_smoke_seed8100
```

| Metric | Value |
| --- | ---: |
| Candidates | 60 |
| Paired candidates | 60 |
| Accepted visible matches | 41 |
| Accepted outcome-sensitive pairs | 0 |
| Margin-gap accept rows before final filters | 2 |
| Max margin gap | 0.040596 |
| Mean probe steps | 21.50 |

The strong probe creates the first large wrong-history margin gaps, but they are
not valid accepted snippets. The top rows either fail strict context matching or
have normal-history collision as well as wrong-history collision. Therefore they
do not prove useful self-identification.

### Relaxed Diagnostic

The same strong low-friction run was repeated with relaxed context and normal
margin filters:

```text
runs/m73_active_probe_strong_friction_relaxed_seed8100
```

Result:

| Metric | Value |
| --- | ---: |
| Accepted visible matches | 52 |
| Accepted outcome-sensitive pairs | 0 |
| Margin-gap accept rows before final filters | 2 |
| Max margin gap | 0.040596 |

Even with relaxed matching, the high-gap rows are collision-to-collision cases,
not normal-success/wrong-history-failure cases.

## Interpretation

M73 is an infrastructure pass and a mixed negative diagnostic.

What improved:

- active probing increases visible match rates versus passive warm-up;
- stronger low-friction probing creates real action-response/history sensitivity
  at the margin metric level.

What failed:

- no strict accepted outcome-sensitive snippets were found;
- the large margin gaps occur in cases where normal history already collides;
- the current policy was not trained to exploit probing history, so fixed
  probing mainly perturbs the state rather than creating a deployable
  self-identification behavior.

## Next Step

M74 should use the M73 near-miss evidence instead of broad random mining:

```text
active-probe outcome-bound scenario sweep
```

For high-gap active-probe seeds, sweep obstacle distance and width around the
same hidden dynamics and probing history, searching for cases where:

```text
normal probing history succeeds or has positive near-boundary margin
wrong probing history collides or loses >= 0.01 m margin
visible response/context distances remain strict
```

Only after that corpus exists should the project train a student objective on
active-probing history.
