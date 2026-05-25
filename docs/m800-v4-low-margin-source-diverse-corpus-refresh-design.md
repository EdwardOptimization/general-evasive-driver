# M800 V4 Low-Margin Source-Diverse Corpus Refresh Design

## Purpose

M800 designs the next no-training data refresh after M799 accepted the M798
active-steer guard corpus blocker.

The working hypothesis is:

```text
The active-steer guard branch is currently corpus-limited. We do not have a
source-diverse set of normal-history rows whose residual-assisted alpha 0.2
branch succeeds with very low clearance margin. Before another calibrator
objective, we need to deliberately mine that low-margin normal boundary.
```

This milestone is design-only:

```text
no corpus run
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Why This Is Not Just a Threshold Problem

M798 used the registered low-margin guard selector on the M795 parent replay:

```text
branch == normal
alpha == 0.2
normal margin <= 0.00005
or known active boundary key
```

The result was only:

```text
12 rows
1 seed
1 source_index
1 fault-family pair
max seed dominance: 1.0
```

A direct margin-distribution check on the same parent replay shows that the
problem is not only the exact `0.00005` cutoff:

```text
normal alpha 0.2 rows: 2640
margin <= 0.00005: 12 rows, 1 seed, 1 source, 1 pair
margin <= 0.00010: 12 rows, 1 seed, 1 source, 1 pair
margin <= 0.00100: 36 rows, 1 seed, 3 sources, 2 pairs
margin <= 0.10000: 36 rows, 1 seed, 3 sources, 2 pairs
next distinct low rows jump to about 0.201 m
```

So the existing M773/M795 surface has a real gap: it contains many broad
sequence-outcome rows, but almost no source-diverse residual-assisted
normal-boundary rows. Weakening the threshold would mostly turn the same
single seed into a larger public tuning target.

## Source Boundary

M800 keeps the same claim boundary as M773:

```text
current_model_or_proxy
```

The current simulator can represent or proxy broad capability-loss families,
but it cannot support true per-wheel physical claims yet. The refresh may mine
current-model or current-model-proxy faults such as:

```text
global mu loss
front/rear lateral authority loss
brake authority loss
drive authority loss
steering fault
mass/CG shift
delay/noise fault
combined fault
```

It must not claim true single-wheel blowout, stuck caliper, split-mu,
halfshaft, suspension damage, or wheel-sensor physics until a four-wheel or
higher-fidelity dynamics engine exists.

## M801 Pipeline Design

M801 should implement and run a no-training low-margin refresh with four
stages.

### 1. Boundary-Retargeted Source Wave

Add a public mining config:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

The config should be derived from the M772 broader-holdout config but retargeted
toward low normal margins:

```text
seed_start: 78048
seed_count: 2048
max_pairs: 49152
max_source_rows: 2048
claim_boundary_level: current_model_or_proxy
```

Sampling should emphasize:

```text
near-boundary obstacle timing
stable-AES-infeasible and drift-required windows
brake/drive/rear-lateral/steering/combined fault pairs
pre-emergency and emergency-entry fault onsets
normal-success but low-clearance branches
```

This is public mining data, not a private promotion holdout.

### 2. V4 Sequence-Outcome Export

Reuse the established M773 pipeline:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 78048 \
  --seed-count 2048 \
  --device cpu \
  --run-dir runs/m801_v4_low_margin_refresh_extreme_faults

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --reset-rows runs/m801_v4_low_margin_refresh_extreme_faults/reset_only_rows.csv \
  --rejected-rows runs/m801_v4_low_margin_refresh_extreme_faults/rejected_rows.csv \
  --seed-start 78048 \
  --seed-count 2048 \
  --max-source-rows 2048 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m801_v4_low_margin_refresh_sequence_intervention

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m801_v4_low_margin_refresh_sequence_intervention/summary.json \
  --rollouts runs/m801_v4_low_margin_refresh_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m801_v4_low_margin_refresh_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m801_v4_low_margin_refresh_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m801_v4_low_margin_refresh_corpus_export
```

These stages remain data generation and export only. They must not train or
promote a checkpoint.

### 3. Reference Residual Replay for Guard Selection

M801 should add a small no-training selector/replay tool:

```text
src/autodrift/v4_low_margin_guard_corpus_refresh.py
tests/test_v4_low_margin_guard_corpus_refresh.py
```

The tool should reconstruct supported fresh positives, apply the frozen M568
actor plus frozen M761 residual head, and write a reference replay surface for
guard selection:

```text
runs/m801_v4_low_margin_source_diverse_corpus_refresh/reference_replay_rows.csv
```

Primary alpha:

```text
alpha == 0.2
```

Diagnostic alphas:

```text
0.0, 0.125, 0.15, 0.2
```

If M801 needs to compare against the M795 steer-attributed behavior, it may
load the M795 calibrator only as a reference replay mode. It must not train a
new calibrator in this milestone.

### 4. Low-Margin Guard Corpus Export

M801 should select normal-branch rows from the reference replay with:

```text
branch == normal
alpha == 0.2
normal_success == true
normal_collision == false
0.0 <= min_clearance_margin <= 0.00005
metadata complete
```

It should write:

```text
runs/m801_v4_low_margin_source_diverse_corpus_refresh/low_margin_guard_candidates.csv
runs/m801_v4_low_margin_source_diverse_corpus_refresh/accepted_low_margin_guard_rows.csv
runs/m801_v4_low_margin_source_diverse_corpus_refresh/diagnostic_margin_bands.csv
runs/m801_v4_low_margin_source_diverse_corpus_refresh/summary.json
docs/m801-v4-low-margin-source-diverse-corpus-refresh-implementation.md
```

Diagnostic margin bands should be reported but not used to pass the primary
gate:

```text
margin <= 0.00005
margin <= 0.00010
margin <= 0.00050
margin <= 0.00100
margin <= 0.01000
margin <= 0.10000
margin <= 0.20000
```

If the `0.00005` primary band is sparse but wider bands are rich, the result
should be classified as a boundary-window miss. The follow-up should retarget
scenario sampling, not silently pass with a wider threshold.

## Acceptance Gates

The primary low-margin corpus gate passes only if:

```text
accepted low-margin normal guard rows >= 80
unique seeds >= 8
unique source_index values >= 8
unique fault-family pairs >= 4
max single seed dominance <= 0.25
max single source_index dominance <= 0.15
max single fault-family-pair dominance <= 0.40
normal collision rate in accepted rows == 0.0
actor checksum unchanged
residual-head checksum unchanged
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

The old public active source may be carried into artifacts as a diagnostic
reference, but it must not count toward the fresh-source diversity pass and its
share must be capped:

```text
seed 77025/source_index 12 share <= 0.10 if included
```

## Failure Classes

M801 should classify failures explicitly:

```text
low_margin_rows_absent:
  no meaningful fresh rows in the primary or diagnostic low-margin bands

low_margin_rows_single_source:
  primary rows exist but are dominated by one seed/source/fault pair

diagnostic_band_only:
  wider bands are populated but <= 0.00005 remains sparse

reference_replay_artifact:
  row reconstruction or metadata alignment fails

contract_violation:
  actor inputs or deploy-time features change
```

Only a true source-diverse pass should admit a new active-steer guard
calibration implementation. Sparse or single-source results should route to
another scenario retargeting audit.

## Why M801 Comes Before More Calibration

The previous residual-calibration branch repeatedly found useful but fragile
signals:

```text
M780: alpha 0.125 is feasible but weak
M786: scalar gate has limited alpha 0.15 candidate
M795: steer-attributed gate reaches alpha 0.2 gap but active margin is too thin
M798: active guard cannot start because low-margin rows are single-source
```

The current blocker is therefore data coverage, not another scalar coefficient.
M801 should answer whether the simulator can produce a source-diverse
low-margin normal-boundary surface under the current model. Only then is it
fair to test active-steer guarding again.

## Decision

M800 admits:

```text
m801-v4-low-margin-source-diverse-corpus-refresh-implementation
```

M801 should implement and run the no-training corpus refresh. Residual
calibration, PPO, and checkpoint promotion remain blocked until M801 is audited.
