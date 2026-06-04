# M2690 Engineering Controller Route A Package With Limitations Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_source_diverse_offtrack_protected_target_panel_materialization`
- manifest: `experiments/manifests/m2690-engineering-controller-route-a-package-with-limitations-branch-synthesis.json`
- synthesis artifact: `docs/m2690-engineering-controller-route-a-package-with-limitations-branch-synthesis.md`
- parent audit: `docs/m2689-engineering-controller-route-a-package-with-limitations-protocol-materialization-result-audit.md`
- package summary: `runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2691-engineering-controller-source-diverse-offtrack-protected-target-panel-materialization-preflight.json`
- next: `m2691-engineering-controller-source-diverse-offtrack-protected-target-panel-materialization-preflight`

## Evidence Summary

M2686-M2689 closed the package-with-limitations branch without changing driver
capability evidence. The branch preserved the Route A engineering artifacts,
made their claim boundary auditable, and kept known blockers visible.

Accepted package branch evidence:

```text
M2686:
  closes Route B task-quality role-semantics bounded subset branch
  records off-track dominance: 202/216 outcomes and 203/216 terminations
  rejects paper, current-sim, driver-performance, and self-ID interpretation
  pivots to Route A package-with-limitations protocol design

M2687:
  designs package manifest schema, artifact inventory, provenance,
  known blocker disclosure, actor/action contract, claim-boundary rows, and gates
  admits materialization only, not publication or validation

M2688:
  status_pass: true
  required Route A artifacts covered: 6/6
  package manifest schema rows: 17
  artifact inventory rows: 10
  provenance rows: 10
  blocker disclosure rows: 4
  actor/action contract rows: 9
  claim-boundary rows: 25
  package protocol gates: 20/20 pass
  package_published: false

M2689:
  accepts M2688 as complete and claim-safe
  preserves protected mitigation, current-sim off-track, HF3 dependency,
  and paper/self-ID blockers
  routes to branch synthesis before any further package process
```

The package protocol is useful public/engineering hygiene. It does not execute
reset, step, rollout, replay, validation, training, PPO, source build, adapter
probe, external simulation, ranking, winner selection, checkpoint promotion, or
success-rate verdict computation.

The governing post-M2470 route plan remains active: current-sim should stay a
fast diagnostic layer, Route A engineering work should not be blocked by
current-sim perfection, and high-fidelity validation preparation should not
continue into selected-platform execution while the required source dependency
is unavailable.

## Supported Claims

Supported:

- Route A has an auditable package-with-limitations protocol covering the six
  required post-M2470 artifacts: baseline checkpoint list, actor input/output
  contract, public benchmark pack, runtime/inference-cost report,
  scenario-role metric report, and known failure taxonomy.
- The package protocol records the protected mitigation blocker, current-sim
  off-track blocker, HF3 source dependency blocker, and paper/self-ID blocker
  as visible limitations.
- Actor contract remains deployable: P0 observation shape `72`, action shape
  `3`, action mapping `[steer, throttle, brake]`, no hidden/oracle actor input,
  and no actor-visible taxonomy, route, package, blocker, verdict, or paper
  labels.
- M2688/M2689 are complete enough to preserve as process artifacts and do not
  need another package repair before synthesis.
- The package branch should stop as the active branch unless publication is
  later requested explicitly as a non-performance release operation.

## Falsified Or Rejected Claims

Rejected:

- The package was published.
- The Route A baseline is deployment-ready.
- M2688/M2689 prove driver performance, repair success, validation readiness,
  validation result, current-sim verdict, high-fidelity validation readiness or
  result, paper evidence, finite-window-vs-GRU result, current-response
  sufficiency, full ideal driver completion, or level3 self-identification.
- M2684/M2685/M2686 profile rows rank controller families or select a winner.
- Another package manifest/publication-design/audit milestone is the right
  immediate research action.
- HF3 selected-platform build/probe execution is admitted without a supplied
  local source root, approved package route, or explicit dependency-acquisition
  manifest.

## Failure Taxonomy Summary

- `contract_violation`: not observed. The actor boundary is preserved at P0
  observation shape 72 and action shape 3 with no hidden/oracle inputs and no
  actor-visible package/blocker/verdict labels.
- `lineage_invalid`: not observed. M2688/M2689 trace package artifacts to the
  accepted Route A readiness, runtime, scenario-role, known-failure, Route B
  off-track blocker, HF3 blocker, and post-M2470 route-plan sources.
- `metric_artifact`: controlled for package completeness. Package rows do not
  compute or interpret performance metrics.
- `scenario_sampling_failure`: active. Current-sim off-track dominance remains
  unresolved and blocks current-sim, paper, ranking, performance, and self-ID
  interpretation.
- `behavior_regression`: active. Protected mitigation remains a broad blocker
  with 25 protected blocking rows and 79 regressed row count.
- `objective_overfit`: high if the project continues package process or repeats
  public off-track/protected repair loops. Lower if the next branch creates a
  source-diverse target panel that can admit fresh measured evidence later.
- `proof_washout`: controlled by M2688/M2689 claim boundaries, but would become
  active if package completeness were rebranded as driver capability or paper
  evidence.

## Public-Gate Overfit Risk

The package branch overfit risk is now medium to high. M2687, M2688, and M2689
were all process milestones. They improved package hygiene and claim safety,
but they did not create new closed-loop data, new source diversity, new
generalization evidence, protected mitigation recovery, current-sim
interpretability, high-fidelity validation, or self-ID evidence.

Continuing into package publication design as the immediate next milestone
would mostly optimize public presentation. It would not address the two active
driver-evidence blockers:

```text
protected mitigation blocker:
  25 protected blocking rows
  79 regressed row count

current-sim off-track blocker:
  202/216 off-track outcomes
  203/216 off-track terminations
```

Continuing Route B by another same public T4/T5 off-track repair loop is also
risky. M2680-M2686 already synthesized that branch and found the subset
diagnostic but not interpretable.

The next lower-overfit move is a source-diverse target-panel materialization
that combines the off-track and protected blockers into one admission surface
for a later measured execution. That next milestone must be panel
materialization only: no reset, rollout, validation, training, ranking,
promotion, success-rate verdict, driver-performance claim, paper claim,
current-sim verdict, high-fidelity result, or self-ID claim.

## Next Branch Decision

Decision:

```text
pivot_to_source_diverse_offtrack_protected_target_panel_materialization
```

Rationale:

- The Route A package-with-limitations protocol is complete enough to preserve.
- Another package-process milestone would not change the driver evidence axis.
- HF3 selected-platform execution is paused by M2638 because the configured
  source root `/home/quyaonan/workspace/chrono` is unavailable.
- Route B fair-comparison rows remain off-track dominated and cannot support
  paper or self-ID interpretation.
- The long-term driver objective needs new evidence about failure surfaces that
  actually block closed-loop competence: off-track dominance and protected
  mitigation regression.

Next route:

```text
m2691-engineering-controller-source-diverse-offtrack-protected-target-panel-materialization-preflight
```

M2691 should materialize a source-diverse target panel from existing M2684
off-track evidence, M2664/M2667 protected mitigation evidence, M2688 package
blocker disclosures, and the post-M2470 route plan. It should prepare a
bounded future measured-execution admission surface that can test whether the
driver can improve off-track containment and protected mitigation without
changing actor inputs.

M2691 must not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
checkpoint promotion, package publication, success-rate verdict computation, or
driver-performance interpretation. It must not claim current-sim, paper,
finite-window-vs-GRU, current-response, high-fidelity, full ideal driver, or
self-ID evidence.

## Claim Boundary

Allowed M2690 claim:

```text
The Route A package-with-limitations branch is synthesized, the package
protocol should be preserved as process evidence, and the active route should
pivot to a source-diverse off-track/protected target-panel materialization
before any further package process.
```

Rejected claims:

```text
published package
deployment readiness
validation readiness or result
driver performance
repair success
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
