# M695 Trajectory-Terminal Boundary Source-Miner Implementation

## Purpose

M695 implements the trajectory/terminal-boundary source miner designed in M694.

Question:

```text
Does the M692 replay surface contain rows where small first-action
perturbations or wrong-history actions measurably change closed-loop terminal
margin, risk, collision, off-road, spin, or recovery?
```

This milestone is implementation-only:

```text
no actor training
no residual-head training
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M695 adds:

```text
src/autodrift/trajectory_terminal_boundary_source_miner.py
tests/test_trajectory_terminal_boundary_source_miner.py
```

The miner:

```text
loads the unchanged M568 base actor
uses M692 replay rows as source scenarios
deduplicates the three M689 head replays into unique source rows
reconstructs normal and matched wrong-history snapshots
rolls out short continuations after first-action perturbations
computes terminal-margin and risk sensitivity
rejects rows already failed under normal history
labels trajectory_boundary, history_action_critical, terminal_cliff, and rejected rows
writes candidate, perturbation, accepted, source, split, rejected, and summary artifacts
checks that the actor checksum is unchanged
```

## Command

```bash
rm -rf runs/m695_trajectory_terminal_boundary_source_miner && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.trajectory_terminal_boundary_source_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --source-rows runs/m692_gate_margin_closed_loop_replay/replay_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --max-scenarios 256 \
  --max-boundary-margin 0.15 \
  --min-margin-sensitivity 0.02 \
  --min-risk-sensitivity 0.02 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m695_trajectory_terminal_boundary_source_miner
```

## Artifacts

```text
runs/m695_trajectory_terminal_boundary_source_miner/summary.json
runs/m695_trajectory_terminal_boundary_source_miner/source_rows.csv
runs/m695_trajectory_terminal_boundary_source_miner/candidate_rows.csv
runs/m695_trajectory_terminal_boundary_source_miner/perturbation_rollouts.csv
runs/m695_trajectory_terminal_boundary_source_miner/accepted_rows.csv
runs/m695_trajectory_terminal_boundary_source_miner/source_summary.csv
runs/m695_trajectory_terminal_boundary_source_miner/split_summary.csv
runs/m695_trajectory_terminal_boundary_source_miner/rejected_rows.csv
```

## Result

Implementation cleanliness passed:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

Source reconstruction and perturbation replay ran:

```text
rows_attempted:       40
snapshots_collected:  45
perturbation rows:    680
candidate rows:       40
```

The result is negative:

```text
normal_success_candidates:        15
normal_failed_rejected:           25
trajectory_sensitive_rows:         0
history_action_critical_rows:      0
terminal_cliff_rows:               0
accepted_rows:                     0
heldout_rows:                      0
source_positive:               false
result_class:          surface_empty
```

Sensitivity was far below threshold:

```text
margin_sensitivity_mean:  0.000154
margin_sensitivity_p95:   0.000391
risk_sensitivity_mean:    0.000154
risk_sensitivity_p95:     0.000391
success_flip_count:       0
collision_flip_count:     0
off_road_flip_count:      0
spin_flip_count:          0
```

## Interpretation

M695 confirms the M693 diagnosis.

The M692/M671 surface is not a good terminal-boundary source:

```text
25 / 40 unique source rows are already normal-failed and cannot serve as
action-critical self-ID evidence.

The 15 normal-success rows are insensitive to the registered small first-action
perturbations and matched wrong-history actions.
```

Allowed claim:

```text
The miner implementation works and cleanly reports that the current replay
surface is empty for terminal-margin-sensitive source mining.
```

Rejected claim:

```text
The current M692 source surface is suitable for objective design, actor update,
PPO, or self-ID proof.
```

## Failure Taxonomy

Primary label:

```text
scenario_sampling_failure
```

Reason:

```text
The source surface inherited from M692 is not sampled around terminal-margin
action-critical boundaries.
```

Secondary labels:

```text
metric_artifact:
  The earlier exact-output residual metrics did not identify terminal-sensitive
  closed-loop rows.

normal_failed_only risk:
  A majority of unique rows were already failed under normal history.
```

## Decision

Do not:

```text
design an objective from this surface
run actor update
run PPO
promote a checkpoint
continue response-amplification residual-head tuning
```

Do:

```text
run M696 audit/synthesis
decide whether to continue this branch by broadening scenario sampling
require fresh trajectory-sensitive rows before any objective design
```

## Validation

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_trajectory_terminal_boundary_source_miner.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

## Decision String

```text
trajectory_terminal_boundary_source_miner_surface_empty_admit_audit
```

## Next

```text
m696-trajectory-terminal-boundary-source-miner-audit
```
