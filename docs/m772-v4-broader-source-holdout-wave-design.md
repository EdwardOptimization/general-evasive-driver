# M772 V4 Broader Source-Holdout Wave Design

## Purpose

M772 designs the next fresh source-holdout wave after M770 produced a limited
holdout positive on the sparse M767 corpus.

The working hypothesis is:

```text
The current evidence may still be limited by scenario mining coverage. A wider
fresh extreme-fault wave should test whether the residual self-ID mechanism is
visible across more seeds, fault-family pairs, and severe capability-loss
cases before any stronger generalization, PPO, or promotion claim.
```

This is design-only:

```text
no data wave
no residual replay
no actor training
no PPO
no checkpoint promotion
```

## Why Coverage Is a Real Suspect

M767 was fresh but sparse:

```text
positive_rows: 995
unique_positive_seeds: 25
unique_positive_fault_family_pairs: 13
max_positive_seed_dominance: 0.247236
result_class: v4_sequence_outcome_corpus_sparse
```

M770 then showed that the M761 residual signal transfers to that limited
holdout:

```text
normal_success_rate at alpha 0.2: 995 / 995
normal_collision_rate at alpha 0.2: 0 / 995
intervention_action_gap_mean:
  base: 0.043862
  alpha 0.2: 0.050473
margin_gap_mean:
  base: 0.026641
  alpha 0.2: 0.030329
```

That supports the user's coverage hypothesis: the mechanism exists on fresh
rows, but the rows are too concentrated to support broad conclusions. It is
therefore plausible that we have not mined enough extreme command-response
conditions yet.

## Fault Coverage Boundary

The current simulator is still a single-track model with VehicleParams changes.
It can mine capability-loss proxies, but it cannot make true per-wheel physical
claims.

Current-model or current-model-proxy coverage includes:

```text
global mu loss / ice patch
front and rear lateral authority collapse
front and rear blowout grip proxies
drive authority loss / halfshaft torque-loss proxy
brake authority loss / single-wheel brake-loss proxy
stuck-caliper brake-pull proxy
split-mu front/rear authority proxies
steering authority collapse or steering stuck proxy
payload / mass / inertia / CG shift
actuator and sensor-delay authority proxies
combined fault stacks
```

Future high-fidelity coverage should include true four-wheel/contact-patch
effects:

```text
single-wheel puncture or blowout with radius, drag, and pull
single-corner grip collapse
left-right split-mu patch
stuck caliper or single-wheel brake pull
single-wheel brake pressure loss
asymmetric halfshaft or CV joint torque loss
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor dropout, bias, or quantization
steering rack asymmetry or tie-rod damage
corner suspension, toe, camber, or ride-height damage
tire pressure, temperature, wear, or delamination dynamics
road crown, bank, curb, puddle, gravel, snow, oil, or ice asymmetry
combined single-corner damage
```

M772 does not change the model fidelity. It explicitly keeps these true
per-wheel scenarios as future high-fidelity work while using the current
single-track proxies for source mining.

## Broader Holdout Config

M772 adds:

```text
configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
```

It preserves the v4 fault family and pairing-rule surface but changes the
fresh-holdout coverage intent:

```text
seed_start: 77024
seed_count: 1024
max_pairs: 24576
max_source_rows for sequence intervention: 1024
```

The `max_pairs` increase matters. M767 used `seed_count=512` and saturated the
old `max_pairs=12288` cap. Merely increasing `seed_count` without increasing
`max_pairs` would not broaden matched-pair coverage.

## M773 Registered Pipeline

M773 should run three no-training steps.

### 1. Broader extreme source wave

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 77024 \
  --seed-count 1024 \
  --device cpu \
  --run-dir runs/m773_v4_broader_source_holdout_extreme_faults
```

### 2. Broader reset-source sequence intervention

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --reset-rows runs/m773_v4_broader_source_holdout_extreme_faults/reset_only_rows.csv \
  --rejected-rows runs/m773_v4_broader_source_holdout_extreme_faults/rejected_rows.csv \
  --seed-start 77024 \
  --seed-count 1024 \
  --max-source-rows 1024 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m773_v4_broader_source_holdout_sequence_intervention
```

### 3. Broader v4 sequence-outcome corpus export

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m773_v4_broader_source_holdout_sequence_intervention/summary.json \
  --rollouts runs/m773_v4_broader_source_holdout_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m773_v4_broader_source_holdout_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m773_v4_broader_source_holdout_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m773_v4_broader_source_holdout_corpus_export
```

## Broader Coverage Gates

M773 should preserve the ordinary artifact checks:

```text
sentinel positives: 0
missing normal matches: 0
missing v4 metadata: 0
missing fidelity metadata: 0
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
claim_boundary_level: current_model_or_proxy
```

M773 should also report the broader gates from M771:

```text
positive_rows >= 1500
unique_positive_seeds >= 40
unique_positive_fault_family_pairs >= 18
max_positive_seed_dominance <= 0.15
max_positive_fault_family_pair_dominance <= 0.22
```

If these gates pass, M774 may audit and then consider no-PPO residual replay
with alpha `0.2` as the primary candidate.

If these gates fail, the failure should be classified as
`scenario_sampling_failure`, and the next branch should inspect source
selection before running residual replay.

## Claim Scope

M772 supports only this design claim:

```text
The next highest-leverage step is a broader fresh source-holdout data wave,
because the latest positive result is still limited by sparse and concentrated
coverage.
```

M772 does not claim:

```text
broad generalization
driver promotion readiness
PPO safety
true single-wheel or four-wheel physical fault fidelity
```

## Decision

M772 admits M773:

```text
m773-v4-broader-source-holdout-wave-implementation
```

M773 should generate and export the broader fresh corpus only. Residual replay,
PPO, training, and promotion remain blocked until a separate audit.
