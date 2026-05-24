# M711 Cross-Fault Hidden-Action Gap Audit

## Purpose

M711 audits the M710 `action_washout` result before any source export, actor
update, PPO, or further scenario mining.

This milestone is process-only:

```text
no rerun
no source corpus export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M710 implementation was clean:

```text
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

M710 generated:

```text
scenario_count:       9728
snapshot_count:      33026
matched_pair_count:   2048
row_count:            4096
wrong_rows:           2048
reset_rows:           2048
```

Main result:

```text
result_class: action_washout
history_incompatibility_positive: false
```

Wrong-history counts:

```text
wrong_raw_positive_rows:       1653 / 2048
wrong_fused_positive_rows:     1365 / 2048
wrong_action_positive_rows:       0 / 2048
wrong_outcome_positive_rows:      0 / 2048
wrong_joint_positive_rows:        0 / 2048
```

Reset-hidden counts:

```text
reset_action_positive_rows:    2014 / 2048
reset_outcome_positive_rows:     15 / 2048
```

## Key Metrics

| Variant | Raw Hidden L2 Mean | Next Hidden L2 Mean | Fused Feature L2 Mean | Action L2 Mean | Action L2 P95 | Action L2 Max | Margin Gap Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wrong history | 0.101285 | 0.043808 | 0.015664 | 0.001587 | 0.005282 | 0.013204 | 0.000349 |
| reset hidden | 0.653912 | 0.266605 | 0.099829 | 0.020228 | 0.025853 | 0.033014 | 0.036786 |

Retention ratios:

| Variant | Next / Raw | Fused / Raw | Action / Fused |
| --- | ---: | ---: | ---: |
| wrong history | 0.435647 | 0.155083 | 0.092014 |
| reset hidden | 0.406729 | 0.152615 | 0.202227 |

Wrong-history signal reaches fused features, but the action head maps it to
small action changes:

```text
wrong fused positive rows:  1365
wrong action positive rows:    0
```

## Supported Claims

M711 supports:

```text
1. The M707/M708 wrong-history failure is not because cross-fault histories are
   absent in recurrent state.

2. The GRU update does not fully erase cross-fault wrong-history differences.

3. The response/context fusion does not fully erase cross-fault wrong-history
   differences.

4. The current actor action map suppresses those differences below the
   behaviorally meaningful action threshold.

5. Continued current-model scenario mining is now lower leverage than auditing
   how fused history directions couple to actor actions.
```

## Falsified Claims

M711 falsifies:

```text
1. M707 was negative simply because wrong histories were identical to normal
   histories at every internal level.

2. The immediate blocker is raw recurrent-state collapse.

3. The immediate blocker is full response/context fusion collapse.

4. Raw hidden or fused feature distance alone is sufficient self-ID proof.

5. M710 rows are ready for source export or PPO.
```

M711 does not falsify:

```text
the ideal driver hypothesis
```

because this actor was not trained with an objective that makes cross-fault
history directions behaviorally relevant.

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
Feature-level separability exists, but treating raw/fused feature distance as
closed-loop self-identification proof would overclaim the metric. The deployed
action and margin evidence is still negative.
```

Not classified as:

```text
scenario_sampling_failure:
  M710 found a signal in 1653 raw-positive and 1365 fused-positive rows.

training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Public Gate Overfit Risk

The main risk is now:

```text
feature-distance overclaiming
```

A diagnostic can find hidden/fused feature differences while the deployed
policy still ignores them. Future gates must require action or outcome
relevance before any source export or PPO.

The secondary risk remains:

```text
reset-hidden overclaiming
```

Reset hidden is disruptive, but that does not prove a correct fault-specific
capability belief.

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Close branch:

```text
extreme_hidden_condition_scenario_generation
```

New branch:

```text
actor_head_history_signal_coupling
```

Next evidence axis:

```text
G_action_head_coupling:
determine whether the current actor head is insensitive to cross-fault fused
history directions, whether those directions need amplification, or whether the
policy must be trained with an explicit history-to-action objective.
```

Next blocker:

```text
m712-actor-head-history-signal-coupling-design
```

M712 should design a no-training actor-head sensitivity audit:

```text
1. Reconstruct normal and wrong fused features for M710-style pairs.
2. Measure actor-head pre-tanh projection of wrong feature deltas.
3. Measure tanh derivative attenuation.
4. Compare wrong-history directions against reset-hidden directions.
5. Compute a feature-delta amplification line search:
   smallest alpha where action_l2 >= 0.015.
6. Report whether the blocker is:
   - actor_head_projection_washout,
   - tanh_saturation_washout,
   - feature_delta_too_small,
   - action_near_threshold_but_outcome_insensitive.
```

Do not run actor update, PPO, or source export before this audit design.
