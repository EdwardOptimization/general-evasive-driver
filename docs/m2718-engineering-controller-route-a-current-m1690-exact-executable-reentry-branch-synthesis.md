# M2718 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_preflight`
- manifest: `experiments/manifests/m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis.json`
- synthesis artifact: `docs/m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis.md`
- parent audit: `docs/m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit.md`
- parent summary: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight.json`
- next: `m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight`

## Evidence Summary

M2713-M2717 completed one bounded current-M1690 exact-executable reentry branch:
design, materialization, materialization audit, bounded execution, and execution
result audit. This branch produced real closed-loop diagnostic rows on an
existing current-runner surface while preserving the protected proposal
exclusion boundary.

Accepted M2713-M2717 evidence:

```text
M2713 design:
  selected 9 M2693 anchor task_source_ids
  selected 4 existing M1690 profiles
  expected exact executable candidate rows: 36
  protected M2710 proposal rows excluded: 12

M2714 materialization:
  status_pass: true
  exact executable candidate rows: 36
  profile context rows: 36
  protected proposal exclusion rows: 12
  gate rows: 35
  all candidate rows source-backed existing M1690: true

M2715 audit:
  accepted M2714 complete and claim-safe
  admitted one bounded execution preflight

M2716 bounded execution:
  status_pass: true
  exact execution rows: 36/36
  failure rows: 0
  profile aggregate rows: 4
  anchor aggregate rows: 9
  protected proposal exclusion audit rows: 12
  actor-contract join rows: 12
  claim-boundary rows: 33
  gate rows: 20
  gate_matrix_pass: true

M2717 audit:
  accepted M2716 complete and claim-safe
  rejected profile ranking validation performance paper current-sim high-fidelity full-driver and self-ID interpretation
  routed to branch synthesis
```

The M2716 row-level diagnostic outcome remains weak and off-track dominated:

```text
total exact execution rows: 36
diagnostic success rows: 3
obstacle collision rows: 2
off_track termination rows: 31
failure rows: 0
```

By profile, without ranking:

```text
L0_current_masked: 0/9 success, 1/9 collision, 8/9 off_track
L2_window_50_current_tiled: 0/9 success, 0/9 collision, 9/9 off_track
L3_online_gru: 0/9 success, 0/9 collision, 9/9 off_track
L3_reset_control_corrected: 3/9 success, 1/9 collision, 5/9 off_track
```

By anchor:

```text
m1680-spec-0000: 0/4 success, 0/4 collision, 4/4 off_track
m1680-spec-0002: 1/4 success, 0/4 collision, 3/4 off_track
m1680-spec-0004: 0/4 success, 0/4 collision, 4/4 off_track
m1680-spec-0005: 0/4 success, 0/4 collision, 4/4 off_track
m1680-spec-0006: 0/4 success, 0/4 collision, 4/4 off_track
m1680-spec-0036: 1/4 success, 1/4 collision, 2/4 off_track
m1680-spec-0038: 0/4 success, 1/4 collision, 3/4 off_track
m1680-spec-0040: 1/4 success, 0/4 collision, 3/4 off_track
m1680-spec-0041: 0/4 success, 0/4 collision, 4/4 off_track
```

Actor and claim boundaries remain intact:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
target labels actor-visible: false
protected labels actor-visible: false
profile labels actor-visible: false
blocker labels actor-visible: false
route labels actor-visible: false
verdict labels actor-visible: false
protected rows in ordinary success denominators: false
```

## Supported Claims

M2718 supports only these operational claims:

```text
M2713-M2717 produced a complete exact-executable current-M1690 reentry branch.

M2716 executed 36/36 existing current-M1690 candidate rows and recorded 0
failure rows.

M2716/M2717 preserved actor 72/action 3, no hidden/oracle actor input,
actor-invisible labels, and protected proposal exclusions outside execution
and denominators.

The branch produced diagnostic behavior rows useful for failure taxonomy and
target selection.

The branch did not produce validation, performance, ranking, paper,
current-sim, high-fidelity, full ideal driver, or self-ID evidence.
```

The useful result is not that a profile won. The useful result is that the
existing executable surface now has bounded diagnostic rows that expose a
dominant off-track failure surface with a smaller collision surface and a few
diagnostic success rows that require row-level taxonomy before repair design.

## Falsified Claims

M2718 rejects these interpretations:

```text
M2716 proves repair success.
M2716 ranks controller families.
M2716 selects L3_reset_control_corrected as a winner.
M2716 proves current-response sufficiency or finite-window-vs-GRU conclusions.
M2716 validates driver performance.
M2716 supplies paper-level evidence.
M2716 resolves current-sim or high-fidelity validation.
M2716 executes or validates protected mitigation proposal rows.
M2716 proves full ideal driver completion or level3 self-identification.
```

The branch also rejects another direct same-panel execution as the immediate
next step. Repeating the 36-row execution before taxonomy would risk optimizing
around a narrow public panel instead of identifying the failure surfaces that
could change repair or integration work.

## Failure Taxonomy Summary

Accepted active failures or blockers:

```text
scenario_sampling_failure:
  Active. The exact executable panel is off-track dominated with 31/36
  off_track terminations.

behavior_regression:
  Active/incomplete. The protected proposal side remains excluded and cannot be
  assessed as protected mitigation behavior evidence.

objective_overfit:
  Medium if the branch repeats same-panel execution or treats the 3/36
  diagnostic successes as a profile winner.

proof_washout:
  Controlled only while aggregate rows remain diagnostic and non-ranking.
```

Not observed:

```text
contract_violation
lineage_invalid
hidden/oracle actor input injection
actor-visible target/protected/profile/blocker/route/verdict labels
protected denominator leakage
unrecorded execution failure rows
controller ranking or winner selection
checkpoint promotion
private holdout contamination
```

## Public Gate Overfit Risk

Risk entering M2718: `medium`.

Reason:

```text
M2716 produced real execution rows, so this is no longer only static artifact
churn. However, the panel is small and branch-specific: 9 anchors x 4 profiles.
Direct repetition or profile ranking would turn it into a local public-gate
loop.
```

Risk after M2718: `medium-low` only if the next route converts M2716 rows into
failure taxonomy and target selection without claiming performance or ranking.

The mitigation is strict:

```text
Do not repeat the exact executable panel immediately.

Do not rank profiles or select a winner from M2716 aggregates.

Do not execute M2710 protected proposal rows.

Materialize a no-rollout failure taxonomy from M2716 rows first, preserving
off_track, obstacle_collision, diagnostic_success, and protected-excluded
boundaries.
```

## Next Branch Decision

Decision:

```text
continue_to_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_preflight
```

The next bounded route is:

```text
m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight
```

Rationale:

```text
Stopping the Route A branch is premature because M2716 produced new behavior
evidence.

Direct profile ranking is forbidden because M2716 was not a fair ranking
benchmark and aggregate rows are diagnostic only.

Direct same-panel execution would be local search before the failure surface is
classified.

Direct protected execution remains forbidden because M2710 proposal rows are
not exact existing M1690 workload rows and were not executed.

The next evidence-changing step is no-rollout materialization of a failure
taxonomy over M2716 exact execution rows and protected exclusions. That can
identify whether the next active route should be off-track repair design,
collision repair design, protected executable-surface implementation, Route C
dependency work, or stop/pivot.
```

M2719 must not execute reset, step, rollout, replay, validation, training, PPO,
private holdout, ranking, winner selection, promotion, success-rate verdict,
driver-performance claim, paper claim, current-sim verdict, high-fidelity
validation claim, full ideal driver claim, or self-ID claim.
