# M696 Trajectory-Terminal Boundary Source-Miner Audit

## Purpose

M696 audits the M695 `surface_empty` result and decides whether the
`trajectory_terminal_boundary_source_mining` branch should continue.

This milestone is process-only:

```text
no mining rerun
no threshold relaxation
no objective design
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M695 implemented the miner cleanly:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

The command replayed the source rows inherited from M692:

```text
source rows:  runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
checkpoint:   runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
surfaces:     fresh, ood
first-action perturbations:
  steer +/- 0.01, +/- 0.02
  throttle +/- 0.03
  brake +/- 0.03
  steer/brake pairs
continuation: 40 steps
```

The run produced complete artifacts:

```text
summary.json
source_rows.csv
candidate_rows.csv
perturbation_rollouts.csv
accepted_rows.csv
source_summary.csv
split_summary.csv
rejected_rows.csv
```

Core result:

```text
rows_attempted:                  40
snapshots_collected:             45
normal_success_candidates:       15
normal_failed_rejected:          25
trajectory_sensitive_rows:        0
history_action_critical_rows:     0
terminal_cliff_rows:              0
accepted_rows:                    0
result_class:         surface_empty
```

Sensitivity was too small by two orders of magnitude:

```text
margin_sensitivity_mean: 0.000154
margin_sensitivity_p95:  0.000391
risk_sensitivity_mean:   0.000154
risk_sensitivity_p95:    0.000391
threshold:               0.020000
```

## Supported Claims

The evidence supports:

```text
1. M695 is a valid no-training source-mining implementation.

2. The M692/M671 inherited replay surface is not a terminal-margin-sensitive
   action-critical source surface.

3. The previous M689 output-level residual-head success should remain
   diagnostic-only.

4. Objective design, actor update, PPO, and promotion must remain blocked.
```

## Falsified Claims

The evidence falsifies:

```text
1. The current M692 replay rows can directly support a trajectory-boundary
   objective.

2. Loosening exact residual-head gates is enough to find closed-loop useful
   rows on this source.

3. M692 replay_neutral was only caused by a weak residual head; M695 shows the
   underlying source rows themselves are not trajectory-sensitive under the
   registered perturbations.
```

The evidence does not falsify:

```text
trajectory_terminal_boundary_source_mining as a branch
```

because M695 only tested the old M692 source rows. It did not sample fresh
scenario seeds, obstacle timings, speed bands, curvature bands, or hidden
dynamics ranges for terminal-boundary sensitivity.

## Failure Taxonomy Summary

Primary label:

```text
scenario_sampling_failure
```

Reason:

```text
The source rows inherited from M692 are stale for the new terminal-boundary
question. Most rows are either already normal-failed or insensitive.
```

Secondary label:

```text
metric_artifact
```

Reason:

```text
The M689 exact output metrics identified a residual-head diagnostic pass, but
those metrics did not identify a trajectory-sensitive closed-loop source.
```

Not classified as:

```text
training_instability:
  no training occurred

proof_washout:
  no actor parameters changed

contract_violation:
  P0 actor inputs were unchanged
```

## Public Gate Overfit Risk

The risk is confirmed.

The M669-M692 branch created progressively better exact output diagnostics on a
public source family. M695 then tested that family with closed-loop perturbation
replay and found no terminal-boundary source rows.

This means future work must not:

```text
reuse the same rows as if they were trajectory-sensitive
loosen thresholds to manufacture accepted rows
turn accepted_rows=0 into objective design
```

The next experiment must change the sampling distribution, not tune the same
public surface.

## Next Branch Decision

Synthesis decision:

```text
continue
```

Branch remains:

```text
trajectory_terminal_boundary_source_mining
```

But the source family changes:

```text
from:
  M692 replay rows

to:
  fresh broad scenario sampling with terminal-boundary prepass
```

Rationale:

```text
M695 only proves that the inherited M692 surface is empty. It does not prove
that fresh scenario sampling cannot find boundary-sensitive rows.
```

## Next Design Target

M697 should design a fresh sampler that does not depend on M692 rows.

It should:

```text
sample fresh scenario seeds across fresh and ood configs
collect multiple candidate snapshots per episode
filter for obstacle/boundary interaction windows
use normal-history continuation to reject already-failed rows
run local first-action perturbation sensitivity
run wrong/counterfactual-history sensitivity when pairable
write source-diverse accepted rows
```

It should not:

```text
train actor
run PPO
promote checkpoint
change actor inputs
call output-level residual gaps source evidence
```

## Decision String

```text
trajectory_boundary_source_empty_continue_with_fresh_sampling
```

## Next

```text
m697-fresh-trajectory-boundary-sampling-design
```
