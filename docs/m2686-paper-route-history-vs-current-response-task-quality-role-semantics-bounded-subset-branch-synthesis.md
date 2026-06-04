# M2686 Paper Route History Vs Current Response Task Quality Role Semantics Bounded Subset Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_package_with_limitations_protocol_design`
- manifest: `experiments/manifests/m2686-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-branch-synthesis.json`
- parent audit: `docs/m2685-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-result-audit.md`
- parent execution summary: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/summary.json`
- governing route plan: `docs/post-m2470-route-plan.md`
- Route B governing plans: `docs/self-id-go-no-go-paper-route-plan.md` and `docs/paper-route-finite-window-vs-gru-plan.md`
- Route A readiness reference: `docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md`
- HF3 blocker reference: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- follow-up manifest: `experiments/manifests/m2687-engineering-controller-route-a-package-with-limitations-protocol-design.json`
- next: `m2687-engineering-controller-route-a-package-with-limitations-protocol-design`

## Evidence Summary

M2680-M2685 advanced the Route B task-quality and role-semantics branch from
static calibration into one bounded measured execution. The branch produced
useful diagnostic evidence and a cleaner claim boundary, but it did not remove
the interpretation blocker that motivated the branch.

The accepted M2684/M2685 execution state is:

```text
status_pass: true
result_class: paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_pass
episode rows: 216/216
accounted cells: 216/216
failure rows: 0
profiles covered: 12/12
subset specs covered: 18/18
candidate aggregates: 9
source-edge aggregates: 9
role-semantics aggregate groups: 2
runtime joins: 12/12 pass
claim-boundary rows: 37
gate rows: 30/30 pass
subset expanded to full public matrix: false
actor observation shape: 72
action shape: 3
hidden/oracle actor input detected: false
role semantics actor visible: false
training/PPO/replay/private holdout/profile-specific tuning: false
```

The same execution also preserved the main blocker:

```text
outcomes:
  off_track_noncollision_noncompletion: 202/216
  success_obstacle_pass: 11/216
  collision_failure: 3/216

terminations:
  off_track: 203/216
  none/success: 11/216
  obstacle_collision: 2/216
```

The profile aggregates remain diagnostic only. The L3 reset/truncated-control
row had 7/18 successes, L0 current-response had 2/18, L1 one-step had 1/18,
L3 online GRU had 1/18, and all L2 finite-window/current-tiled rows had 0/18
successes on the bounded subset. These numbers are not rankings or paper
results because the subset is bounded, current-sim, public, off-track
dominated, and selected from a task-quality repair admission panel.

This branch therefore improves scenario/task-quality evidence and workflow
discipline. It does not improve the paper verdict, current-sim verdict,
driver-performance claim, high-fidelity validation claim, or level3 self-ID
claim.

## Supported Claims

Supported:

- M2684 produced a complete, guardrail-clean, bounded 216-row closed-loop
  diagnostic dataset.
- M2685 correctly accepted M2684 artifact completeness while blocking direct
  interpretation.
- Runtime enforcement still covers the Route B L0/L1/L2/L3 comparison profiles,
  including L2 current-tiled controls and L3 reset/truncated-control.
- Actor contract remains P0 observation shape `72`, action shape `3`, with no
  hidden/oracle actor input and no actor-visible role semantics, route labels,
  controller-family labels, or verdict labels.
- The task-quality and role-semantics branch has evidence value as a current-sim
  diagnostic and scenario-quality audit.
- The governing post-M2470 route plan is still active: current-sim should remain
  a fast diagnostic layer, while engineering Route A and high-fidelity
  validation preparation should not wait for current-sim perfection.
- Route A already has a packageable-with-limitations readiness index from
  M2667/M2668/M2669 covering the six post-M2470 near-term artifacts:
  baseline checkpoint list, actor input/output contract, public benchmark pack,
  known failure taxonomy, runtime/inference-cost report, and scenario-role
  metric report.

## Falsified Or Rejected Claims

M2686 rejects these interpretations:

- M2684 ranked controller families.
- M2684 selected a winner.
- M2684 proved finite-window-vs-GRU, current-response sufficiency, or level3
  self-identification.
- M2684 produced paper-level evidence.
- M2684 produced a current-sim verdict.
- M2684 produced driver-performance evidence.
- M2684 produced high-fidelity validation readiness or validation results.
- M2684 completed the full ideal driver objective.
- The L3 reset/truncated-control diagnostic row can be treated as an L3
  self-ID proof.
- Another narrow public task-quality/role-semantics subset repair is the right
  immediate next step.

The branch also does not justify resuming HF3 selected-platform source-build or
adapter-probe execution. M2638 already paused that route until a valid local
source root, approved package route, or explicitly admitted dependency
acquisition operation is supplied.

## Failure Taxonomy Summary

- `contract_violation`: not observed. The actor/action boundary, no-hidden
  actor input rule, no private holdout rule, and actor-invisible role semantics
  boundary remain intact.
- `lineage_invalid`: not observed. M2684 consumes the pre-registered M2682
  subset, M2673 runtime-enforcement rows, M1690 workload artifacts, and M1674
  checkpoint lineage.
- `metric_artifact`: controlled for artifact completeness. Metrics are finite,
  but aggregate success and profile rows are diagnostic only.
- `scenario_sampling_failure`: active for interpretation. Off-track remains the
  dominant outcome and termination mode.
- `behavior_regression`: not decided. No ranking, promotion, repair success, or
  performance verdict is admitted.
- `objective_overfit`: high if the next action is another public current-sim
  task-quality subset repair. Lower if the project pivots to a different
  evidence axis or packages Route A limitations honestly.
- `proof_washout`: controlled in M2684/M2685 by explicit claim-boundary rows,
  but would become active if diagnostic subset success rows were rebranded as
  paper or self-ID evidence.

## Public-Gate Overfit Risk

Risk is high for continuing the current Route B task-quality/role-semantics
sub-branch. M2680, M2681, M2682, M2683, M2684, and M2685 all addressed the same
off-track interpretation blocker. M2684 was an evidence-expanding execution,
but the central blocker survived:

```text
off-track outcomes: 202/216
off-track terminations: 203/216
paper verdict delta: no verdict
driver-performance delta: no claim
self-ID delta: no claim
```

Continuing with another narrow subset repair would optimize the visible
current-sim public surface rather than changing the scientific or engineering
evidence axis.

Risk is lower for a Route A package-with-limitations design because it does not
claim new driver capability. It converts already accepted readiness evidence
into a bounded public/engineering package protocol while keeping known blockers
visible. That route must still forbid validation-readiness, driver-performance,
paper, current-sim, high-fidelity, and self-ID claims.

## Next Branch Decision

Decision:

```text
pivot_to_route_a_package_with_limitations_protocol_design
```

Rationale:

- `docs/post-m2470-route-plan.md` says current-sim should remain diagnostic and
  should not block engineering and high-fidelity preparation.
- M2638 paused HF3 selected-platform execution until source dependency evidence
  is supplied, so HF3 build/probe execution is not the next non-overfit action.
- M2667/M2668/M2669 already established that Route A has a current integrated
  artifact set that is packageable with limitations.
- M2669 deferred packaging because Route B offered a new history-dependence
  evidence axis. M2670-M2685 exercised that axis, but direct interpretation is
  still blocked by off-track dominance.
- Returning to Route A packaging now reduces workflow drift without converting
  diagnostic current-sim rows into paper or self-ID claims.

Next route:

```text
m2687-engineering-controller-route-a-package-with-limitations-protocol-design
```

M2687 must design, not materialize, the package-with-limitations protocol. It
should specify:

- package manifest schema and artifact inventory
- baseline checkpoint list inclusion rules
- actor input/output contract inclusion rules
- public benchmark pack inclusion rules
- runtime/inference-cost report inclusion rules
- scenario-role metric report inclusion rules
- known failure taxonomy and protected mitigation blocker disclosure rules
- current-sim diagnostic limitation disclosure rules, including the M2684/M2685
  off-track dominance blocker
- HF3 source dependency blocker disclosure rules from M2638
- claim-boundary rows that forbid validation readiness, driver performance,
  paper, finite-window-vs-GRU, current-response, current-sim, high-fidelity,
  full ideal driver, and self-ID claims
- a bounded M2688 materialization preflight handoff if the design is accepted

M2687 must not install dependencies, fetch source, import high-fidelity
packages, execute source builds, run adapter probes, start a backend, reset,
step, roll out, replay, validate, train, run PPO, rank controllers, select a
winner, promote checkpoints, compute success-rate verdicts, or claim driver
performance.

## Claim Boundary

Allowed M2686 claim:

```text
M2680-M2685 produced complete and claim-safe task-quality/role-semantics
diagnostic evidence, but the bounded subset remains off-track dominated, so the
Route B task-quality sub-branch should pivot to a Route A
package-with-limitations protocol design rather than another narrow current-sim
repair loop.
```

Rejected claims remain rejected:

```text
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
comparison-delta verdict
repair success
driver performance
validation readiness
validation result
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
