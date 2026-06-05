# M2730 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_evidence_index_after_exact_executable_repair_refresh`
- manifest: `experiments/manifests/m2730-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-result-synthesis.json`
- synthesis artifact: `docs/m2730-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-result-synthesis.md`
- parent audit: `docs/m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-result-audit.md`
- parent summary: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2731-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-preflight.json`
- next: `m2731-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-preflight`

## Evidence Summary

M2719-M2729 converted the M2716 exact-executable reentry diagnostic panel into
a bounded offtrack repair branch:

```text
M2719 taxonomy:
  48 taxonomy rows
  36 exact execution rows
  31 off_track rows
  2 obstacle_collision rows
  3 diagnostic_success rows
  12 protected_excluded rows

M2721 target panel:
  31 offtrack target rows
  2 collision caution rows
  3 diagnostic success context rows
  12 protected exclusion rows

M2725 candidate pack:
  31 candidate target rows
  15 shared repair overlay rows
  17 guardrail rows
  9 actor rows
  23 claim rows
  17 gate rows

M2728 bounded repair execution:
  31 repair execution rows
  0 candidate execution failure rows
  465 overlay application rows
  17 guardrail audit rows
  4 profile aggregates
  9 anchor aggregates
  12 actor rows
  38 claim rows
  21 gate rows
  gate_matrix_pass: true
```

The branch is complete and claim-safe, but it did not produce a repair success
surface:

```text
M2728 diagnostic outcome:
  success: 1/31
  collision: 3/31
  off_track terminations: 27/31

M2728 profile diagnostics:
  L0_current_masked: success 0/8, collision 1/8, offtrack 7/8
  L2_window_50_current_tiled: success 0/9, collision 0/9, offtrack 9/9
  L3_online_gru: success 0/9, collision 2/9, offtrack 7/9
  L3_reset_control_corrected: success 1/5, collision 0/5, offtrack 4/5
```

M2729 audited these artifacts and accepted only this bounded claim:

```text
M2728 repair execution artifacts are complete and claim-safe, but the
diagnostic outcome remains offtrack-dominated and does not justify
repair-success, performance, validation, current-sim, paper, high-fidelity,
full-driver, or self-ID interpretation.
```

## Supported Claims

M2730 supports these operational claims:

```text
M2719-M2729 form a complete Route A offtrack repair diagnostic branch.

The branch preserved actor observation shape 72 and action shape 3.

No hidden/oracle actor input, actor-visible target labels, profile labels,
protected labels, route labels, or verdict labels were introduced.

M2728 applied repair overlays only through temporary run-dir snapshots and did
not overwrite active configs or profile-specific tune.

M2728 executed only the 31 M2725 candidate target rows; protected and guardrail
rows remained non-target and outside ordinary success denominators.

The branch produced useful negative diagnostic evidence: the shared overlay
repair did not solve the current-M1690 exact-executable offtrack surface.

The next step should not be another same-surface repair execution. It should
refresh Route A evidence/readiness admission using this negative result plus
the existing HF3 source dependency blocker and protected mitigation blockers.
```

## Falsified Claims

M2730 rejects these interpretations:

```text
M2728 repaired the offtrack surface.
M2728 selected a best controller profile.
M2728 proved driver performance.
M2728 granted validation readiness or produced a validation result.
M2728 produced a current-sim verdict.
M2728 produced high-fidelity validation readiness or a high-fidelity result.
M2728 produced paper evidence, finite-window-vs-GRU evidence, current-response
sufficiency evidence, full ideal driver completion, or level3
self-identification evidence.
```

M2730 also rejects another immediate same-surface repair loop. The post-M2470
route plan allows bounded current-sim diagnostic work, but it warns against
turning current-sim readiness or public-gate repair into the main loop. The
M2719-M2729 branch has now completed target taxonomy, target panel,
synthesis, repair design, candidate materialization, execution design, bounded
execution, and audit on the same offtrack surface.

## Failure Taxonomy Summary

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle actor
  input, actor-invisible labels, protected-row denominator exclusion, and
  temporary overlay snapshots were preserved.
- `lineage_invalid`: not observed. The branch traces from M2716 diagnostics
  through M2719 taxonomy, M2721 target panel, M2725 candidate rows, M2728
  bounded execution, and M2729 audit.
- `metric_artifact`: controlled. Profile and anchor aggregates are diagnostic
  only and non-ranking.
- `scenario_sampling_failure`: active. The same current-M1690 exact-executable
  offtrack surface remains offtrack-dominated after the shared repair overlay.
- `behavior_regression`: active. Collision caution is visible as 3/31 M2728
  collision outcomes and protected mitigation rows remain blocked outside this
  exact-executable surface.
- `objective_overfit`: high if the branch continues with another same-surface
  repair design/materialization/execution loop. Controlled only by pivoting.
- `proof_washout`: controlled. The synthesis rejects repair success,
  performance, validation, paper, current-sim, high-fidelity, full-driver, and
  self-ID interpretations.

## Public Gate Overfit Risk

Risk entering M2730: `high`.

Reason:

```text
M2719-M2729 repeatedly refined the same offtrack repair surface:
taxonomy, target panel, audit, synthesis, repair design, candidate
materialization, audit, execution design, bounded execution, and audit.
```

That work was useful until M2728 produced the first closed-loop repair
diagnostic result. Once the result is negative, another same-surface repair
attempt would optimize the current public M1690 offtrack rows without proving a
broader Route A engineering controller capability.

Risk after M2730: `medium-low` only if the active branch leaves same-surface
offtrack repair and refreshes next-action admission from the whole Route A
evidence set.

The important route constraints are:

```text
Do not schedule another current-M1690 exact-executable offtrack repair
execution from M2728 rows.

Do not rank controller profiles from M2728 profile aggregates.

Do not claim driver performance or validation from M2728.

Keep HF3 selected-platform execution paused until the M2638 source dependency
contract is satisfied.

Use M2728/M2729 as negative diagnostic evidence in a Route A evidence/readiness
index, then choose a non-same-surface evidence route.
```

## Next Branch Decision

Decision:

```text
pivot_to_route_a_evidence_index_after_exact_executable_repair_refresh
```

The next bounded route is:

```text
m2731-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-preflight
```

Rationale:

```text
Stopping the whole project is wrong because the long-term driver goal remains
active and the full ideal driver gate has not passed.

Continuing same-surface offtrack repair is local search because M2728 already
ran the shared repair overlay and M2729 accepted the negative diagnostic.

Direct validation, ranking, promotion, performance, paper, current-sim,
high-fidelity, full-driver, or self-ID interpretation is forbidden by M2729.

External HF3 execution remains paused by M2638 until a valid local source root,
approved package route, or explicit dependency-acquisition manifest exists.

The highest leverage next action is a fresh Route A evidence/readiness index
that integrates M2728/M2729 negative offtrack repair evidence with existing
baseline, actor-contract, runtime, benchmark-pack, protected mitigation, and
HF3 blocker artifacts. That index should decide the next non-overfit
evidence-expanding route.
```

M2731 must not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, success-rate verdict computation, or performance interpretation.

## Claim Boundary

Allowed M2730 claim:

```text
M2719-M2729 are a complete claim-safe offtrack repair diagnostic branch, and
their negative M2728 result requires pivoting away from same-surface repair
toward Route A evidence/readiness admission.
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
