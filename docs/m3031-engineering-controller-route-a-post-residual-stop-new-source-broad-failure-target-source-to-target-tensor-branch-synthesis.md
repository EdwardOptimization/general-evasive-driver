# M3031 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target-Source To Target-Tensor Branch Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m3032_target_tensor_materialization_preflight`
- parent audit: `docs/m3030-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-result-audit.md`
- follow-up manifest: `experiments/manifests/m3032-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-preflight.json`
- next: `m3032-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-preflight`

M3031 synthesizes the post-residual-stop source-axis-expansion branch because
the workflow cadence blocked another direct non-synthesis milestone. The
branch has produced new-source contracts, executable workload/env artifacts,
bounded diagnostic execution rows, failure localization, broad-failure
objective contracts, raw actor-view traces, and target-source feasibility
rows. It has not repaired behavior and cannot support driver performance,
paper, current-sim verdict, high-fidelity validation, full-driver,
finite-window-vs-GRU, or self-ID claims.

## Synthesis Questions

### evidence_summary

The M3005-M3030 source-axis branch changed the project state from exhausted
same-source evidence to a claim-safe new-source broad-failure target-source
panel:

```text
M3005: accepted M3004 source-axis expansion and rejected same-surface reuse.
M3006-M3010: materialized and audited new task-source identities and executable workload contracts.
M3011-M3013: materialized and audited executable environment contracts.
M3014-M3017: executed the 32-row new-source diagnostic denominator and synthesized a strongly negative result.
M3018-M3020: localized broad failures across candidate and parent profiles.
M3021-M3023: admitted and audited broad-failure objective contracts.
M3024-M3026: materialized and audited target-source readiness with explicit raw-trace blockers.
M3027-M3028: captured and audited raw deployable actor-view traces for all 32 rows.
M3029-M3030: materialized and audited target-source feasibility for 29 future target candidates plus 3 success identity guards.
```

Accepted M3030/M3029 evidence:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
target-source plan rows: 32
target-source candidate rows: 29
success identity guard rows: 3
target-source availability rows: 32
target-source feasibility established rows: 29
raw trace joins: 32
raw trace files: 32
trace step range: 31-177
actor observation/action: 72/action 3
numeric target tensors: 0
local-action search runs: 0
```

This is a real dataset/panel admission improvement. It is not behavior
improvement, validation evidence, or repair success.

### supported_claims

Supported claims:

```text
the branch created new task-source identities rather than reusing exhausted M1690/M2919/M3000 surfaces
the 32-row new-source denominator was executed diagnostically and preserved
the broad-failure surface is strongly negative and offtrack-dominant with collision and speed-floor guard context
29 future target candidates now have legal raw actor-view trace-backed target-source feasibility
3 success identity rows remain guard-only and non-positive targets
actor observation/action remains 72/action 3
hidden oracle future-target source route outcome objective readiness progress verdict and TTC actor inputs remain blocked
target tensor materialization is now a materially different next step rather than another static readiness artifact
```

### falsified_claims

Not supported and therefore rejected:

```text
repair success
driver performance
validation readiness or validation result
current-sim verdict
paper evidence
high-fidelity validation readiness or result
finite-window-vs-GRU conclusion
full ideal driver completion
level3 self-identification
target tensor quality
fitting readiness
checkpoint ranking or promotion
controller/source/profile winner selection
```

### failure_taxonomy_summary

The active failure surface is still broad and negative. M3015/M3016 recorded
3 success rows, 5 collision rows, 23 off-track terminations, 4 obstacle
collision terminations, and 2 speed-too-low terminations. M3018-M3020
localized the negative surface across 13/16 non-success task-source ids under
both candidate and parent profiles.

The active process risk is local-search/process overhead. The branch needed
many materialization and audit milestones to preserve source identity,
execution, raw trace, target-source, actor, and claim boundaries. That overhead
is now high enough to require synthesis before the next step. The next step is
allowed only because M3029/M3030 changed the available evidence surface from
readiness/blockers to legal target-source rows.

### public_gate_overfit_risk

Risk is medium. The branch did not tune a policy on public proof rows or select
a winning controller. It did, however, accumulate many static artifacts around
one Route A repair path. M3032 must therefore operate on the full M3029
denominator and preserve every row role. It must not cherry-pick the 29
candidate rows without accounting for the 3 success guards, and it must not
interpret target tensors as validation, ranking, repair success, or paper
evidence.

### next_branch_decision

Decision:

```text
continue_to_m3032_target_tensor_materialization_preflight
```

M3032 should be a bounded infrastructure milestone. It may materialize
trainer-side target tensors, masks, weights, and provenance from the
M3030-accepted M3029 feasibility rows. It must not fit, train, validate, rank,
select a winner, promote or mutate checkpoints, tune profiles, or claim repair
success, driver performance, paper evidence, current-sim verdict,
high-fidelity validation, finite-window-vs-GRU, full-driver completion, or
self-ID evidence.

If M3032 cannot materialize numeric target tensors while keeping target labels
and provenance actor-invisible and preserving success identity guards, the
branch should route to artifact repair, pivot, or stop rather than continue
process-only work.
