# M1200 Paper-Route Fair Comparison Pilot Result Audit

## Summary

M1200 audits the M1199 public pilot before increasing the profile-comparison
budget.

Decision:

```text
fair_comparison_pilot_audit_route_to_profile_separability_audit
```

The M1199 pilot is valid as a public pilot trend, but it should not be scaled
directly into a longer comparison yet. The next step should first verify that
the L0/L1/L2/L3 profiles are behaviorally and architecturally separated enough
for a larger training result to be meaningful.

## Evidence Checked

Source artifacts:

```text
runs/m1199_fair_comparison_pilot/summary.json
runs/m1199_fair_comparison_pilot/profile_seed_rows.csv
runs/m1199_fair_comparison_pilot/profile_aggregate.csv
docs/m1199-paper-route-fair-comparison-pilot-run.md
```

Completion remains clean:

```text
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

So M1199 is not rejected for plumbing, masking, finite-metric, or protocol
reasons.

## Public Pilot Trend

M1199 supports only this limited claim:

```text
Under a short fixed public training budget, finite-window L2 profiles show the strongest public pilot trend.
```

Aggregate metrics:

| Profile | Success | Collision | Mean Margin | Return |
| --- | ---: | ---: | ---: | ---: |
| `L0_current_masked` | 0.1458 | 0.8333 | 0.1072 | 27.0871 |
| `L1_one_step` | 0.2969 | 0.6562 | 0.3505 | 35.6983 |
| `L2_window_13` | 0.3854 | 0.4219 | 0.7175 | 36.6199 |
| `L2_window_25` | 0.3854 | 0.4219 | 0.7189 | 36.6392 |
| `L2_window_50` | 0.3854 | 0.4219 | 0.7189 | 36.6392 |
| `L2_window_100` | 0.3854 | 0.4219 | 0.7189 | 36.6392 |
| `L3_online_gru` | 0.2552 | 0.7448 | 0.2726 | 35.4705 |
| `L3_reset_control` | 0.2656 | 0.7135 | 0.2934 | 36.1018 |

This is enough to justify more investigation of finite-window feedback. It is
not enough to select a final architecture.

## L2 Window-Equivalence Audit

The L2 window profiles have different observation dimensions:

| Profile | Observation Dim | Parameter Count |
| --- | ---: | ---: |
| `L2_window_13` | 936 | 29895 |
| `L2_window_25` | 1800 | 29895 |
| `L2_window_50` | 3600 | 29895 |
| `L2_window_100` | 7200 | 29895 |

The parameter count is identical because the temporal GRU uses a shared
per-frame encoder and fixed hidden size. Extra window length changes the number
of unrolled frames, not model capacity.

Classification:

```text
inconclusive_but_suspicious
```

Reasons:

- `L2_window_25`, `L2_window_50`, and `L2_window_100` are nearly identical in
  success, collision, margin, return, and seed-level pattern.
- `L2_window_13` is also very close, with only small margin differences.
- This may be expected if the current task distribution and short training
  budget only require the recent response frame.
- It may also mean the profile implementation or temporal encoder is not
  creating meaningful older-history use.

The audit cannot distinguish those explanations from aggregate metrics alone.

## L3 Reset-Parity Audit

M1199 compares:

```text
L3_online_gru success/collision/margin:    0.2552 / 0.7448 / 0.2726
L3_reset_control success/collision/margin: 0.2656 / 0.7135 / 0.2934
```

Classification:

```text
negative_for_recurrent_hidden_benefit_in_this_pilot
```

Reasons:

- Reset control is not worse than online GRU in this short pilot.
- Both profiles share the same seed-fragility pattern: one seed is much better,
  two seeds are weak.
- This does not prove online GRU is bad; it only says M1199 does not show useful
  accumulated-hidden-state contribution.

This is consistent with the project's self-identification discipline: robust
closed-loop behavior is not recurrent belief. History necessity still needs
same-current, delayed-history, wrong-history, and reset/zero-history tests.

## Route Decision

Do not immediately run a longer M1199-style profile comparison.

Next route:

```text
m1201-paper-route-profile-separability-audit
```

M1201 should audit, without training:

```text
1. whether generated profile configs differ exactly as intended;
2. whether L2 history stacks contain distinct older frames under rollout;
3. whether trained L2 policies are action-sensitive to older-history ablations;
4. whether L3 online-GRU actions differ from reset-hidden actions on the same states;
5. whether the current short-budget pilot collapsed profiles because of task/budget rather than implementation.
```

Only after M1201 should the project choose between:

```text
repeat M1199 with a longer budget;
repair finite-window or L3 profile implementation;
add a history-necessity task distribution;
or design a stronger profile-comparison benchmark.
```

## Guardrails

No training, PPO, replay, promotion, private holdout, per-profile tuning, or
actor-input contract change occurred in M1200.

Unsupported:

```text
paper-level architecture ranking
L2 promotion
L3 rejection
GRU recurrent-belief advantage
self-identification
private-holdout generalization
```

## Next Milestone

```text
experiments/manifests/m1201-paper-route-profile-separability-audit.json
```
