# M1376 Paper-Route Promoted-Base Source-Rich Public Wave Result Audit

## Purpose

M1376 audits M1375 before any temporal/sequence intervention run, source
redesign, L0/L1/L2/L3 comparison refresh, PPO continuation, promotion, or
private-holdout use.

M1376 does not train, run PPO, run new evaluation, promote, use private holdout,
change actor inputs, mutate a checkpoint, relax thresholds, or make
high-fidelity physical claims.

## M1375 Evidence

M1375 artifact:

```text
runs/m1375_promoted_base_source_rich_public_wave/summary.json
```

M1375 result:

```text
result_class: cross_fault_wrong_sparse
scenario_count: 3328
snapshot_count: 16257
matched_pair_count: 4096
unmatched_rows: 1
accepted_rows: 3
reset_only_rows: 1281
rejected_rows: 2812
normal_failed_rejected: 936
history_insensitive_rejected: 1876
wrong_history_action_critical_rows: 3
reset_history_action_critical_rows: 1281
unique_accepted_fault_families: 2
unique_accepted_wrong_fault_families: 2
unique_accepted_severities: 1
unique_accepted_seeds: 2
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M1375 passed structurally and failed source-positive interpretation thresholds:

```text
accepted_rows: 3 / 40 required
unique_accepted_fault_families: 2 / 4 required
unique_accepted_seeds: 2 / 24 required
```

## Audit

M1375 confirms the M1373 pattern:

```text
cross-fault wrong-history accepted rows remain sparse;
larger seed/pair coverage mostly scales reset-only rows;
the current single hidden-state cross-fault swap is not producing
source-diverse outcome-sensitive wrong-history proof.
```

M1375 should not be treated as a failed harness run. It is a valid negative
source-rich result:

```text
structural source-rich public wave: pass
source-positive cross-fault wrong-history evidence: not supported
reset-hidden recurrent-state sensitivity: strongly supported
```

This result blocks direct training from accepted wrong-history rows and blocks
any source-diverse self-identification claim. It supports a more targeted next
test: sequence-level temporal interventions on the reset-only source rows.

## Why Not Keep Scaling Cross-Fault Pairs

The larger wave already used:

```text
seed_count: 256
matched_pair_count: 4096
reset_only_rows: 1281
```

Accepted wrong-history rows only increased from `2` in M1373 to `3` in M1375.
That is not a promising active set for objective training or another immediate
seed-only expansion.

The strongest available evidence axis is reset-only:

```text
M1373 reset_only_rows: 174
M1375 reset_only_rows: 1281
```

Prior capability-step work showed that reset-only rows can become useful
temporal-history evidence when the intervention is sequence-level rather than a
single hidden-state swap. The next test should therefore ask whether the current
promoted M1362 base also has outcome-relevant temporal-history dependence under
the M1375 source-rich reset-only rows.

## Route Decision

Admit:

```text
m1377-paper-route-promoted-base-source-rich-sequence-intervention-probe
```

Planned command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1377_promoted_base_source_rich_sequence_intervention_probe
```

M1377 should remain a no-training public probe. It should classify:

```text
accepted_temporal_sequence_rows
accepted_cross_fault_sequence_rows
unique_temporal_accepted_fault_pairs
unique_temporal_accepted_seeds
variant_summary
history_length_summary
```

Pre-registered interpretation:

```text
accepted_temporal_sequence_rows >= 100
and unique_temporal_accepted_fault_pairs >= 6
and unique_temporal_accepted_seeds >= 12:
  temporal-history-positive candidate, still audit before any corpus/objective.

accepted_cross_fault_sequence_rows > 0:
  cross-fault sequence diagnostic signal, audit separately before claim.

accepted_temporal_sequence_rows > 0 but below thresholds:
  sparse temporal diagnostic signal.

accepted_temporal_sequence_rows == 0 and accepted_cross_fault_sequence_rows == 0:
  reset-only source rows do not convert under this sequence intervention;
  route to source/intervention redesign.
```

Do not convert any M1377 positive row directly into training without a separate
corpus export and exact-objective sanity milestone.

## Claim Boundary

The current source-rich branch still uses current single-track and axle-level
faults/proxies. M1376 makes no true single-wheel, split-mu, halfshaft,
stuck-caliper, suspension, tire-damage, high-fidelity, real-vehicle,
paper-level, L0/L1/L2/L3, or level3 self-identification claim.

## Supported Claims

M1376 supports:

```text
1. M1375 is a clean structural larger public source-rich wave.
2. M1375 falsifies the source-positive interpretation for current cross-fault
   wrong-history swaps under pre-registered thresholds.
3. M1375 strongly supports reset-hidden recurrent-state sensitivity.
4. The next best public evidence step is sequence-level temporal intervention
   on the M1375 reset-only rows.
```

## Unsupported Claims

M1376 does not support:

```text
1. training or PPO;
2. promotion;
3. private-holdout evidence;
4. source-diverse cross-fault wrong-history self-identification;
5. temporal-history evidence from M1375 alone;
6. L0/L1/L2/L3 comparison conclusions;
7. high-fidelity per-wheel or real-vehicle transfer claims;
8. level3 anticipatory recurrent-belief self-identification.
```

## Decision

Decision:

```text
promoted_base_source_rich_public_wave_audit_admit_sequence_probe
```

Next:

```text
m1377-paper-route-promoted-base-source-rich-sequence-intervention-probe
```
