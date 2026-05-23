# M422 Mixed-Radius Anchor Export Implementation

M422 implements the mixed-radius export path designed in M421. It does not run
projection, PPO, promotion, threshold changes, or actor-input changes.

## Code Changes

`src/autodrift/active_set_radius_anchor.py` now supports profile sets:

```text
base  -> conservative, medium, loose
mixed -> mixed_a, mixed_b, mixed_c
all   -> base + mixed profiles
```

The M421 mixed profiles are:

| Profile | M267 rows | `10004` | `9998` | `10023` | spillovers |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mixed_a` | `0.00030` | `0.00050` | `0.00012` | `0.00020` | `0.00015` |
| `mixed_b` | `0.00030` | `0.00065` | `0.00012` | `0.00020` | `0.00015` |
| `mixed_c` | `0.00045` | `0.00065` | `0.00012` | `0.00020` | `0.00015` |

This keeps old-key `10023` tight while opening slack on rows that did not fail
the M420 medium proof gate.

## Export Artifacts

Run directory:

```text
runs/m422_mixed_radius_anchor
```

Primary anchors:

```text
runs/m422_mixed_radius_anchor/mixed_a_radius_anchor.npz
runs/m422_mixed_radius_anchor/mixed_b_radius_anchor.npz
runs/m422_mixed_radius_anchor/mixed_c_radius_anchor.npz
```

Each profile has:

```text
rows: 274
base active-set rows: 192
spillover rows: 82
```

Source metadata:

```text
runs/m422_mixed_radius_anchor/radius_anchor_sources.csv
```

## No-Update Smokes

All smokes use M400 as both base and raw checkpoint, `steps=0`, and the exact
M297/M270/old-key corpora. This checks loadability and exact feasibility only.

| Profile | Run dir | Rows | Replay loss | Exact pass |
| --- | --- | ---: | ---: | --- |
| `mixed_a` | `runs/m422_mixed_a_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |
| `mixed_b` | `runs/m422_mixed_b_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |
| `mixed_c` | `runs/m422_mixed_c_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |

For all three profiles:

```text
exact M297 delta vs base: 0.0
exact M270 delta vs base: 0.0
old-key surrogate delta vs base: 0.0
```

## Tests

Focused tests:

```text
tests/test_active_set_radius_anchor.py
```

Result:

```text
4 passed
```

## Decision

Admit:

```text
m423-mixed-radius-projection-probe
```

M423 should run no-PPO exact projection in M421 order:

```text
mixed_a -> mixed_b if proof passes but utility is still below threshold -> mixed_c if mixed_b proof passes but utility is still below threshold
```

If any mixed profile fails proof, stop and audit the newly active row. Do not
run PPO or lower thresholds.
