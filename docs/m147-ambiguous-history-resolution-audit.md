# M147 Ambiguous History Resolution Audit

Date: 2026-05-22

## Question

M146 found many H1 body-history pairs where command, actuator, yaw/IMU, and
scene history were close but future envelope targets were far apart.

M147 asks whether those ambiguous H1 pairs are resolved by existing candidate
signals:

```text
P0 current no-wheel actor contract
raw front/rear wheel-speed proxy
front/rear local ground-speed diagnostic slots
extra-only vx/vy/steer-rate channels
```

This is still a supervised diagnostic audit. It does not promote any actor
input and does not run PPO.

## Method

M147 consumes the exported M146 pair files:

```text
runs/m146_body_feedback_seed9480/ambiguous_body_history_pairs.csv
runs/m146_body_feedback_seed9481/ambiguous_body_history_pairs.csv
runs/m146_body_feedback_seed9482/ambiguous_body_history_pairs.csv
```

For each seed, it replays the same deterministic sample collection and computes
standardized pair distances under:

```text
h1_body_only
p0_current_baseline
h1_plus_raw_wheel
h1_plus_raw_wheel_vparallel
extra_vx
extra_vy
extra_vx_vy
extra_steer_rate_proxy
extra_p0_missing = vx, vy, steer-rate proxy
extra_raw_wheel
extra_vparallel
```

Resolution criteria:

```text
full candidate:
  distance_gain_vs_h1 >= 0.05
  and distance_ratio_vs_h1 >= 1.25

extra-only candidate:
  standardized extra distance >= 0.25
```

The extra-only rows are not actor profiles. They answer whether the missing
channel itself separates the pair.

## Implementation

New module:

```text
src/autodrift/ambiguous_history_resolution_audit.py
```

New tests:

```text
tests/test_ambiguous_history_resolution_audit.py
```

## Commands

Seed runs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.ambiguous_history_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m146_body_feedback_seed9480/ambiguous_body_history_pairs.csv \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m147_ambiguous_resolution_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.ambiguous_history_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m146_body_feedback_seed9481/ambiguous_body_history_pairs.csv \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m147_ambiguous_resolution_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.ambiguous_history_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m146_body_feedback_seed9482/ambiguous_body_history_pairs.csv \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 25 \
  --post-slip-beta-threshold 0.06 \
  --run-dir runs/m147_ambiguous_resolution_seed9482
```

Aggregate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.ambiguous_history_resolution_audit \
  --mode aggregate \
  --summary-jsons runs/m147_ambiguous_resolution_seed9480/summary.json,runs/m147_ambiguous_resolution_seed9481/summary.json,runs/m147_ambiguous_resolution_seed9482/summary.json \
  --run-dir runs/m147_ambiguous_resolution_multiseed
```

## Artifacts

```text
runs/m147_ambiguous_resolution_seed9480/summary.json
runs/m147_ambiguous_resolution_seed9481/summary.json
runs/m147_ambiguous_resolution_seed9482/summary.json
runs/m147_ambiguous_resolution_multiseed/summary.json
runs/m147_ambiguous_resolution_multiseed/resolution_summary.csv
```

## Multiseed Results

Aggregate over `150` exported M146 ambiguous pairs:

| Profile | Role | Mean distance | Mean gain vs H1 | Resolved fraction | Feature-target corr. |
| --- | --- | ---: | ---: | ---: | ---: |
| H1 body only | base | 0.352134 | 0.000000 | 0.000000 | 0.699678 |
| P0 current baseline | full candidate | 0.398350 | 0.046216 | 0.153333 | 0.534400 |
| H1 + raw wheel | full candidate | 0.401967 | 0.049833 | 0.186667 | 0.399738 |
| H1 + raw wheel + vparallel | diagnostic full candidate | 0.438875 | 0.086740 | 0.306667 | 0.258442 |
| extra vx | extra only | 0.998091 | 0.645957 | 0.806667 | 0.018381 |
| extra vy | extra only | 0.580594 | 0.228460 | 0.686667 | 0.366183 |
| extra vx/vy | extra only | 0.879556 | 0.527422 | 0.860000 | 0.145021 |
| extra steer-rate proxy | extra only | 0.721031 | 0.368897 | 0.766667 | 0.007657 |
| extra P0 missing | extra only | 0.915898 | 0.563763 | 1.000000 | 0.138040 |
| extra raw wheel | extra only | 0.999903 | 0.647768 | 0.806667 | 0.020244 |
| extra vparallel | diagnostic extra only | 0.997300 | 0.645165 | 0.806667 | 0.018508 |

## Interpretation

The exported M146 H1 pairs are not also close under the channels missing from
H1. In fact, `extra_p0_missing` resolves every exported pair by the extra-only
distance threshold. Raw wheel and `v_parallel` also separate many pairs, but
their extra-only distances are almost uncorrelated with the future-envelope
target distance.

The important distinction:

```text
The extra channels distinguish many pairs.
They do not yet prove a target-aligned self-identification signal.
```

Full-profile candidates are weaker:

```text
P0 current baseline resolves only 15.3%.
H1 + raw wheel resolves only 18.7%.
H1 + raw wheel + vparallel resolves 30.7%, but vparallel is diagnostic only.
```

This suggests M146's ambiguity may partly be an artifact of using a narrower
H1 profile that removed deployable current kinematic cues. It does not justify
adding raw wheel or `v_parallel` to the actor.

## Decision

Complete M147 as a diagnostic audit:

- keep P0 as the current human-view actor contract;
- do not promote raw wheel or `v_parallel`;
- treat M146 H1 ambiguity as insufficient evidence that current P0 is
  information-limited;
- the next high-value step is a stricter ambiguity miner that requires pairs to
  be close under P0, not only under H1.
