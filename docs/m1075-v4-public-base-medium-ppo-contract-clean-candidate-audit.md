# M1075 V4 Public Base Medium PPO Contract Clean Candidate Audit

## Purpose

M1075 audits the M1073 projection candidate table after M1074 rejected the
selected `line_row16x4_s40_a1` checkpoint as an allowed-surface contract
artifact.

This milestone does not run PPO, train the actor, promote, or use private
holdout.

## Inputs

```text
projection_metrics:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/projection_metrics.csv

M1074 full gate:
  runs/m1074_medium_ppo_repair_projection_full_public_gate/summary.json
```

Allowed changed parameter prefixes remain:

```text
actor_mean.
response_context_fusion.0.
```

M1075 does not weaken that contract.

## Result

The M1073 table contains contract-clean exact-pass alternatives:

```text
projection rows: 39
exact-pass contract-clean rows: 13
all clean rows changed_parameter_count: 4
all clean rows eligible_for_first_replay: true
all clean rows movement_retained_pass: true
```

The selected M1075 candidate is:

```text
label: m1031_base_row16x4_s40_a1
checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

changed_parameter_count: 4
changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight

exact_gate_pass: true
exact_m297_delta_vs_base: -0.0000852346420288086
exact_m270_delta_vs_base: -0.00006854534149169922
eligible_for_first_replay: true
movement_retained_pass: true
```

This is the strongest exact-pass contract-clean `m1031_base_row16x4_s40`
candidate by alpha and by M297/M270 exact deltas.

## Interpretation

M1074 should not be treated as proof washout. The closed-loop gate stack passed
for the broader `line` candidate, but that candidate inherited disallowed PPO
parameter movement. M1075 shows that the same M1073 projection run also
produced a contract-clean candidate that preserves the exact active-set
objectives and stays inside the intended repair surface.

That candidate still needs the full expanded public gate. M1075 only selects
the next checkpoint to test; it makes no promotion or behavior claim.

## Decision

```text
medium_ppo_contract_clean_candidate_audit_route_to_full_public_gate
```

Next:

```text
m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate
```
