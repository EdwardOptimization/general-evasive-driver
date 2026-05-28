# M1335 Paper-Route Materialized Source-History Objective Corpus Design

## Summary

M1335 designs a no-policy objective-corpus export from the M1333 materialized
history artifacts.

Decision:

```text
materialized_source_history_objective_corpus_design_admit_export
```

The export should use the history-distinguishable active subset:

```text
active source pairs: 344
active pair-probe groups: 688
active history prefixes: 1376
active history frames: 33024
active source families: 6
active zero response_l2 prefixes: 0
```

It should quarantine:

```text
halfshaft source pairs: 22
halfshaft history prefixes: 88
halfshaft history frames: 2112
global_friction_step: missing source family
```

This is a design-only milestone. It does not train, run PPO, promote, use
private holdout, change actor inputs, or claim self-identification.

## Active Selection Rule

The active objective corpus should include a source pair only if:

```text
source_family != halfshaft_torque_loss->halfshaft_torque_loss
and every history prefix for that pair has response_l2_from_opposite_branch >= 0.01
and all corresponding source, prefix, frame, intervention, and wrong-history
rows preserve source_run_id/source_row_id/original_pair_id/source_identity
```

For M1333 this is equivalent to:

```text
exclude source_family == halfshaft_torque_loss->halfshaft_torque_loss
```

because every non-halfshaft prefix has `response_l2 >= 0.01`.

Do not use raw `pair_id` as global source identity. It is only a M1330/M1333
local row id. The durable identity remains:

```text
source_identity = source_run_id + ":" + source_row_id
```

## Active Corpus Shape

Expected active artifacts:

```text
active_source_pair_rows: 344
active_history_prefix_rows: 1376
active_history_frame_rows: 33024
active_history_intervention_rows: 1376
active_wrong_history_pair_rows: 1376
```

Active family counts:

```text
steering_actuator_fault: 96
single_wheel_grip_collapse: 64
single_wheel_brake_pull: 62
load_cg_perturbation: 54
left_right_split_mu: 37
tire_blowout_like: 31
```

Active fold balance:

```text
fold 0: 71 pairs, 6 families, top share 0.2254
fold 1: 70 pairs, 6 families, top share 0.2857
fold 2: 68 pairs, 6 families, top share 0.2941
fold 3: 68 pairs, 6 families, top share 0.2941
fold 4: 67 pairs, 6 families, top share 0.2985
```

This remains above the earlier expansion target:

```text
target source pairs: 240
target pair-probe groups: 480
active source pairs: 344
active pair-probe groups: 688
```

## Quarantine Rule

Halfshaft rows are not deleted. They should be exported into a quarantine set:

```text
quarantine_reason: halfshaft_probe_silent
source_family: halfshaft_torque_loss->halfshaft_torque_loss
source_pairs: 22
history_prefixes: 88
history_frames: 2112
```

Reason:

```text
The current brake/lift probes use throttle=-1.0 and brake=+1.0, so rear
halfshaft torque-loss branches are not distinguished in the history prefix.
```

Global friction should be represented by a separate missing-family quarantine
row:

```text
quarantine_reason: source_family_missing
source_family: global_friction_step->global_friction_step
source_pairs: 0
```

The quarantine artifacts are bookkeeping and future-work inputs. They are not
active objective rows.

## M1336 Tool

Add:

```text
src/autodrift/materialized_source_history_objective_corpus_export.py
tests/test_materialized_source_history_objective_corpus_export.py
```

The tool should read:

```text
runs/m1333_source_topup_response_history_materialization/summary.json
runs/m1333_source_topup_response_history_materialization/source_pair_rows.csv
runs/m1333_source_topup_response_history_materialization/history_prefix_rows.csv
runs/m1333_source_topup_response_history_materialization/history_frame_rows.csv
runs/m1333_source_topup_response_history_materialization/history_intervention_rows.csv
runs/m1333_source_topup_response_history_materialization/wrong_history_pair_rows.csv
runs/m1333_source_topup_response_history_materialization/source_lineage_rows.csv
```

It should write:

```text
runs/m1336_materialized_source_history_objective_corpus_export/summary.json
runs/m1336_materialized_source_history_objective_corpus_export/active_source_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_prefix_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_frame_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_intervention_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_wrong_history_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_source_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_prefix_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_frame_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_intervention_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_wrong_history_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_family_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_family_summary.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_fold_summary.csv
runs/m1336_materialized_source_history_objective_corpus_export/source_lineage_rows.csv
```

## M1336 Command

Proposed command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_materialized_source_history_objective_corpus_export.py

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_objective_corpus_export \
  --materialized-run-dir runs/m1333_source_topup_response_history_materialization \
  --run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --min-response-l2 0.01
```

## M1336 Acceptance

M1336 should pass as infrastructure if:

```text
focused tests pass
summary.json exists
active_source_pair_rows == 344
active_history_prefix_rows == 1376
active_history_frame_rows == 33024
active_history_intervention_rows == 1376
active_wrong_history_pair_rows == 1376
active_source_family_count == 6
active_zero_response_l2_prefix_count == 0
active_response_l2_ge_0_01_count == 1376
active_max_source_family_fold_share <= 0.40
quarantine_source_pair_rows == 22
quarantine_history_prefix_rows == 88
quarantine_history_frame_rows == 2112
quarantine_family_rows includes halfshaft_probe_silent
quarantine_family_rows includes global_friction_missing
source_identity_duplicate_count == 0
source_identity_metadata_preserved == true
labels_enter_actor_input == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
accepted_thresholds_relaxed == false
```

If the active corpus falls below the 240/480 source-pair and group targets,
M1336 should route to a fold/cap repair audit instead of objective design.

## Guardrails

M1335 and M1336 must not:

```text
train;
run PPO;
promote;
use private holdout;
change actor inputs;
include halfshaft history-silent rows in active objective rows;
hide global friction absence;
claim driver performance;
claim strong self-identification;
claim high-fidelity or real-vehicle validation.
```

## Next Milestone

Admit:

```text
m1336-paper-route-materialized-source-history-objective-corpus-export
```

Scope:

```text
implement one no-policy active/quarantine export;
preserve source identity metadata;
write active and quarantine artifacts;
do not train;
do not run PPO;
do not promote.
```
