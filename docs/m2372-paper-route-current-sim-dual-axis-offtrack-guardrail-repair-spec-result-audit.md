# M2372 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Spec Result Audit

- status: completed
- decision: `repair_spec_result_accepted_route_to_offtrack_guardrail_repair_implementation_design`
- manifest: `experiments/manifests/m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit.json`
- parent doc: `docs/m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization.md`
- audited summary: `runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json`
- reset/rollout/measured execution in M2372: `false`
- policy action executed in M2372: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair claims: `false`

## Audit Result

M2371 is accepted as a complete artifact-only repair-spec materialization pass:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_pass
repair_spec_row_count: 320
ordinary_offtrack_repair_spec_count: 36
mixed_guarded_repair_spec_count: 18
collision_guardrail_spec_count: 28
r4_guardrail_spec_count: 48
diagnostic_guardrail_spec_count: 190
profile_or_pack_repair_spec_count: 0
r4_ordinary_repair_spec_count: 0
collision_blind_mixed_repair_spec_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Repair family counts:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
```

Priority tier counts:

```text
P0: 26
P1: 28
G0: 28
R4: 48
D0: 190
```

## Interpretation

The M2371 spec layer is internally clean enough to admit a bounded repair
implementation design:

```text
ordinary offtrack specs exist;
mixed guarded offtrack specs retain collision guardrail requirements;
collision-only rows remain guardrail constraints;
R4 mitigation semantics rows remain guardrails, not ordinary repair specs;
diagnostic rows remain no-ranking guardrails;
forbidden execution, ranking, and paper/self-ID claim flags are false.
```

This does not show that any repair lever works. M2372 is a result audit only.
It does not execute repair, rerun scenarios, train a policy, replay a gate, use
PPO, select a winner, or support a paper-level conclusion.

## Repair Spec Surfaces

Ordinary offtrack repair specs:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
```

These are the only rows eligible for ordinary offtrack containment repair
design.

Mixed offtrack/collision specs:

```text
guarded_offtrack_containment_repair: 18
collision_guardrail_required: true
guardrail_metric: collision_rate_not_worse
```

These rows can be used by a repair design only if collision guardrails remain
first-class constraints.

Guardrail-only specs:

```text
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
```

These are not ordinary offtrack repair targets. They constrain later repair
design, evaluation, and claim boundaries.

## Decision

M2372 routes to:

```text
m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design
```

M2373 should design the bounded implementation route for the repair levers
named by M2371. It should not execute the repair. The design must preserve:

```text
1. ordinary offtrack containment as the only direct repair target;
2. mixed-row collision guardrails as constraints, not optional metrics;
3. R4 mitigation semantics as a separate guardrail route;
4. diagnostic/profile/pack/global rows as no-ranking guardrails;
5. actor input and human-view contract unchanged;
6. no hidden/oracle feature injection;
7. no profile-specific tuning, ranking, or winner selection;
8. no scenario-redesign-executed or training-repair-success claim.
```

Because the current outcome-localization branch is near its synthesis cadence,
M2373 should also decide whether the next step after implementation design must
be branch synthesis before any new narrow implementation milestone.

## Claim Boundary

M2372 may claim only:

```text
M2371 repair-spec artifacts are complete and clean enough to admit a bounded
offtrack guardrail repair implementation design.
```

Still blocked:

```text
repair execution
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-registered follow-up:

```text
m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design
```
