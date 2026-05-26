# M960 V4 Public Base Low-Tail Direction-Family Target Audit Implementation

## Purpose

M960 implements the no-training direction-family target audit designed in M959.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_low_tail_direction_family_target_audit
```

## Artifacts

```text
runs/m960_v4_public_base_low_tail_direction_family_target_audit/summary.json
runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_family_summary.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_rows.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/normal_retention_metrics.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/m267_direction_target_preflight.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/route_decision.csv
```

## Implementation

M960 adds:

```text
src/autodrift/public_base_low_tail_direction_family_target_audit.py
tests/test_public_base_low_tail_direction_family_target_audit.py
```

The audit evaluates:

```text
direction families: 10
target family rows: 50
amplitudes: 0.001, 0.002, 0.004, 0.006, 0.008
evaluated low-tail rows: 64
M267/M264 active rows: 6, 13, 15, 16
```

It keeps four checks separate:

```text
normal retention
terminal-margin behavior grounding
old low-tail proxy compatibility
M267/M264 branch-separated proof retention
```

The old low-tail proxy is reported but does not override terminal-margin
grounding. This matters because M958 showed the old proxy is anti-aligned for
the away/toward intervention pair.

## Result

```text
result_class: low_tail_direction_family_target_audit_joint_candidate
direction_target_family_count: 50
normal_retained_family_count: 29
behavior_grounded_family_count: 20
m267_target_preflight_pass_count: 30
joint_direction_target_candidate_count: 20
primary_joint_candidate_count: 20
best_joint_candidate_family: throttle_minus_amp_0_0080
```

All joint candidates come from primary M959 families:

```text
brake_plus:
  amplitudes 0.001, 0.002, 0.004, 0.006, 0.008

steer_minus_brake_plus:
  amplitudes 0.001, 0.002, 0.004, 0.006, 0.008

throttle_minus:
  amplitudes 0.001, 0.002, 0.004, 0.006, 0.008

toward_intervention:
  amplitudes 0.001, 0.002, 0.004, 0.006, 0.008
```

The best candidate by p10/mean margin and drift ordering is:

```text
throttle_minus_amp_0_0080:
  terminal_margin_mean_delta: +0.00009178
  terminal_margin_p10_delta: +0.00004844
  positive_margin_fraction: 1.000000
  normal_retention_pass: true
  M267/M264 proof preflight: true
```

Diagnostic-only anti-aligned families are not accepted:

```text
away_from_intervention
throttle_plus
brake_minus
steer_plus
```

## Interpretation

M960 changes the branch state. M954-M956 did not find feasible targets because
they moved along an action-gap direction that M958 later showed was
behaviorally sign-wrong. Once the target family is selected from
terminal-margin-improving directions, normal-retained and proof-retained
targets exist.

Supported:

- target-space feasibility is not exhausted;
- M958 behavior-improving primary families are valid candidate target sources;
- anti-aligned proxy-improving families should stay diagnostic-only;
- M267/M264 active proof retention is not the blocker for these targets when
  wrong-history targets remain branch-separated and anchored.

Falsified:

- low-tail target feasibility failure means no target-space route exists;
- actor training should use the old away-from-intervention target direction;
- old low-tail proxy improvement is sufficient for target acceptance.

## Next Blocker

M960 routes to:

```text
m961-v4-public-base-direction-target-export-actor-fit-objective-design
```

M961 should design the direction-target export and actor-fit objective around
the accepted M960 primary candidates. It must still block PPO, promotion,
private holdout, and actor-input changes until exact target-fit and replay
gates are specified.
