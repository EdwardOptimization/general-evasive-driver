# M668 Normal-Success Boundary Source Miner Audit

## Purpose

M668 audits the negative M667 result before another source-mining or training
branch. The question is whether M667 failed because valid preferred windows are
missing, because wrong history has no action effect, or because wrong history
has first-action effects that do not persist or affect outcomes.

## M667 Evidence

M667 was implementation-clean:

```text
snapshot_count:                     644
near_boundary_preferred_snapshots:  204
candidate_pairs:                   3200
candidate_rows:                    9600
accepted_rows:                        0
actor_checksum_changed:           false
actor_checkpoint_written:         false
ppo_used:                         false
```

Normal window coverage:

```text
near_boundary_preferred: 204
early_safe_diagnostic:   296
already_failed:          144
```

By surface:

```text
fresh near_boundary_preferred: 108 rows, 38 seeds, 3 targets
ood near_boundary_preferred:    96 rows, 34 seeds, 2 targets
```

Near-boundary margins were valid:

```text
mean normal_margin: 0.520157
min normal_margin:  0.000474
max normal_margin:  0.997193
```

So M667 is not blocked by missing valid preferred windows.

## Wrong-History Effect

Wrong-history first-action sensitivity is present:

```text
wrong_first_action_l2 >= 0.002 rows: 8934 / 9600
max wrong_first_action_l2:           0.015159
```

But the effect is not strong enough as a short-horizon action sequence:

```text
wrong_action_sequence_mean_l2 >= 0.006 rows:        4
preferred/rejected action mean_l2 >= 0.010 rows:    0
max wrong_action_sequence_mean_l2:             0.006325
max preferred/rejected action mean_l2:         0.006325
```

And it has no outcome effect:

```text
margin_gap >= 0.010 rows: 0
success_drop_rate:        0.000
normal_success_rate:      1.000
wrong_success_rate:       1.000
max margin_gap:           0.000034
```

## Classification

M667 should be classified as:

```text
near_boundary_exists_but_wrong_history_outcome_insensitive
```

More specifically:

```text
first_action_gap_positive
short_horizon_action_gap_weak
outcome_gap_absent
```

This is different from M664:

```text
M664: action gaps existed mostly in already-failed normal states.
M667: valid near-boundary normal-success states exist, but wrong-history
      substitutions still do not affect outcome.
```

## Rejected Interpretations

Reject:

- `no_near_boundary_normal_success_windows`: M667 found `204`.
- `implementation_failure`: artifacts, checksum, and no-training guards are
  clean.
- `train_from_empty_corpus`: no accepted rows exist.
- `threshold_too_strict`: first-action gaps are common, but outcome gaps are
  near zero; lowering action thresholds would not create self-ID evidence.
- `self-ID unnecessary`: this only says the current BC5660 actor/outcome
  boundary is insensitive under these compatible wrong-history substitutions.

## Next Branch

Continuing source mining with the same actor is now lower leverage unless the
scenario distribution changes substantially. The next branch should address the
action boundary directly:

```text
response/history information reaches recurrent hidden;
some first-action sensitivity exists;
but the fused policy/action trajectory does not make history matter enough.
```

M669 should design an action-boundary response-amplification stage. It should
remain no-PPO initially and should not claim promotion. It should define a
shadow or tightly gated objective that:

```text
anchors normal-history action on valid near-boundary preferred windows;
increases sustained sequence separation for wrong-history hidden states;
keeps actor input contract unchanged;
uses full-corpus exact gates before any closed-loop actor update;
requires replay validation before promotion.
```

## Decision

```text
normal_success_boundary_source_miner_audit_admit_action_boundary_amplification_design
```

## Next

```text
m669-action-boundary-response-amplification-design
```
