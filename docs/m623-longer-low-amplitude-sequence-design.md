# M623 Longer Low-Amplitude Sequence Design

## Purpose

M623 designs a no-training diagnostic after M622 found that M621 has useful
candidate-level family diversity but insufficient source-level diversity.

M621/M622 facts:

```text
accepted candidate rows: 189
accepted selected sequences: 6
accepted physical pairs: 5
accepted left seeds: 4
dominant blocker: source-level diversity, not candidate-family availability
```

Question:

```text
Can a longer low-amplitude prefix recover additional source-diverse accepted
sequences without widening trust regions or lowering target thresholds?
```

M623 is design-only:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Design Decision

Run one diagnostic sequence-mining experiment that keeps the M621 setup but adds
`K=7`:

```text
M621 baseline: K in {3, 5}
M624 diagnostic: K in {3, 5, 7}
```

The candidate families should remain:

```text
constant_delta
decay_pulse
brake_release_then_steer
steer_then_brake
```

Do not introduce `ramp_hold` or `smooth_pulse` yet. The current miner already
supports arbitrary K for the existing families, and M624 should isolate the
effect of sequence length before adding more shape degrees of freedom.

## Low-Amplitude Delta Grid

M624 should keep the existing action trust metrics:

```text
per-step action L2 <= 0.10
sequence mean L2 <= 0.08
sequence max L2 <= 0.10
max delta-delta L2 <= 0.08
```

To make the longer prefix genuinely low-amplitude, M624 may add intermediate
steer deltas while retaining the original endpoints:

```text
steer_delta in {-0.08, -0.06, -0.04, 0, +0.04, +0.06, +0.08}
throttle_delta in {-0.06, 0, +0.03}
brake_delta in {-0.08, -0.04, 0, +0.04, +0.08}
```

This does not widen the action trust region. It only gives the search a lower
amplitude option that may work better over seven steps.

## Acceptance Thresholds

M624 must keep M621 target thresholds unchanged:

```text
margin_improvement >= 0.02
or risk_improvement >= 0.05
```

Hard rejects remain:

```text
candidate_collision
candidate_off_road
candidate_spin_out
outside_sequence_trust_region
```

## Source Rows

M624 should use the M616 expanded source table:

```text
runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv
```

This preserves source-tier metadata and lets M624 compare directly to M621.

## Comparison To M621

M624 should explicitly compare against:

```text
runs/m621_tier_aware_sequence_target_miner/summary.json
```

Required comparison metrics:

```text
selected accepted sequences
accepted selected physical pairs
accepted selected left seeds
accepted selected source tiers
accepted candidate rows
accepted candidate physical pairs
accepted candidate left seeds
accepted candidate family counts
accepted candidate sequence-length counts
best unaccepted margin/risk improvement
candidate rejection counts
```

## Success Criteria For Later Audit

M624 remains diagnostic-only. It can admit an optimizer-design discussion only
if a later audit confirms source-level breadth:

```text
selected accepted sequences >= 8
selected accepted physical pairs >= 6
selected accepted left seeds >= 6
accepted source-tier distribution audited
selected action-mode / sequence-length distribution audited
```

Candidate-level counts remain diagnostic:

```text
accepted_candidate_sequences != independent training examples
```

If K=7 only increases candidate rows on the same five physical pairs, that is a
negative result for source diversity, even if accepted candidate count rises.

## Proposed M624 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.sequence_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --boundary-source-rows runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --sequence-lengths 3,5,7 \
  --family constant_delta \
  --family decay_pulse \
  --family brake_release_then_steer \
  --family steer_then_brake \
  --steer-deltas=-0.08,-0.06,-0.04,0,0.04,0.06,0.08 \
  --throttle-deltas=-0.06,0,0.03 \
  --brake-deltas=-0.08,-0.04,0,0.04,0.08 \
  --per-step-action-l2 0.10 \
  --sequence-mean-l2-limit 0.08 \
  --sequence-max-l2-limit 0.10 \
  --max-delta-delta-l2-limit 0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --max-continuation-steps 80 \
  --device cpu \
  --run-dir runs/m624_longer_low_amplitude_sequence_miner
```

Expected candidate count:

```text
30 source rows
3 sequence lengths
246 candidates per length/source
22140 candidate rollouts
```

This is small enough for a diagnostic run and still no-training.

## Contract Checks

```text
actor_input_changed: false
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
longer_low_amplitude_sequence_design_admit_m624
```

Next blocker:

```text
m624-longer-low-amplitude-sequence-miner
```
