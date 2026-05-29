# M1686 Paper-Route Controller-Family Measured Routing Smoke

- status: completed
- result class: `controller_family_measured_routing_smoke_pass`
- artifact: `runs/m1686_controller_family_measured_routing_smoke/summary.json`
- episode rows: `runs/m1686_controller_family_measured_routing_smoke/episode_rows.csv`
- profile aggregate: `runs/m1686_controller_family_measured_routing_smoke/profile_aggregate.csv`
- spec aggregate: `runs/m1686_controller_family_measured_routing_smoke/spec_aggregate.csv`
- selected specs: `runs/m1686_controller_family_measured_routing_smoke/selected_specs.csv`

## Scope

M1686 executes the small public routing smoke admitted by M1685. It runs the 12
M1674 controller-family profile checkpoints over 4 source-diverse executable
public specs for a total of 48 environment episodes.

This milestone is infrastructure evidence only. It does not rank controller
families and does not support paper-level, private-holdout, promotion, or
level3 self-identification claims.

## Selected Public Specs

The routing smoke used 2 T4 and 2 T5 executable specs:

- `t4_staged_warmup_capability`
- `t4_actuator_delay_response`
- `t5_near_boundary_warmup`
- `t5_boundary_axis_retarget`

Each spec preserves the strict human-view/no-wheel/no-oracle contract. Profile
history length is preserved so L2 finite-window checkpoints receive their
expected observation shape, while hidden/oracle inputs, wheel/slip observations,
and nonzero obstacle relative velocity remain blocked.

## Result

- episode count: `48`
- expected episode count: `48`
- profile count: `12`
- spec count: `4`
- profile aggregate rows: `12`
- spec aggregate rows: `4`
- all selected metrics finite: `true`
- all episodes completed: `true`
- guardrail violation count: `0`
- passes public smoke gates: `true`

Forbidden guardrails remained false:

- training
- replay
- PPO
- promotion
- private holdout
- actor-input contract change
- profile-specific tuning
- paper-level claim
- controller-family ranking claim
- level3 self-identification claim

## Interpretation

Supported:

- The M1674 profile checkpoints/configs can be routed through a small
  source-diverse public executable task subset.
- The runner produces complete episode, profile, and spec aggregates with
  finite selected metrics.
- The two-stage measured-execution route can proceed to an audit before any
  full 864-cell rollout.

Unsupported:

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- rollout task quality at full scale
- private-holdout evidence
- paper-level evidence
- level3 anticipatory self-identification

## Next Step

M1687 should audit this smoke before any full rollout expansion. The audit
should check artifact completeness, guardrail cleanliness, selected-spec
coverage, and whether the runner design is sufficient for the larger measured
execution route.
