# M419 Active-Set Radius Anchor Export Implementation

M419 implements the export-only infrastructure admitted by M418. It does not run
projection, PPO, promotion, threshold changes, or actor-input changes.

## Code Changes

New exporter:

```text
src/autodrift/active_set_radius_anchor.py
```

The exporter:

1. reads the M416 zero-radius active-set anchor;
2. filters M417 old-key targeted replay failures for the spillover guard cases;
3. reuses the old-key replay-failure trajectory exporter to reconstruct those
   spillover wrong-history trajectories from the M400 base;
4. writes conservative, medium, and loose active-set v2 anchors with explicit
   per-row `radius`;
5. records source-level metadata for each profile.

The active-set v2 anchor keeps the M416 five sources and adds two old-key
spillover guards:

| Source | Rows | Role |
| --- | ---: | --- |
| M267/M264 row `6` | `40` | active |
| M267/M264 row `15` | `34` | active |
| old-key `10004...0.800000` | `37` | active |
| old-key `9998...1.400000` | `40` | active |
| old-key `10023...1.200000` | `41` | guard |
| old-key `9951...1.400000` | `40` | spillover guard |
| old-key `9939...1.400000` | `42` | spillover guard |
| total | `274` |  |

## Export Artifacts

Run directory:

```text
runs/m419_active_set_radius_anchor
```

Primary anchors:

```text
runs/m419_active_set_radius_anchor/conservative_radius_anchor.npz
runs/m419_active_set_radius_anchor/medium_radius_anchor.npz
runs/m419_active_set_radius_anchor/loose_radius_anchor.npz
```

Source metadata:

```text
runs/m419_active_set_radius_anchor/radius_anchor_sources.csv
```

Spillover rows:

```text
runs/m419_active_set_radius_anchor/spillover_failed_rows.csv
```

## Radius Profiles

| Source group | Conservative | Medium | Loose |
| --- | ---: | ---: | ---: |
| M267 rows `6` and `15` | `0.00015` | `0.00030` | `0.00045` |
| old-key `10004` | `0.00035` | `0.00050` | `0.00065` |
| old-key `9998` | `0.00008` | `0.00012` | `0.00018` |
| old-key `10023` | `0.00020` | `0.00035` | `0.00050` |
| old-key spillover guards | `0.00008` | `0.00015` | `0.00025` |

Each profile has `274` rows and explicit finite nonnegative radii.

## No-Update Smokes

All smokes use M400 as both base and raw checkpoint, `steps=0`, and the exact
M297/M270/old-key corpora. This checks loadability and exact feasibility only.

| Profile | Run dir | Rows | Replay loss | Exact pass |
| --- | --- | ---: | ---: | --- |
| conservative | `runs/m419_conservative_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |
| medium | `runs/m419_medium_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |
| loose | `runs/m419_loose_radius_anchor_no_update_smoke` | `274` | `0.0` | `true` |

For all three profiles:

```text
exact M297 delta vs base: 0.0
exact M270 delta vs base: 0.0
old-key surrogate delta vs base: 0.0
```

## Tests

Focused radius-export tests:

```text
tests/test_active_set_radius_anchor.py
```

Result:

```text
3 passed
```

## Decision

Admit:

```text
m420-active-set-radius-projection-probe
```

M420 should run the no-PPO projection probe in the M418 order:

```text
medium -> conservative if proof fails -> loose if proof passes but recovery < 0.20
```

The probe must keep exact M297/M270/old-key no-regression, M267/M264 `17/17`,
old-key compact `0` accepted regressions, M183/M170 `17/17`, and recovery
retention `>= 0.20` for a primary pass.
