# M231 Protected-Key Snippet Surface Export

M231 exports a deployable snippet/action-anchor surface for the historical
protected key before any more PPO. No PPO is run in this milestone.

Actor inputs are unchanged.

## Export

The protected key comes from the M229 critical-key replay guard:

```text
9944|perturbed|28|28
```

The export reruns snapshot-bank relocation from the M224 reference checkpoint
with the exact protected-key relocation geometry:

| Field | Value |
| --- | ---: |
| seed | 9944 |
| source condition | perturbed |
| source step | 28 |
| paired step | 28 |
| obstacle x | 11.0 |
| obstacle y | -1.0 |
| obstacle half width | 0.9 |

Artifacts:

```text
runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
runs/m231_protected_key_snippet_surface/protected_key_snippets.csv
runs/m231_protected_key_snippet_surface/protected_key_validation.json
runs/m231_protected_key_snippet_surface/summary.json
```

## Validation

The exported NPZ is compatible with the PPO snippet-action-anchor loader:

| Array | Shape | Finite |
| --- | ---: | ---: |
| observation | 1 x 72 | true |
| preferred_hidden | 1 x 128 | true |
| rejected_hidden | 1 x 128 | true |
| preferred_action | 1 x 3 | true |
| weight | 1 | true |

The row is exactly the protected key:

| Key | Normal margin | Wrong-history margin | Margin gap | Weight |
| --- | ---: | ---: | ---: | ---: |
| 9944\|perturbed\|28\|28 | 0.186385 | 0.086925 | 0.099460 | 0.051482 |

Validation loaded the NPZ through:

```text
load_outcome_intervention_snippets(obs_dim=72, hidden_size=128, act_dim=3)
```

and confirmed one positive finite-weight row.

## Interpretation

M230 showed that M229 protected the M223 proof surface but not the historical
9944 protected key. M231 makes that missing proof row explicit as a deployable
snippet/action-anchor surface. This is not a driver promotion and does not
change the protected-key threshold.

## Decision

M231 completes as infrastructure.

Next blocker:

```text
m232-protected-key-combined-snippet-anchor-corpus
```

M232 should combine the M223 proof-surface snippets with the M231 protected-key
snippet into one validated anchor corpus before any protected-key-aware PPO
repair.
