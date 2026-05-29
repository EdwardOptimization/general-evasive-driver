# M1432 Paper-Route Geometry-Aware Selector Implementation

## Summary

M1432 implements the M1431 geometry-aware preflight selector.

Decision:

```text
geometry_aware_selector_implemented_route_to_branch_synthesis
```

M1432 does not run bounded replay, train, run PPO, promote, use private holdout,
export a training corpus, or change actor inputs.

## Implementation

Updated:

```text
src/autodrift/bounded_relocation_replay_probe.py
tests/test_bounded_relocation_replay_probe.py
```

New selector functions:

```text
classify_relocation_geometry
geometry_preflight_frame
select_geometry_aware_replay_candidates
build_geometry_preflight_summary
geometry_preflight_from_trace_candidates
```

New CLI controls:

```text
--geometry-aware-selector
--min-source-body-x
--per-seed-cap
--per-reveal-bucket-cap
--per-variant-cap
```

The default replay path remains compatible. Geometry-aware preflight is only
enabled when `--geometry-aware-selector` is passed.

## Geometry Rules

The selector rejects rows when:

```text
source_body_x < 4.0
relocated_body_x <= min_body_x + 1e-6
relocation_body_x_clipped == true
source_half_width < min_half_width
relocated_half_width <= min_half_width + 1e-6
geometry is non-finite
```

Selected rows are capped by:

```text
per seed
per capability pair
per reveal bucket
per history variant
```

This directly addresses the M1429 failure where one seed and one variant
dominated and most selected rows were clipped from behind-vehicle obstacle
sources.

## Outputs

When geometry-aware selection is enabled, the run path now writes:

```text
geometry_preflight_rows.csv
geometry_rejected_rows.csv
geometry_summary.json
```

The main summary also includes:

```text
geometry_aware_selector
geometry_preflight
geometry_preflight_rows_csv
geometry_rejected_rows_csv
geometry_summary_json
```

Preflight rows still do not count as replay evidence. A future milestone must
run the selector before any new bounded replay result can be interpreted.

## Tests

Focused tests cover:

```text
source_body_x rejection
relocation clipping rejection
forward unclipped pass case
history/control filtering
per-seed and per-variant caps
geometry preflight summary fields
contract guardrail flags
```

Focused result:

```text
tests/test_bounded_relocation_replay_probe.py: 8 passed
```

## Guardrails

M1432 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

The action-divergent geometry branch has reached the synthesis cadence. Do not
run the geometry-aware selector smoke directly as M1433.

Admit:

```text
m1433-paper-route-action-divergent-geometry-branch-synthesis
```

M1433 should synthesize M1423-M1432 and decide whether the implemented selector
justifies a public geometry-aware preflight/source smoke, whether the branch
should pivot back to source mining, or whether it should stop.
