# M72 Pre-Emergency Warm-Up History Harness

M71 showed that passive matched snapshots still do not produce causal
wrong-history outcome gaps. M72 starts the next proof surface: let the recurrent
driver collect action-response evidence before the obstacle becomes visible.

## Goal

Create a gate where the policy has a warm-up phase with randomized hidden
dynamics, then enters an emergency avoidance phase. The deployable actor must
still see only human-view inputs.

Target comparison:

```text
normal warm-up history
wrong matched warm-up history
reset history
zero action history
zero response history
```

Pass evidence should be outcome-level:

```text
normal history success or clearance margin
  >
wrong/reset/zero-history success or clearance margin
```

under strict visible-state matching.

## M72-A: Obstacle Perception Reveal Infrastructure

Added obstacle perception reveal controls to `ObstacleTaskConfig`:

```text
perception_reveal_step
perception_reveal_distance
```

Behavior:

- the obstacle still exists physically from reset;
- collision, clearance, scenario labels, and logging remain available;
- actor obstacle slots stay zero until the reveal conditions pass;
- observation dimension and slot layout remain unchanged.

This supports a controlled warm-up phase without changing the actor contract.
The driver can experience vehicle response first, then see the obstacle later.

M72-B also wired these controls into `outcome_sensitive_corpus`:

```text
--obstacle-perception-reveal-step STEP
--obstacle-perception-reveal-distance DISTANCE
```

This lets the M71 outcome-sensitive miner run warm-up reveal gates without a
separate config file.

## Tests

Focused tests cover:

```text
obstacle slots are hidden before reveal
step and distance reveal conditions work
config loader accepts reveal fields
existing obstacle observation behavior remains visible by default
```

Validation command:

```text
conda run -n autodrift pytest -q tests/test_env.py tests/test_config.py
```

Result:

```text
33 passed
```

Additional M72-B validation:

```text
conda run -n autodrift pytest -q \
  tests/test_outcome_sensitive_corpus.py tests/test_env.py tests/test_config.py
```

Result:

```text
40 passed
```

## Warm-Up Reveal Smoke

Both smoke runs hide obstacle slots until at least step `20` and until obstacle
longitudinal distance is at most `14 m`. Snapshots are collected after reveal at
`8,10,12 m`.

### Weak-Brake Warm-Up Reveal

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7700 \
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
  --top-k 20 \
  --run-dir runs/m72_warmup_reveal_brake_smoke_seed7700
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 60 |
| Paired candidates | 60 |
| Accepted visible matches | 33 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.008442 |

### Low-Friction Warm-Up Reveal

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7800 \
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
  --top-k 20 \
  --run-dir runs/m72_warmup_reveal_friction_smoke_seed7800
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 60 |
| Paired candidates | 57 |
| Accepted visible matches | 7 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.007695 |

## Interpretation

M72 is an infrastructure pass and a negative smoke result.

The reveal mechanism creates the intended observation sequence, but the current
policy still does not show causal dependence on warm-up recurrent history:

- weak-brake warm-up reveal has many visible matches, but max wrong-history
  margin gap remains below the 1 cm acceptance threshold;
- low-friction warm-up reveal has few strict visible matches and also stays
  below threshold;
- normal margins for the highest-gap rows are still not near-boundary.

This means passive warm-up is still insufficient. The next proof surface should
add active but safety-bounded identification actions during warm-up, or train a
policy/objective that makes warm-up response history action-relevant.

## Next Step

Build M73:

```text
active-probing warm-up harness
small steer/brake/throttle excitation under safety cost
wrong matched probing history intervention
outcome-sensitive acceptance after obstacle reveal
```

The probing sequence must remain deployable. Hidden parameters can only be used
for pairing, labels, diagnostics, or teacher-only training targets.
