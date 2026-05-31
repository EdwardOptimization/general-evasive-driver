# M1892 Executable V2 Support-First Measured Execution Branch Synthesis

- status: completed
- synthesis decision: `continue`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- evidence window: `M1882-M1891`
- reset run: `false`
- rollout/training/replay/PPO: `false`

## Evidence Summary

M1882-M1891 advanced the support-first measured-execution branch from a
zero-success public diagnostic result to a repaired bounded-smoke execution
protocol.

Branch evidence:

- M1882 localized the M1880 outcome dominance from existing artifacts:
  `526` dominant slices across all roles, role surfaces, and controller
  profiles. The failure was diffuse task-quality/outcome dominance, not a
  controller-specific ranking signal.
- M1883 designed the no-training success-semantics and task-quality repair
  route: preserve the original baseline, add role-aware diagnostic semantics,
  and separate road-boundary geometry from obstacle/finish semantics.
- M1884 materialized the repair matrix without rollout: `2160` base workload
  rows, `5` repair variants, and `10800` repair rows, with all controller
  profiles preserved and guardrail `0`.
- M1885 audited that materialization as complete, but blocked direct execution
  until geometry deltas had an explicit runner/adapter protocol.
- M1886 chose a bounded repaired smoke before full-matrix execution:
  `576` new geometry rollout cells plus `384` imported original/semantics rows
  for a `960`-row smoke panel.
- M1887 implemented the no-rollout repaired adapter with config-delta
  validation and rollout/import row separation.
- M1888 registered the exact no-rollout preflight command and target counts.
- M1889 ran the real-artifact no-rollout preflight successfully:
  `16` selected sources, `48` patched executable specs, `576` rollout cells,
  `384` import rows, `960` total panel rows, no config failures, no missing
  imports, no duplicate specs/workloads, and guardrail `0`.
- M1890 audited M1889 as count-complete and guardrail-clean, but still blocked
  direct execution because the old runner cannot consume repaired specs plus
  import rows.
- M1891 designed the repaired bounded-smoke execution protocol: run only the
  geometry variants, import original/semantics-only rows from M1880 source
  episodes, preserve repair metadata, and defer interpretation to a
  post-execution audit.

## Supported Claims

Supported:

- the support-first outcome-dominance issue has been localized as diffuse
  task-quality/semantics pressure, not a controller-family ranking result;
- the repair matrix exists and preserves the original baseline plus four repair
  variants;
- a bounded smoke is the correct next execution scale before the full
  `10800`-row matrix;
- the bounded smoke inputs are count-complete and guardrail-clean;
- the repaired execution protocol is specified well enough to implement a
  wrapper;
- controller profile controls for later current-response, finite-window, and
  GRU comparison remain preserved.

Unsupported:

- repaired bounded-smoke rollout result;
- repaired task-quality success;
- controller-family ranking;
- paper-level benchmark evidence;
- current-response versus finite-window versus GRU verdict;
- level3 self-identification evidence.

## Falsified Claims

Falsified or rejected during this branch window:

- The M1880 zero-success result can be interpreted as controller-family
  performance.
- Direct full `10800`-row repair execution is the right next step before a
  bounded smoke.
- The existing support-first measured runner can directly consume repaired
  specs and import rows.
- Import rows and rollout rows can be collapsed without preserving provenance.

## Failure Taxonomy Summary

Observed blockers:

- `metric_artifact`: M1880's raw binary success was not sufficient for role-wise
  active-safety interpretation.
- `task_quality_dominance`: off-track/collision outcomes dominated across
  roles and profiles, blocking ranking.
- `schema_mismatch`: repaired specs, geometry workload rows, and import rows
  required a wrapper instead of the old runner.

No actor-input contract violation occurred. No controller profile was tuned. No
private holdout, training, replay, PPO, promotion, ranking, paper-level claim,
or level3 self-ID claim was made.

## Public Gate Overfit Risk

Public-gate overfit risk is still present but bounded by the branch scope. This
branch is about task-quality and measurement plumbing, not training a policy or
selecting a winner. The main risk is artifact overconfidence: a clean
preflight and a good execution protocol do not prove that repaired task quality
will be interpretable after rollout.

Therefore the next implementation must keep execution and interpretation
separate. The wrapper can create the measured artifacts, but controller ranking
must remain blocked until a post-execution audit verifies count completeness,
metric completeness, import/rollout provenance, and absence of diffuse
task-quality dominance.

## Next Branch Decision

Decision:

```text
continue
```

Continue branch:

```text
paper_route_executable_v2_support_first_measured_execution
```

Next milestone:

```text
m1893-executable-v2-support-first-repaired-bounded-smoke-runner-implementation
```

M1893 should implement the wrapper specified by M1891:

```text
src/autodrift/executable_v2_support_first_repaired_bounded_smoke_execution.py
tests/test_executable_v2_support_first_repaired_bounded_smoke_execution.py
```

It should use focused tests only and must not run the real `576`-rollout
bounded smoke. A later execution-command design milestone should register the
real command.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- branch synthesis and continuation decision;
- repaired bounded-smoke wrapper implementation is admitted.

Unsupported:

- repaired measured execution result;
- repaired task-quality conclusion;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
