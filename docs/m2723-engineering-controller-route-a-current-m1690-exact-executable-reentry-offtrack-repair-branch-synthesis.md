# M2723 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_current_m1690_exact_executable_reentry_offtrack_repair_design_preflight`
- manifest: `experiments/manifests/m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis.json`
- synthesis doc: `docs/m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis.md`
- parent audit: `docs/m2722-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-result-audit.md`
- parent target panel: `runs/m2721_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight.json`
- next: `m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight`

## Synthesis Questions

### Evidence Summary

M2719-M2722 converted the M2716 exact-executable diagnostic execution branch
into a bounded offtrack repair target surface without adding execution,
training, ranking, or actor-contract changes.

Accepted evidence:

```text
M2719 taxonomy:
  48 taxonomy rows
  36 exact execution rows
  31 off_track rows
  2 obstacle_collision rows
  3 diagnostic_success rows
  12 protected_excluded rows
  19 gate rows all pass

M2720 audit:
  accepts M2719 as complete and claim-safe
  routes to no-rollout offtrack repair target-panel materialization

M2721 target panel:
  31 offtrack target rows
  2 collision caution rows
  3 diagnostic success context rows
  12 protected exclusion rows
  5 aggregate rows
  8 actor joins
  20 claim rows
  16 gate rows all pass

M2722 audit:
  accepts M2721 as complete and claim-safe
  target rows are repair-planning input only
  no execution is scheduled
```

The branch is still diagnostic/process evidence. It has not produced repair
execution evidence, performance evidence, validation evidence, current-sim
verdict evidence, high-fidelity evidence, full-driver evidence, or self-ID
evidence.

### Supported Claims

Supported:

```text
M2721 target-panel artifacts are complete and claim-safe.
The branch has an offtrack-dominant repair-planning surface: 31 target rows.
Collision caution rows and diagnostic success rows remain separate context.
Protected exclusions remain not targets, not executed, and outside denominators.
Actor observation shape 72 and action shape 3 are preserved.
Target, profile, protected, route, success, and verdict labels remain actor-invisible.
The next step may be a bounded repair-design preflight if it stays design-only.
```

### Falsified Claims

Rejected or unsupported:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
profile winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
protected mitigation preservation result
full ideal driver completion
level3 self-identification
```

The M2722 validation correction also falsifies the shortcut "go directly to
repair design without cadence synthesis." M2723 closes that process gap before
any repair design is admitted.

### Failure Taxonomy Summary

- `contract_violation`: not observed. The 72/3 actor/action contract,
  actor-invisible labels, and no hidden/oracle actor input boundary are
  preserved.
- `lineage_invalid`: not observed. The branch traces through M2718 synthesis,
  M2719 taxonomy, M2720 audit, M2721 target panel, and M2722 audit.
- `metric_artifact`: controlled. The branch materializes row accounting and
  guardrails only; it does not compute ranking or performance metrics.
- `scenario_sampling_failure`: active. The concrete repair surface is
  offtrack-dominant: 31 offtrack target rows from the exact-executable branch.
- `behavior_regression`: active/incomplete. Collision caution rows and
  protected exclusions must remain guardrails before any execution route.
- `objective_overfit`: medium but controlled. Another static target/audit loop
  would be local search; a bounded design preflight can change admission if it
  defines concrete repair levers and guardrails.
- `proof_washout`: controlled. Claim-boundary rows and this synthesis reject
  verdict claims from target-panel artifacts.

### Public Gate Overfit Risk

Risk before this synthesis: medium. M2719-M2722 are useful, but another
taxonomy/target/audit loop would be process-heavy and could look like public
gate polishing rather than evidence expansion.

Risk after this synthesis: medium-low only if the branch moves to a bounded
design preflight that can change the next admission decision. M2724 must either
define concrete offtrack repair levers with collision/protected-row guardrails
or stop/pivot; it must not add another static current-sim artifact or claim a
driver verdict from the target panel.

### Next Branch Decision

Decision:

```text
continue_to_current_m1690_exact_executable_reentry_offtrack_repair_design_preflight
```

M2719-M2722 are complete enough to admit design, but not execution. The next
bounded Route A step should freeze a repair design over the 31 offtrack target
rows, while preserving collision caution rows, diagnostic success context rows,
protected exclusions, and the actor/action contract.

Next route:

```text
m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight
```

M2724 must remain design-only. It must define the repair levers or
execution-admission constraints implied by the target panel, specify collision
and protected-row guardrails, keep labels actor-invisible, preserve actor
observation shape 72/action shape 3, and select one bounded follow-up route or
stop.

## Claim Boundary

Allowed M2723 claim:

```text
M2719-M2722 form a complete claim-safe offtrack repair target branch that can
continue to bounded repair design before any execution or verdict claim.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
protected mitigation preservation result
full ideal driver completion
level3 self-identification
```
