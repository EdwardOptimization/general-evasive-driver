# M71 Outcome-Sensitive Matched Scenario Constructor

M70 showed that wrong-history first-action differences are not enough. M71 adds
a stricter corpus miner:

```text
visible state must match
normal history must succeed
wrong history must reduce success or clearance margin
```

The point is to reject first-action-only snippets and keep only cases that can
support a causal self-identification claim.

## Harness

New module:

```text
python -m autodrift.outcome_sensitive_corpus
```

Artifacts:

```text
outcome_candidates.csv
replays.csv
outcome_sensitive_snippets.csv
summary.csv
summary.json
manifest.json
```

The harness reuses the M68/M70 snapshot and continuation machinery, but changes
the acceptance rule:

- match only the first 72 deployable human-view observation values;
- split visible distance into response and context terms;
- replay normal history and wrong matched history for both nominal and
  perturbed source conditions;
- accept only if wrong history causes a success drop or
  `normal_margin - wrong_history_margin >= min_margin_gap`;
- optionally require the normal-history margin to be inside a near-boundary
  window.

M71 also adds CLI overrides for obstacle geometry:

```text
--obstacle-distance-range LOW,HIGH
--obstacle-half-width-range LOW,HIGH
```

This is important because simply changing the decision snapshot distance does
not make the sampled obstacle itself near-boundary. Tight obstacle settings may
fail scenario sampling; M71 records those rows as missing/error candidates
instead of aborting the run.

## Smoke Runs

### Weak-Brake Baseline Geometry

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7300 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --perturbed-randomization brake_scale_range=0.50,0.60 \
  --target-obstacle-distances 6,8,10,12 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --top-k 20 \
  --run-dir runs/m71_outcome_sensitive_brake_smoke_seed7300
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 80 |
| Paired candidates | 80 |
| Accepted visible matches | 35 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.003190 |

### Low-Friction Baseline Geometry

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7400 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --target-obstacle-distances 6,8,10,12 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --top-k 20 \
  --run-dir runs/m71_outcome_sensitive_friction_smoke_seed7400
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 80 |
| Paired candidates | 80 |
| Accepted visible matches | 7 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.013007 |

The max margin gap clears 1 cm, but the row is not a valid strict visible match
and normal margins are not near-boundary enough for the M71 acceptance rule.

### Tight Weak-Brake Geometry

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7500 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --perturbed-randomization brake_scale_range=0.50,0.60 \
  --obstacle-distance-range 3,12 \
  --obstacle-half-width-range 1.30,2.00 \
  --target-obstacle-distances 4,6,8,10 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --top-k 20 \
  --run-dir runs/m71_outcome_sensitive_tight_brake_smoke_seed7500
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 80 |
| Paired candidates | 16 |
| Accepted visible matches | 13 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.000169 |

### Tight Low-Friction Geometry

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 20 \
  --seed 7600 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-distance-range 3,12 \
  --obstacle-half-width-range 1.30,2.00 \
  --target-obstacle-distances 4,6,8,10 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --top-k 20 \
  --run-dir runs/m71_outcome_sensitive_tight_friction_smoke_seed7600
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 80 |
| Paired candidates | 28 |
| Accepted visible matches | 5 |
| Accepted outcome-sensitive pairs | 0 |
| Max margin gap | 0.005372 |

## Interpretation

M71 is an infrastructure pass and another negative diagnostic.

The new harness now asks the right question, but the current M67-E teacher/policy
and passive snapshot collection still do not produce strict outcome-sensitive
wrong-history cases:

- baseline weak-brake has many visible matches but margin gaps are millimeter
  scale;
- baseline low-friction can produce a 1 cm margin gap, but not under strict
  visible matching and near-boundary constraints;
- tight obstacle geometry reduces sampleability and does not amplify
  wrong-history outcome damage;
- no smoke run produced an accepted `outcome_sensitive_snippets.csv` row.

This means the next step should not be student OSI distillation yet. There is
still no causal corpus showing that wrong matched history worsens outcome.

## Next Step

Move to a task that creates response evidence before the emergency, not only a
passive matched snapshot:

```text
M72 pre-emergency warm-up / active-probing scenario harness
```

The next harness should let the policy accumulate action-response history during
a controlled warm-up segment, then introduce the obstacle. The gate should compare:

```text
normal warm-up history
wrong matched warm-up history
reset history
zero action/response history
```

Pass only if normal warm-up history improves success or clearance margin under
strict visible-state matching and M62-class margin retention.
