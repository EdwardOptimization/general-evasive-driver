# M1721 Paper-Route Controller-Family Off-Track Repair Panel Preflight

- status: completed
- result class: `off_track_repair_panel_preflight_pass`
- artifact: `runs/m1721_off_track_repair_panel_preflight/summary.json`
- parent design: `docs/m1720-paper-route-controller-family-off-track-repair-panel-design.md`

## Summary

M1721 materialized the no-rollout off-track repair panel metadata.

This milestone did not execute rollout, train, replay, run PPO, promote, use
private holdout, change actor inputs, tune profiles, rank controller families,
or claim paper-level evidence or level3 self-identification.

## Preflight Result

- selected base specs: `18`
- selected task family counts: `T4=12`, `T5=6`
- repair panel specs: `72`
- repair panel matrix cells: `864`
- profiles: `12`
- contract violation count: `0`
- missing config / checkpoint count: `0` / `0`
- guardrail violation count: `0`
- environment rollout started: `false`

Variant counts:

| variant | specs |
| --- | ---: |
| `original_axis_baseline` | `18` |
| `best_off_track_variant` | `18` |
| `collision_control_wide_relaxed` | `18` |
| `wide_relaxed_extended` | `18` |

Selected source coverage:

| metric | count |
| --- | ---: |
| source edges | `5` |
| executable source families | `5` |
| environment template families | `4` |
| window tags | `3` |

Selected source-edge counts:

| source edge | selected base specs |
| --- | ---: |
| `capability_step_down|t5_near_boundary_warmup` | `6` |
| `t4_staged_warmup_capability|capability_step_up` | `5` |
| `actuator_delay_step|capability_step_up` | `3` |
| `t4_capability_step_temporal|capability_step_down` | `3` |
| `t4_actuator_delay_response|actuator_delay_step` | `1` |

## Selection Interpretation

The selector used only M1718 non-profile target slices:

```text
variant_source_edge
source_task_family
```

Profile rows were not used for source ranking. The selected set is intentionally
repair-targeted rather than maximally source-diverse: it preserves a fixed
`T4=12/T5=6` split and favors high off-track, low-collision target slices while
keeping diversity as a tie-breaker before target-slice count.

## Artifacts

```text
runs/m1721_off_track_repair_panel_preflight/summary.json
runs/m1721_off_track_repair_panel_preflight/selected_base_specs.csv
runs/m1721_off_track_repair_panel_preflight/rejected_target_sources.csv
runs/m1721_off_track_repair_panel_preflight/repair_panel_specs.json
runs/m1721_off_track_repair_panel_preflight/repair_panel_specs.csv
runs/m1721_off_track_repair_panel_preflight/repair_panel_matrix.csv
runs/m1721_off_track_repair_panel_preflight/contract_violations.csv
```

## Verification

Commands run:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_off_track_repair_panel_preflight.py tests/test_controller_family_off_track_dominance_localization.py
PYTHONPATH=src python -m autodrift.controller_family_off_track_repair_panel_preflight
```

Focused test result:

```text
5 passed
```

## Supported Claims

- The M1720 repair panel can be materialized as clean no-rollout metadata.
- The missing composite `wide_relaxed_extended` variant is available for all
  selected base specs.
- The repair panel preserves all twelve controller-family controls.

## Unsupported Claims

- repair panel execution result
- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1721 passes as a no-rollout preflight. Route to M1722 result audit before any
execution design.
