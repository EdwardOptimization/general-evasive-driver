# M312 M310 Protected-Key Window Failure Audit

M312 audits why M310 repaired passed exact objectives and replay gates but
failed protected key `9944|perturbed|28|28`. No PPO was run, no actor update was
run, and M310 remains rejected.

## Gate Parameters

The protected key is replayed through the M133 reference manifest. Its relevant
acceptance window is:

| Field | Value |
| --- | ---: |
| min_margin_gap | 0.005 |
| min_normal_margin | 0.0 |
| max_normal_margin | 0.2 |
| require_normal_success | true |

## Protected-Key Result

M311 guard result:

```text
runs/m311_full_public_gate_for_m310_repaired/full_gates/critical_key_seed9944
```

| Policy | Accepted | Normal success | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | --- | ---: | ---: | ---: |
| m263_a005 | true | true | 0.199909 | 0.099300 | 0.100609 |
| m307_base | true | true | 0.198863 | 0.098839 | 0.100023 |
| m310_repaired | false | true | 0.206337 | 0.108747 | 0.097590 |
| m239_a750 | false | true | 0.200336 | 0.099817 | 0.100519 |

The selected protected row for M310 has:

```text
perturbed_margin_gap_accept = true
perturbed_accepted_outcome_sensitive = false
```

So the failure is not caused by losing wrong-history sensitivity. The margin
gap remains far above `0.005`. The failure is caused by the upper normal-margin
window: M310's protected-key normal margin is `0.206337`, above the `0.2`
maximum.

## Comparison To M307

Delta from M307 to M310 on the protected key:

| Metric | Delta |
| --- | ---: |
| normal margin | +0.007475 |
| wrong-history margin | +0.009908 |
| margin gap | -0.002433 |

M310 makes both correct-history and wrong-history branches safer on this one
protected key. The wrong-history branch becomes safer slightly more, so the
gap shrinks, but it remains large enough for the margin-gap condition.

## Classification

This is best classified as:

```text
protected_key_window_failure
promotion_gate_failure
```

It is not a broad `proof_washout`:

- six replay surfaces pass;
- M183/M170 and M267/M264 retain `17/17` success drops;
- the protected key still has a large margin gap;
- the guard remains discriminative because M307 passes and `m239_a750` fails.

It is also not safe to bypass as a stale singleton. The key is narrow and
window-limited, but it remains an active promotion veto under the registered
gate. The correct next step is to test whether the M310 direction can be kept
inside the protected-key window with a smaller trust-region move.

## Next Repair Path

The most direct next experiment is a protected-key-bounded interpolation from
M307 to M310:

```text
theta(alpha) = (1 - alpha) * M307 + alpha * M310_repaired
```

The expected protected-key crossing is around:

```text
alpha ~= (0.2 - 0.198863) / (0.206337 - 0.198863) ~= 0.15
```

M313 should therefore sweep small alphas, check exact M297/M270 and protected
key first, then run M183/M170 and M267/M264 first replay only for the selected
protected-key-safe alpha.

## Decision

Do not promote M310.

Admit:

```text
m313-m310-protected-key-bounded-interpolation-probe
```

Decision:

```text
admit_m313_protected_key_bounded_interpolation_probe
```
