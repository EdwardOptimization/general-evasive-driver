# M958 V4 Public Base Low-Tail Target Metric Artifact Audit Implementation

## Purpose

M958 implements the no-training metric-grounding audit designed in M957.

It does not train, update model weights, run PPO, change actor inputs, relax
thresholds, use private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_low_tail_metric_artifact_audit
```

## Artifacts

```text
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/summary.json
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/direction_family_summary.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/row_metric_grounding.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/proxy_behavior_correlation.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/route_decision.csv
```

## Implementation

M958 adds:

```text
src/autodrift/public_base_low_tail_metric_artifact_audit.py
tests/test_public_base_low_tail_metric_artifact_audit.py
```

The audit evaluates 10 direction families over `64` low-tail rows and three
amplitudes:

```text
direction families:
  away_from_intervention
  toward_intervention
  steer_plus / steer_minus
  brake_plus / brake_minus
  throttle_plus / throttle_minus
  steer_plus_brake_plus / steer_minus_brake_plus

amplitudes:
  0.004, 0.006, 0.008
```

For each row, it compares:

```text
proxy:
  normal_intervention_gap_delta
  gap_deficit_delta
  low_tail_proxy_improved

behavior:
  terminal_margin_delta
  behavior_improved
  success_delta
  collision_delta
```

## Result

```text
result_class: low_tail_metric_artifact_audit_direction_sign_suspicion
direction_family_count: 10
row_metric_count: 1920
proxy_improved_behavior_worse_family_count: 4
behavior_improved_family_count: 6
direction_sign_suspicion: true
target_metric_artifact: false
threshold_only_issue: false
```

The key comparison is:

```text
away_from_intervention:
  proxy_improved_fraction: 1.000000
  behavior_improved_fraction: 0.000000
  proxy_improved_behavior_worse_fraction: 1.000000
  terminal_margin_mean_delta: -0.000057

toward_intervention:
  proxy_improved_fraction: 0.000000
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000057
```

This is a direction-sign result: the current low-tail proxy says moving away
from the intervention action is good, but closed-loop terminal margin says the
opposite direction is better on the sampled rows.

Other behavior-improving directions:

```text
throttle_minus: behavior_improved_fraction 1.000000
brake_plus: behavior_improved_fraction 1.000000
steer_minus_brake_plus: behavior_improved_fraction 1.000000
steer_minus: behavior_improved_fraction 0.828125
steer_plus_brake_plus: behavior_improved_fraction 0.812500
```

## Interpretation

This is not a threshold-only issue. If thresholds were the main blocker, proxy
improvement and terminal-margin improvement would be directionally aligned and
the candidate would simply miss a cutoff. Instead, the proxy and behavior are
anti-aligned for the primary away/toward intervention pair.

This is also not a pure "all proxy metrics are meaningless" result. Some
directions such as `brake_plus` improve both proxy and behavior. The issue is
that the existing low-tail target construction used the wrong family of action
directions for these rows.

Supported:

- Low-tail action-gap proxy is not sufficient by itself.
- The current away-from-intervention direction is sign-wrong for closed-loop
  terminal margin on this sample.
- Several simple action families improve margin and should be audited as
  candidate target directions.

Falsified:

- The M954/M956 away-from-intervention target direction is behaviorally
  grounded.
- The current blocker is merely a strict threshold artifact.
- Actor training is justified before target-direction redefinition.

## Next Blocker

M958 routes to:

```text
m959-v4-public-base-low-tail-direction-family-target-audit-design
```

M959 should design a no-training audit that converts the behavior-improving
direction families into target candidates, while keeping normal retention and
M267/M264 proof retention explicit.
