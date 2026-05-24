# M720 Temporal Action-Only Audit

## Purpose

M720 audits the M719 `temporal_action_only` result before any source export,
objective design, actor update, PPO, or checkpoint promotion.

This milestone is process-only:

```text
no rerun
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M719 implemented a no-training temporal command-response mismatch runner and
ran the full registered wave:

```text
scenario_count: 16896
snapshot_count: 72056
matched_pair_count: 4096
row_count: 42994
result_class: temporal_action_only
```

Main result:

```text
temporal_action_critical_rows: 3114
temporal_outcome_critical_rows: 0
reset_action_critical_rows: 3140
reset_outcome_critical_rows: 0
normal_history_retention_pass: true
```

Dominant variant:

```text
mismatch_zero_command_history:
  action-critical rows: 3064
  action distance mean: 0.021019
  action distance max:  0.036131
  margin gap max:       0.006888
```

Contrast variants:

```text
cross_fault_wrong_hidden:
  action-critical rows: 0
  action distance max:  0.012664

reset_hidden:
  action-critical rows: 3140
  margin gap max:       0.005486

delayed_hidden_20:
  action-critical rows: 22
  margin gap max:       0.001659

pre_fault_stale_hidden:
  action-critical rows: 22
  margin gap max:       0.000755
```

Cleanliness:

```text
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

## What This Means

M719 is not a failed implementation. It successfully found a strong action-level
temporal signal:

```text
the actor's action head depends heavily on previous physical-command history.
```

This is closer to the driver-like command-response claim than the earlier
cross-fault hidden swaps. However, the current scenarios do not convert that
action difference into clearance margin, collision, or success changes.

The current evidence is therefore:

```text
action-level temporal coupling: strong
closed-loop outcome causality: not yet shown
```

## Supported Claims

M720 supports:

```text
1. The actor is not ignoring command-response history. Zeroing previous command
   history inside the recurrent stream changes actions on many rows.

2. Cross-fault hidden injection was too weak as a temporal intervention; it
   remains below the action threshold on the same broad scenario family.

3. Reset-hidden degradation and zero-command-history mismatch now point to a
   real temporal/action coupling signal.

4. The next useful evidence axis should ask when this action delta matters for
   collision margin.
```

## Falsified Claims

M720 falsifies:

```text
1. The actor has no temporal command-response action dependence.

2. Current M719 action-only evidence proves closed-loop self-identification.

3. The project should proceed directly to PPO or checkpoint promotion.

4. Another broad current-model fault coverage wave is the highest-leverage next
   step.
```

M720 does not falsify:

```text
1. Temporal command-response mismatch may become outcome-critical under sharper
   obstacle timing, lateral offset, or boundary-margin scenarios.

2. Actor-head/residual objective design may still be useful after an outcome
   boundary corpus exists.

3. True asymmetric vehicle faults may still require a higher-fidelity dynamics
   branch.
```

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
The strongest M719 evidence is action-distance evidence. It would be a metric
artifact to report it as closed-loop self-ID without margin or success effects.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observation contract was unchanged.

scenario_sampling_failure:
  M719 did find many action-sensitive temporal rows; the missing part is
  outcome conversion, not raw sample absence.
```

## Public Gate Overfit Risk

The active risk is:

```text
zero-command-history overclaiming
```

`mismatch_zero_command_history` is a strong but synthetic intervention. It says
the recurrent policy uses command-history features, but it does not by itself
prove realistic delayed/stale/wrong history causes collision or recovery
failure.

Future gates must separate:

```text
action sensitivity
outcome sensitivity
realistic temporal corruption
source-positive self-ID proof
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close branch:

```text
temporal_action_response_mismatch
```

Next branch:

```text
temporal_action_boundary_outcome_mining
```

Next evidence axis:

```text
G_action_to_outcome:
use M719 temporal action-sensitive rows to mine near-boundary scenarios where
the temporal action delta changes clearance margin or success.
```

Next blocker:

```text
m721-temporal-action-boundary-outcome-mining-design
```

M721 should design a no-training miner that starts from M719 high-action-delta
rows, especially `mismatch_zero_command_history`, and searches local obstacle
timing / lateral offset / boundary-margin variants for:

```text
normal history succeeds or has nonnegative margin
temporal mismatch action changes by >= 0.015
temporal mismatch margin gap >= 0.02 or success drops
source diversity across fault families and seeds
```

Direct actor update, PPO, source export, and promotion remain blocked until this
outcome bridge exists.
