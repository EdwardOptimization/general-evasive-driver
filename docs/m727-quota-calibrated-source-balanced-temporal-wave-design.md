# M727 Quota-Calibrated Source-Balanced Temporal Wave Design

## Purpose

M727 designs the next no-training wave after M726 audited M725.

The question is:

```text
Can we remove the M725 quota artifact and run a genuinely source-balanced
4096-pair temporal wave before deciding whether the lack of outcome-critical
rows is a real scenario/fidelity limit?
```

This is a design milestone only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## M725 Blocker

M725 had enough proposals:

```text
proposal_count: 69591
proposal preferred families: 9
proposal fault-family pairs: 40
```

But it selected only:

```text
selected_pair_count: 2048
```

The direct cause was:

```text
per_step_bucket_cap: 1024
populated step buckets: 2
maximum selectable rows from this cap: 2048
```

So M725 does not prove the extreme scenario wave is exhausted. It proves the
registered selection caps were too tight for the intended scale.

## Design Decision

M727 keeps the selected-pair target at `4096`.

It changes the run configuration, not the actor or training method:

```text
selected_pair_count: 4096
per_seed_pair_cap: 8
per_fault_family_pair_cap: 256
per_preferred_family_cap: 640
per_step_bucket_cap: 4096
seed_count: 512
```

Rationale:

```text
1. per_step_bucket_cap=4096 removes the artificial 2048 ceiling.

2. per_seed_pair_cap=8 preserves seed diversity and makes 512 seeds enough for
   exactly 4096 selected pairs.

3. per_preferred_family_cap=640 keeps any preferred family below 0.15625 of the
   selected set, stricter than the 0.25 dominance gate.

4. per_fault_family_pair_cap=256 prevents a small set of pair types from
   dominating while still allowing 16 full-cap pairs to fill 4096 rows.

5. The run still has to pass source-balance gates; the design does not lower
   outcome or source-balance thresholds after seeing M725.
```

## Registered M728 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_temporal_wave \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 512 \
  --selected-pair-count 4096 \
  --per-seed-pair-cap 8 \
  --per-fault-family-pair-cap 256 \
  --per-preferred-family-cap 640 \
  --per-step-bucket-cap 4096 \
  --device cpu \
  --run-dir runs/m728_quota_calibrated_source_balanced_temporal_wave
```

Optional smoke before the registered run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_temporal_wave \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 2 \
  --selected-pair-count 16 \
  --per-seed-pair-cap 8 \
  --per-fault-family-pair-cap 256 \
  --per-preferred-family-cap 640 \
  --per-step-bucket-cap 4096 \
  --device cpu \
  --run-dir runs/m728_quota_calibrated_source_balanced_temporal_wave_smoke
```

## M728 Required Artifacts

```text
runs/m728_quota_calibrated_source_balanced_temporal_wave/summary.json
runs/m728_quota_calibrated_source_balanced_temporal_wave/scenario_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/pair_proposals.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/selected_pair_proposals.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/source_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/intervention_rollouts.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/sentinel_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/rejected_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/quota_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/seed_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/fault_family_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/variant_summary.csv
```

## M728 Gate Targets

Source-balance gate:

```text
selected_pair_count >= 3000
unique_selected_seeds >= 128
unique_preferred_fault_families >= 8
unique_fault_family_pairs >= 24
max_seed_dominance <= 0.02
max_preferred_family_dominance <= 0.25
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
```

Action evidence:

```text
temporal_action_critical_rows >= 300
unique_temporal_action_seeds should be recorded
variant-level action rows must be separated from reset-hidden rows
```

Outcome evidence:

```text
temporal_outcome_critical_rows >= 20
```

If the source-balance gate passes but outcome rows remain below threshold, the
result class should remain action-only or sparse. It should not be promoted to
closed-loop self-identification proof.

## Claims Allowed After M728

If M728 passes source-balance but has `0` outcome rows, it can claim:

```text
source-balanced temporal command-history action coupling exists under the
current v2 extreme-fault scenario family.
```

It cannot claim:

```text
closed-loop outcome-critical self-identification proof.
```

If M728 passes both source-balance and outcome gates, M729 must still audit the
rows before any source export, actor update, PPO, or promotion.

## Forbidden Shortcuts

M728 must not:

```text
1. add hidden fault labels to actor observations;
2. treat hidden fault metadata as deployable input;
3. lower outcome thresholds after the run;
4. merge action-only rows into outcome-positive rows;
5. train or update actor parameters;
6. run PPO;
7. promote a checkpoint.
```

## Decision Tree After M728

If M728 is `source_balance_blocked`:

```text
audit the selected/proposal distribution again before changing scenario
families.
```

If M728 is `source_balanced_temporal_action_only`:

```text
audit and then choose between source-balanced boundary mining and
sequence-level interventions.
```

If M728 is `source_balanced_temporal_outcome_positive`:

```text
audit accepted rows, export a compact corpus, and only then design an objective
or gate.
```

If M728 remains action-only after a clean source-balanced pass:

```text
this strengthens the case that the project needs either closer outcome-boundary
mining, sequence-level command-response interventions, or more physical
asymmetric/yaw-disturbance dynamics.
```
