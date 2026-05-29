# M1687 Paper-Route Controller-Family Measured Routing Smoke Result Audit

- status: completed
- decision: `routing_smoke_audit_pass_route_to_full_rollout_design`
- audited artifact: `runs/m1686_controller_family_measured_routing_smoke/summary.json`
- audited doc: `docs/m1686-paper-route-controller-family-measured-routing-smoke.md`

## Audit Result

M1686 is a clean routing-smoke pass.

- required summary exists: `true`
- required CSV artifacts exist: `true`
- episode rows: `48`
- profile aggregate rows: `12`
- spec aggregate rows: `4`
- selected specs: `4`
- episode count target met: `true`
- profile count target met: `true`
- spec count target met: `true`
- selected metrics finite: `true`
- all episodes completed: `true`
- forbidden guardrail violation count: `0`

## Guardrail Audit

The following remained false in M1686:

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

Environment rollout did start, but that was explicitly allowed by the M1686
manifest as a bounded public routing smoke.

## Selected-Spec Coverage

M1686 used 4 executable public specs:

- `t4_staged_warmup_capability`
- `t4_actuator_delay_response`
- `t5_near_boundary_warmup`
- `t5_boundary_axis_retarget`

This is sufficient as routing/plumbing evidence, because it includes both T4
and T5 and exercises finite-window and recurrent profile observation shapes.
It is not sufficient as controller-family ranking evidence.

## Supported Claims

- The measured-routing runner can execute the 12 M1674 controller-family profile
  checkpoints over a source-diverse executable public task subset.
- The runner preserves the no-training/no-replay/no-PPO/no-promotion guardrails.
- The artifact schema is sufficient to support a larger measured-rollout design.

## Unsupported Claims

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- full-distribution rollout task quality
- private-holdout evidence
- paper-level evidence
- level3 anticipatory self-identification

## Decision

M1687 passes. The next step should be a full measured rollout design, not direct
execution. That design should specify the exact 864-cell public workload, run
artifacts, time/CPU expectations, failure handling, and claim boundary before
any full rollout starts.
