# M2732 Engineering Controller Route A Evidence Index After Exact-Executable Repair Refresh Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2731_route_to_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_design`
- manifest: `experiments/manifests/m2732-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-result-audit.json`
- parent summary: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/summary.json`
- parent doc: `docs/m2731-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2733-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-design.json`
- next: `m2733-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-design`

## Audit Verdict

M2732 accepts M2731 as complete and claim-safe evidence/readiness indexing.
M2731 performed source-artifact reanalysis only and wrote:

```text
summary status_pass: true
evidence rows: 10
blocker rows: 5
next-action admission rows: 6
claim-boundary rows: 19
gate rows: 21
gate_matrix_pass: true
```

The audit rejects direct execution, ranking, validation, performance, paper,
current-sim, high-fidelity, full ideal driver, and self-ID interpretation from
M2731. M2731 is an index and route-admission artifact only.

## Diagnostic Boundary

M2731 preserves the accepted M2728/M2729 negative diagnostic:

```text
M2728 repair execution rows: 31
diagnostic success: 1/31
collision: 3/31
off_track: 27/31
```

These rows remain non-ranking and non-verdict evidence. They do not support
repair success, driver performance, validation readiness, validation result,
current-sim verdict, high-fidelity validation readiness/result, paper evidence,
finite-window-vs-GRU evidence, full ideal driver completion, or level3 self-ID.

## Blocker Boundary

M2731 keeps the active blockers visible:

```text
same-surface exact-executable offtrack repair: closed by M2730 pivot
protected mitigation blocker: preserved outside success denominators
HF3 selected-platform execution: paused by M2638 source dependency blocker
actor contract: P0 observation 72 / action 3 preserved
hidden/oracle actor input: false
```

The blocker matrix correctly rejects another direct same-surface repair
execution. It also rejects HF3 selected-platform execution until a valid source
root, package route, or dependency acquisition manifest exists.

## Actor Boundary

The audit finds no actor-contract expansion:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input detected: false
taxonomy labels actor-visible: false
repair-target labels actor-visible: false
objective-gate labels actor-visible: false
route-decision labels actor-visible: false
verdict labels actor-visible: false
```

This preserves the deployable human-view contract required by the Route A
engineering controller mainline.

## Next Route Decision

M2732 admits one bounded follow-up:

```text
m2733-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-design
```

Rationale:

```text
M2730 closed same-surface exact-executable offtrack repair.
M2731 indexed the negative diagnostic and active blockers.
M2732 accepts that index and should now leave the audit/index loop.
The next useful step is a non-same-surface closed-loop evidence surface design
that can define source-diverse execution materialization without weakening the
actor contract or claiming performance.
```

M2733 is design-only. It must not reset, step, rollout, replay, validate,
train, run PPO, source build, adapter probe, run external simulation, rank
controllers, select a winner, promote a checkpoint, or compute success-rate
verdicts. Its purpose is to define the next evidence surface after the M2728
negative result, not to claim driver progress.

## Rejected Shortcuts

M2732 rejects:

```text
same-surface exact-executable offtrack repair execution from M2728 rows
profile ranking from M2728 aggregates
Route A validation readiness from M2731 indexing
driver-performance or repair-success interpretation
HF3 selected-platform execution while M2638 remains unresolved
paper, finite-window-vs-GRU, current-sim, high-fidelity, full-driver, or self-ID claims
```
