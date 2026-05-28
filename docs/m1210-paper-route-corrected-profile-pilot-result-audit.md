# M1210 Paper-Route Corrected Profile Pilot Result Audit

## Summary

M1210 audits the M1209 corrected public pilot result before any repeat, longer
training, promotion, or paper-level interpretation.

Decision:

```text
corrected_profile_pilot_audit_route_to_fresh_repeat_design
```

No training, PPO, candidate replay, promotion, private holdout, profile tuning,
or actor-input change occurs in M1210.

## Artifact Validity

M1209 artifacts are complete:

```text
runs/m1209_corrected_profile_pilot/summary.json
runs/m1209_corrected_profile_pilot/profile_seed_rows.csv
runs/m1209_corrected_profile_pilot/eval_rows.csv
runs/m1209_corrected_profile_pilot/profile_aggregate.csv
```

Validity checks:

```text
result_class: corrected_profile_pilot_completed
completed_seed_runs: 24
failed_seed_runs: 0
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
actor_input_contract_changed: false
```

Runner/eval semantics are valid for this pilot. `corrected_profile_pilot.py`
evaluates checkpoints through:

```text
wrap_env_with_profile_mask(...)
ActorPolicy(..., reset_hidden_policy=profile_runtime_summary(config)["reset_hidden_policy"])
```

This means generated current-tiled controls and corrected reset-control
semantics are applied during the public evaluation, not just during training.

## L2 Current-Tiled Audit

Pair deltas are normal minus current-tiled control:

| Pair | Success Delta | Collision Delta | Mean Margin Delta | P10 Margin Delta | Return Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L2_window_13 - current_tiled` | +0.0208 | +0.0052 | -0.0419 | -0.0213 | +2.3101 |
| `L2_window_25 - current_tiled` | +0.0052 | +0.0208 | -0.0430 | -0.0126 | +1.4086 |

Classification:

```text
negative_for_finite_window_history_necessity
```

Reason:

```text
L2 normal has only tiny success gains, worse collision, and worse mean/p10 clearance margin than current-tiled controls.
Current-tiled controls therefore explain much of the L2 capacity trend.
```

This keeps current-frame substitution risk active. M1209 does not support a
claim that finite-window history is necessary.

## L3 Reset-Control Audit

Pair delta is online minus corrected reset-control:

| Pair | Success Delta | Collision Delta | Mean Margin Delta | P10 Margin Delta | Return Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `L3_online_gru - L3_reset_control_corrected` | 0.0000 | +0.0104 | +0.0404 | +0.0200 | +0.0115 |

Classification:

```text
positive_for_L3_architecture_family
inconclusive_for_recurrent_hidden_benefit
negative_for_strong_self_identification
```

Reason:

```text
L3 online and reset-control tie on success and termination.
Online has somewhat better clearance margins, but reset has slightly lower collision.
Both share the same seed-fragility pattern.
```

Per-seed success rates:

| Profile | Seed 110600 | Seed 110601 | Seed 110602 |
| --- | ---: | ---: | ---: |
| `L3_online_gru` | 0.1250 | 0.8281 | 0.1250 |
| `L3_reset_control_corrected` | 0.1094 | 0.8125 | 0.1562 |

This is not recurrent-belief evidence. It is a public pilot trend showing that
the L3 architecture family can train into a stronger reactive controller under
one seed block, with severe seed dependence.

## Overall Interpretation

Supported:

```text
M1209 is a valid corrected public pilot.
L3 family is stronger than L0/L1/L2 in this seed block.
The corrected controls are now strong enough to block over-interpretation.
```

Blocked:

```text
finite-window history necessity
GRU recurrent-hidden benefit
self-identification
profile promotion
private-holdout evaluation
paper-level architecture ranking
```

The most important result is not that L3 wins the aggregate. The important
result is that the corrected controls prevent the project from mistaking an
architecture-family trend for history/belief evidence.

## Decision

Do not scale to longer training yet. First run a fresh public repeat design.

Rationale:

```text
M1209 uses only one 3-seed public block.
L3 aggregate is driven by one strong seed.
L2 current-tiled controls remain competitive or safer.
The next experiment should test repeatability, not increase budget.
```

## Next Milestone

```text
experiments/manifests/m1211-paper-route-corrected-profile-repeat-design.json
```

M1211 should pre-register a fresh public repeat:

```text
same corrected profile set
same 8192-step budget
fresh training seed base
fresh eval seed base
same no-private-holdout/no-promotion/no-tuning rules
explicit interpretation rules for L2/current-tiled and L3/reset outcomes
```
