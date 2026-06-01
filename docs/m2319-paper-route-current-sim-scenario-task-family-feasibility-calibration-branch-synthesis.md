# M2319 Paper-Route Current-Sim Scenario Task-Family Feasibility Calibration Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_residual_support_structure_audit_design`
- manifest: `experiments/manifests/m2319-paper-route-current-sim-scenario-task-family-feasibility-calibration-branch-synthesis.json`
- synthesis artifact: `docs/m2319-paper-route-current-sim-scenario-task-family-feasibility-calibration-branch-synthesis.md`
- synthesis window: `M2312-M2318`
- reset/rollout/policy action in M2319: `false`
- training/replay/PPO in M2319: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2312 designed a diagnostic support-policy panel over the reset-valid 72-spec
current-sim role-family pack:

```text
scenario specs: 72
support policies: AEB / AES / envelope-AES
seed repeats: 5
episode count: 1080
support-policy purpose: diagnostic support bounds, not deployable candidates
```

M2313 executed that panel cleanly:

```text
episode_count: 1080
failure_count: 0
guardrail_violation_count: 0
support labels: support_clear 12, support_mixed 26, support_blocked 21, metric_conflict 13
R0: metric_conflict 12 / 12
R1: support_clear 12 / 12
```

M2314-M2316 diagnosed R0 as a metric semantics conflict rather than
support-blocked infeasibility. AEB support rows safely stopped before the
obstacle:

```text
R0 AEB safe-stop rows: 60
collision: 0
offtrack: 0
min/mean/max clearance: 10.96082732487428 / 25.993928793681416 / 43.58735902844862
```

M2317 designed a bounded role-success semantics repair:

```text
R0 safe-stop success iff:
  role_family == R0_stable_avoidable
  termination_reason == speed_too_low
  min_clearance_margin > 0
  no collision
  no offtrack
```

M2318 implemented the repair and rescored the existing M2313 artifacts without
rerun:

```text
result_class: current_sim_scenario_task_family_role_success_semantics_repair_pass
input/rescored episodes: 1080 / 1080
guardrail_violation_count: 0
baseline labels: support_clear 12, support_mixed 26, support_blocked 21, metric_conflict 13
repaired labels: support_clear 24, support_mixed 26, support_blocked 21, metric_conflict 1
support_clear_delta: 12
metric_conflict_delta: -12
R0 support_clear / metric_conflict: 12 / 0
non_r0_safe_stop_success_count: 0
```

## Supported Claims

M2319 supports these bounded claims:

- The M2313 support-policy panel is complete and useful as diagnostic evidence.
- R0 was blocked by a success-semantics artifact, not by task infeasibility.
- The bounded R0 safe-stop repair is accepted: R0 becomes `support_clear 12/12`
  without globalizing safe-stop success to other roles.
- R1 remains `support_clear 12/12` after the repair.
- R2-R5 still contain structured residual support issues:

```text
R2: support_mixed 7 / 12, support_blocked 5 / 12
R3: support_mixed 8 / 12, support_blocked 3 / 12, metric_conflict 1 / 12
R4: support_mixed 3 / 12, support_blocked 9 / 12
R5: support_mixed 8 / 12, support_blocked 4 / 12
```

## Falsified Claims

M2319 falsifies or blocks these claims:

- R0 should be treated as support-blocked.
- Obstacle-pass-only success is a valid universal success semantics for the
  current-sim role-family pack.
- The current 72-spec pack is ready for controller-family ranking or paper-level
  current-sim comparison.
- R2-R5 residual rows are solved by the R0 safe-stop rule.
- Residual support-blocked rows are driver failures. At this stage they are
  scenario/support-calibration evidence.
- This branch provides finite-window vs GRU, paper-level, or level3
  self-identification evidence.

## Failure Taxonomy Summary

Primary failure types:

```text
metric_artifact:
  R0 was misclassified by obstacle-pass-only success semantics. M2318 repairs
  this artifact with a bounded R0 safe-stop rule.

scenario_sampling_failure:
  R2-R5 retain support_blocked and support_mixed rows after R0 repair. These may
  indicate over-hard geometry, weak support policies, or missing role semantics.

objective_overfit:
  Prior guarded-repair training failed on this pack before support calibration.
  The current synthesis confirms training should not resume until residual
  support structure is audited.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate and rising.

The branch has now used the same 72-spec pack for support-policy calibration,
metric diagnosis, role-success repair, and artifact-only rescore. M2318 was a
legitimate semantics fix, but continuing to tweak labels or support policies
without a structured residual-support audit would turn the workflow back into a
local gate-passing loop.

The next branch must change the question from:

```text
Can we repair this one metric artifact?
```

to:

```text
Which remaining role/timing/hidden-dynamics slices are unsupported, mixed, or
metric-conflicted, and do they require scenario redesign, support-policy
coverage, or role-specific success semantics before training?
```

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. M2319 runs no driver checkpoint evaluation.

mechanism evidence for history dependence:
  no new support. No wrong-history, reset-hidden, zero-history, finite-window,
  or GRU comparison is run.

scenario/task-quality evidence:
  positive for R0 semantics repair and R1 support clarity; unresolved for R2-R5
  residual support.

high-fidelity validation readiness:
  not ready. Current-sim scenario/support verdict is not frozen.

workflow or complexity reduction:
  positive. The branch synthesis prevents another semantics micro-audit and
  routes to a new residual-support evidence axis.
```

## Next Branch Decision

Decision:

```text
continue
```

New branch:

```text
paper_route_current_sim_scenario_task_family_residual_support_audit
```

Next milestone:

```text
m2320-paper-route-current-sim-scenario-task-family-residual-support-audit-design
```

M2320 should design an artifact-only residual-support audit over M2318 rescored
artifacts. It should quantify, without rerun:

```text
support_blocked / support_mixed / metric_conflict rows by role;
hidden_dynamics_bucket;
obstacle_longitudinal_timing_bucket;
obstacle_lateral_offset_bucket;
support policy;
dominant failure mode;
safe-stop evidence that is not admitted outside R0;
whether each residual group suggests scenario redesign, support-policy coverage,
or role-specific success semantics work.
```

M2320 must not train, rerun the panel, rank support policies, select a winner,
claim paper-level evidence, compare finite-window vs GRU, or claim level3
self-identification.

## Blocked Routes

Blocked:

```text
direct PPO or guarded repair from M2318 labels;
controller-family ranking from support policies;
paper-level current-sim comparison;
claiming R2-R5 residual support solved;
continuing metric micro-audits without residual-support synthesis;
finite-window vs GRU conclusion;
level3 self-identification claim.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2320-paper-route-current-sim-scenario-task-family-residual-support-audit-design.json
```
