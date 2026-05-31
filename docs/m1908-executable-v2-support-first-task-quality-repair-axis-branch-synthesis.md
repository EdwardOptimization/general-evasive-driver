# M1908 Executable V2 Support-First Task-Quality Repair-Axis Branch Synthesis

- status: completed
- decision: `promote_to_next_branch`
- branch synthesized: `paper_route_clearance_containment_task_quality_repair_axis`
- next branch: `paper_route_repair_axis_measured_wrapper`
- evidence window: `M1901-M1907`
- reset/rollout in M1908: false
- measured execution in M1908: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Evidence Summary

M1901-M1907 moved the branch from a localized task-quality conflict to a
count-complete execution-preflightable repair-axis panel.

Evidence produced:

```text
M1901:
  designed eight baseline-preserving task-quality repair-axis variants.

M1902:
  materialized the no-rollout matrix:
  - matrix rows: 1536
  - source specs: 16
  - controller profiles: 12
  - role surfaces: 8
  - repair-axis variants: 8
  - original_retained rows: 192
  - duplicate axis keys: 0
  - guardrail violations: 0

M1903:
  audited the M1902 materialization as count-complete.

M1904:
  designed the wrapper protocol:
  - rollout_geometry_variant rows: 960
  - import/postprocess rows: 576
  - combined panel rows: 1536

M1905:
  implemented dry-run wrapper infrastructure and focused tests.
  - focused tests: 3 passed

M1906:
  ran real-matrix no-rollout wrapper preflight:
  - planned rollout rows: 960
  - import/postprocess rows: 576
  - combined rows: 1536
  - failure count: 0

M1907:
  audited M1906 as clean split/join/count evidence but blocked direct command
  design because measured rollout extension points are still missing.
```

This changes the project capability at the scenario/task-quality layer:

```text
before:
  M1895/M1899 showed zero joint clearance/containment and a split failure
  surface, but no fair next diagnostic execution panel.

after:
  the project has an axis-separated, baseline-preserving 1536-row repair-axis
  panel and a validated no-rollout wrapper preflight for it.
```

It does not change driver capability. It does not support a controller-family
ranking or paper-level result.

## Supported Claims

Supported:

- the clearance/containment conflict is localized enough for axis-specific
  task-quality repair;
- the repair-axis matrix preserves the original baseline, all 12 controller
  profiles, all 8 role surfaces, and support-first metadata;
- the wrapper can split, join, and preflight the real matrix without rollout;
- moving to a measured-wrapper implementation branch is justified.

Supported paper-route category:

```text
scenario/task-quality evidence: improved
workflow or complexity reduction: improved by forcing synthesis before more
  implementation
engineering driver performance: unchanged
mechanism evidence for history dependence: unchanged
high-fidelity validation readiness: unchanged
```

## Falsified Claims

Falsified or still blocked:

- M1895/M1902 can be used for controller-family ranking: false.
- Current repair axes prove task-quality repair success: false.
- Current artifacts prove policy improvement: false.
- Current artifacts prove level3 self-identification: false.
- Direct measured execution command design is ready from the dry-run wrapper:
  false, because measured rollout extension points are not implemented yet.

The branch also falsifies a workflow assumption:

```text
It is not acceptable to keep adding implementation/design milestones after
M1907 without synthesis. The local-search guard correctly stopped that path.
```

## Failure Taxonomy Summary

No new experiment failure occurred in M1901-M1907. The active taxonomy is:

```text
none:
  M1901-M1907 artifacts passed their pre-registered process/infrastructure
  gates.

metric_artifact / scenario_sampling_failure:
  inherited historical concern from M1880-M1899, where raw success was
  uninterpretable due to task-quality geometry and role semantics.
```

The branch is best classified as a task-quality repair route, not a driver
performance route.

## Public Gate Overfit Risk

Risk: medium.

Why:

- the branch uses a public bounded-smoke panel derived from M1895/M1899;
- the repair axes are designed from known conflict classes;
- no private holdout or fresh measured distribution has been used;
- no controller-family ranking is allowed yet.

Why risk is acceptable for the next step:

- M1902 preserved the original baseline instead of deleting hard rows;
- M1902 emitted both targeted and diagnostic-control axis rows;
- M1906 was a no-rollout split/join preflight, not a tuned controller result;
- the next branch is still infrastructure, with real interpretation deferred.

Required guard in the next branch:

```text
measured-wrapper implementation must not change actor inputs, tune profiles,
or claim performance. It may only make the already preflighted matrix executable.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_repair_axis_measured_wrapper
```

Next milestone:

```text
m1909-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-implementation
```

M1909 should extend the validated dry-run wrapper with measured rollout
extension points and mocked tests. It must still not run the real M1902
workload. The real measured execution command design should only come after
M1909 passes.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured execution started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted checkpoint: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Claim Boundary

This synthesis supports a next-branch engineering decision. It does not support
any driver-performance, controller-ranking, paper-result, or self-ID mechanism
claim.
