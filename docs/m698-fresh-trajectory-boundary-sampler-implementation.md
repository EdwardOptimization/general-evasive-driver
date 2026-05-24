# M698 Fresh Trajectory-Boundary Sampler Implementation

## Purpose

M698 implements the fresh broad scenario sampler designed in M697.

Question:

```text
Can fresh scenario sampling find terminal-margin-sensitive trajectory rows
outside the inherited M692 replay surface?
```

This milestone is implementation-only:

```text
no actor training
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M698 adds:

```text
src/autodrift/fresh_trajectory_boundary_sampler.py
tests/test_fresh_trajectory_boundary_sampler.py
```

The sampler:

```text
loads the unchanged M568 base actor
samples fresh seeds across fresh and ood configs
collects multiple candidate snapshots per episode
keeps snapshots closest to a target obstacle distance
runs normal-history prepass
rejects already-normal-failed and too-safe rows
runs local first-action perturbation rollouts on boundary candidates
optionally matches similar snapshots from other seeds for wrong/counterfactual-history testing
writes episode, snapshot, prepass, perturbation, accepted, rejected, source, split, skipped-window, and summary artifacts
checks that the actor checksum is unchanged
```

The sampler does not use M692 rows as the source. M692/M695 are only lineage and
negative-result context.

## Smoke

A small smoke run validated snapshot collection and artifact writing:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.fresh_trajectory_boundary_sampler \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --seed-start 30000 \
  --seed-count 8 \
  --snapshot-stride 3 \
  --max-snapshots-per-episode 3 \
  --target-obstacle-distance 2.0 \
  --max-continuation-steps 12 \
  --device cpu \
  --run-dir runs/m698_fresh_trajectory_boundary_sampler_smoke
```

Smoke result:

```text
episodes_completed:        8
snapshots_collected:      24
normal_failed_rejected:   12
too_safe_rejected:        12
accepted_rows:             0
result_class:  too_safe_only
```

The smoke exposed an implementation issue in the first draft: snapshots were
selected too early in the episode. The sampler was corrected to rank per-episode
candidate snapshots by distance to a target obstacle distance before enforcing
`max_snapshots_per_episode`.

## Registered Command

```bash
rm -rf runs/m698_fresh_trajectory_boundary_sampler && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.fresh_trajectory_boundary_sampler \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --seed-start 30000 \
  --seed-count 512 \
  --snapshot-stride 3 \
  --max-snapshots-per-episode 8 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m698_fresh_trajectory_boundary_sampler
```

## Artifacts

```text
runs/m698_fresh_trajectory_boundary_sampler/summary.json
runs/m698_fresh_trajectory_boundary_sampler/episode_summary.csv
runs/m698_fresh_trajectory_boundary_sampler/snapshot_candidates.csv
runs/m698_fresh_trajectory_boundary_sampler/prepass_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/perturbation_rollouts.csv
runs/m698_fresh_trajectory_boundary_sampler/accepted_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/rejected_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/source_summary.csv
runs/m698_fresh_trajectory_boundary_sampler/split_summary.csv
runs/m698_fresh_trajectory_boundary_sampler/skipped_windows.csv
```

## Result

Implementation cleanliness passed:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

Fresh scenario sampling ran:

```text
episodes_attempted:     512
episodes_completed:     512
snapshots_collected:   4056
prepass_rows:          4056
```

Normal prepass result:

```text
normal_failed_rejected: 1360
too_safe_rejected:     2168
perturbation_evaluated_rows: 528
```

No accepted source rows were found:

```text
trajectory_boundary_rows:      0
history_action_critical_rows:  0
terminal_cliff_rows:           0
accepted_rows:                 0
fresh_source_positive:     false
result_class:   fresh_surface_empty
```

Sensitivity was finite but far below threshold:

```text
margin_sensitivity_mean: 0.000338
margin_sensitivity_p95:  0.001687
risk_sensitivity_mean:   0.000338
risk_sensitivity_p95:    0.001687
threshold:               0.020000
success_flip_count:      0
collision_flip_count:    0
off_road_flip_count:     0
spin_flip_count:         0
```

## Interpretation

M698 is a clean implementation pass and a negative source result.

Allowed claim:

```text
Fresh broad sampling over 512 episodes produced complete artifacts and did not
mutate the actor, but under the registered snapshot window, perturbation grid,
and thresholds it did not find terminal-margin-sensitive rows.
```

Rejected claim:

```text
The current fresh sampler has produced a source corpus suitable for objective
design, actor update, PPO, promotion, or self-ID proof.
```

The result says the current sampling recipe is still not hitting a useful
closed-loop terminal-boundary manifold. The distribution is dominated by:

```text
already failed rows
or rows that pass with too much margin
or boundary-window rows whose small action perturbations barely change margin
```

## Failure Taxonomy

Primary label:

```text
scenario_sampling_failure
```

Reason:

```text
The registered fresh sampler did not produce accepted terminal-boundary rows.
```

Secondary label:

```text
metric_artifact risk
```

Reason:

```text
Earlier exact output metrics and now fresh broad sampling still do not expose
the terminal-margin-sensitive source required for closed-loop evidence.
```

Not classified as:

```text
contract_violation:
  actor inputs were unchanged

training_instability:
  no training occurred

proof_washout:
  actor parameters were unchanged
```

## Decision

Do not:

```text
design an objective from accepted_rows=0
run actor update
run PPO
promote a checkpoint
claim trajectory-boundary or self-ID source success
```

Do:

```text
run M699 audit/synthesis
inspect whether the failure is caused by snapshot windowing, perturbation scale,
or a base-driver distribution that is too bimodal
decide before any new sampler variant
```

## Validation

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_fresh_trajectory_boundary_sampler.py \
  tests/test_trajectory_terminal_boundary_source_miner.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

## Decision String

```text
fresh_trajectory_boundary_sampler_empty_admit_audit
```

## Next

```text
m699-fresh-trajectory-boundary-sampler-audit
```
