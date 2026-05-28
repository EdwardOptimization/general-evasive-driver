# M1378 Paper-Route Promoted-Base Source-Rich Sequence Probe Result Audit

## Purpose

M1378 audits the M1377 sequence intervention probe before any corpus export,
objective update, PPO, promotion, private holdout, L0/L1/L2/L3 comparison, or
claim expansion.

M1378 does not train, run PPO, run new evaluation, promote, use private holdout,
change actor inputs, export a corpus, or make high-fidelity physical claims.

## M1377 Evidence

M1377 artifact:

```text
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/summary.json
```

M1377 result:

```text
result_class: sequence_temporal_history_positive
selected_source_rows: 384
intervention_rows: 6912
accepted_sequence_rows: 180
accepted_temporal_sequence_rows: 180
accepted_cross_fault_sequence_rows: 0
sequence_action_critical_rows: 1491
normal_failed_rows: 0
rejected_trace_rows: 0
unique_temporal_accepted_fault_pairs: 8
unique_temporal_accepted_seeds: 9
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Pre-registered temporal-positive candidate thresholds:

```text
accepted_temporal_sequence_rows >= 100
unique_temporal_accepted_fault_pairs >= 6
unique_temporal_accepted_seeds >= 12
```

Observed:

```text
accepted_temporal_sequence_rows: 180
unique_temporal_accepted_fault_pairs: 8
unique_temporal_accepted_seeds: 9
```

M1377 therefore passes row and fault-pair thresholds but misses the accepted-seed
threshold.

## Evidence Classification

Supported:

```text
M1377 is a clean structural sequence probe.
M1377 shows temporal-history dependence under source-rich capability-step rows.
Temporal accepted rows come from reset_then_warm_history and
delayed_capability_history variants.
```

Blocked:

```text
source-diverse temporal corpus export;
cross-fault wrong-history self-identification;
training or PPO;
promotion;
private holdout;
level3 self-identification.
```

Reason:

```text
The temporal signal is real enough to expand, but the seed threshold miss makes
direct corpus export premature.
```

## Why Expand Instead Of Export

M1377 selected only:

```text
384 source rows
per_fault_pair_cap: 48
```

The selected variants had broad source rows across 40 seeds, but accepted rows
concentrated into 9 seeds. The most direct way to test whether this is a
sampling cap artifact is to rerun the same no-training probe with larger public
source-row coverage.

Do not solve the seed miss by changing thresholds. The right next step is a
larger public sequence probe with the same claim boundary.

## Route Decision

Admit:

```text
m1379-paper-route-promoted-base-source-rich-sequence-expanded-probe
```

Planned command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv \
  --max-source-rows 768 \
  --per-fault-pair-cap 96 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1379_promoted_base_source_rich_sequence_expanded_probe
```

M1379 remains no-training public evaluation only. It must not export a corpus,
train, run PPO, promote, use private holdout, or change actor inputs.

## M1379 Interpretation Rules

M1379 should use stronger source-diversity thresholds:

```text
accepted_temporal_sequence_rows >= 200
unique_temporal_accepted_fault_pairs >= 8
unique_temporal_accepted_seeds >= 12
accepted_cross_fault_sequence_rows reported separately
```

Interpretation:

```text
thresholds pass:
  route to temporal sequence result audit before corpus export design.

rows/pairs pass but seeds still miss:
  classify as temporal-positive seed-thin; route to branch synthesis or
  source-selection redesign before corpus export.

temporal positives collapse:
  classify M1377 as sampling artifact and route to intervention redesign.

cross-fault sequence positives appear:
  audit them separately before any self-ID claim.
```

## Claim Boundary

M1378 preserves the current claim boundary:

```text
temporal-history dependence is not cross-fault self-identification;
reset/temporal positives are level2 history-encoded reactive evidence, not
level3 anticipatory belief;
current single-track proxies are not true per-wheel high-fidelity faults.
```

## Decision

Decision:

```text
promoted_base_source_rich_sequence_probe_audit_admit_expanded_probe
```

Next:

```text
m1379-paper-route-promoted-base-source-rich-sequence-expanded-probe
```
