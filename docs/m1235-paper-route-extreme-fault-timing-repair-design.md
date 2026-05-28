# M1235 Paper-Route Extreme Fault Timing Repair Design

## Summary

M1235 designs the next source-generation step after M1234 audited M1233 as a
normal-failure-dominated, reset-only source result.

Decision:

```text
extreme_fault_timing_repair_design_admit_smoke
```

The next run should not optimize for accepted wrong-history rows first. It
should first make the normal-history branch survive often enough that future
wrong-history degradation can be interpreted.

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1235.

## Problem To Repair

M1233 was a valid infrastructure smoke:

```text
scenario_count: 832
snapshot_count: 3211
matched_pair_count: 768
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

But the source shape was not proof-ready:

```text
accepted_rows: 0
wrong_history_action_critical_rows: 0
reset_only_rows: 58
normal_failed_rejected: 636
history_insensitive_rejected: 74
```

The main blocker is normal-history viability:

```text
normal_surviving_rows = matched_pair_count - normal_failed_rejected
normal_surviving_rows = 132 / 768
normal_surviving_fraction = 0.171875
```

If the normal branch fails, the row cannot support a causal wrong-history
claim. The first repair target is therefore normal survival, not accepted rows.

## Repair Principles

1. Normal-survival gates come before wrong-history accepted-row gates.
2. Hidden fault labels remain metadata only and never enter actor observation.
3. The repair must be config-level and bounded before any tooling or training
   work.
4. Accepted rows, reset-only rows, and sequence candidates are diagnostics at
   the repaired-smoke stage.
5. If normal survival improves but wrong-history remains zero, route to sequence
   intervention design rather than PPO.

## Timing And Horizon Levers

M1236 should adjust only source-generation timing and survival windows:

| Lever | M1233 value | M1236 repair value | Purpose |
| --- | ---: | ---: | --- |
| `max_continuation_steps` | 36 | 18 | reduce all-collision continuations and test short-horizon normal survival |
| `min_step` | 18 | 18 | keep early evidence comparable |
| `snapshot_stride` | 4 | 4 | keep source density comparable |
| `max_snapshots_per_scenario` | 4 | 5 | slightly improve per-seed source coverage |
| `obstacle_longitudinal_min` | -8.0 | -4.0 | avoid already-passed or too-late obstacle states |
| `obstacle_longitudinal_max` | 80.0 | 95.0 | allow earlier normal-surviving windows |
| `min_normal_margin` | 0.0 | 0.0 | keep the first repair focused on survival, not slack |

The fault families stay the same as M1233. Changing the fault distribution at
the same time would make the repair harder to interpret.

## M1236 First Bounded Implementation

M1236 should create a small repair config:

```text
configs/m1236_extreme_fault_timing_repair_smoke.json
```

It should copy the M990/M1233 fault families and pairing rules, changing only
the timing / horizon / obstacle-window values listed above.

Then run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 123600 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1236_extreme_fault_timing_repair_smoke
```

## M1236 Pass Criteria

M1236 should pass as a timing-repair smoke if:

```text
summary.json exists
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
matched fault-family pairs >= 10
matched seeds >= 12
normal_surviving_fraction >= 0.35
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
model_fidelity_limits.md exists
```

Accepted wrong-history rows are not required for this repair smoke.

If accepted rows appear, they are diagnostic and must still pass source-diversity
audit before any objective or PPO work.

## Failure Handling

If normal survival remains low:

```text
classify as timing/horizon repair failure
try a narrower family subset or shorter horizon in a new manifest
do not train or lower proof standards
```

If normal survival improves but wrong-history stays zero:

```text
route to sequence-level temporal intervention source design
```

If normal survival improves and accepted rows appear:

```text
audit source diversity before any training or objective design
```

If reset-only rows grow but remain seed-collapsed:

```text
record reset-only recurrent-disruption evidence and avoid self-ID claims
```

## Decision

```text
extreme_fault_timing_repair_design_admit_smoke
```

M1236 is admitted as a bounded no-training timing-repair smoke.
