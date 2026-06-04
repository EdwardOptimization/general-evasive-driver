# M2661 Engineering Controller Route A Post-Index Target/Protected Evidence Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_protected_mitigation_fresh_failure_surface_panel`
- manifest: `experiments/manifests/m2661-engineering-controller-route-a-post-index-target-protected-evidence-branch-synthesis.json`
- route reference: `docs/post-m2470-route-plan.md`
- parent audit: `docs/m2660-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-result-audit.md`
- parent index summary: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/summary.json`
- parent evidence index: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/evidence_index.csv`
- parent gap matrix: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/gap_matrix.csv`
- parent tradeoff report: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/summary.json`
- follow-up manifest: `experiments/manifests/m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-preflight.json`
- next: `m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-preflight`

## Evidence Summary

M2661 synthesizes the M2648-M2660 Route A target/protected evidence chain after
the refreshed index and audit. It accepts the branch state as a bounded
engineering evidence index, not as repair success or driver performance.

Current indexed evidence:

```text
M2641 source-only fresh panel:
  measured behavior rows: 160
  role families: stable_avoidable, stable_aes, drift_required_recovery, unavoidable_mitigation
  actor contract: P0 observation 72 / action 3, no hidden/oracle actor input

M2648 gap-targeted repair:
  target road-boundary gate: pass, 16/16 improved
  target drift-recovery gate: pass, 8/8 improved
  protected mitigation reference: fail, 1/8 regressed
  status: materialized, not promoted

M2650 localization:
  protected regression: unavoidable_mitigation seed 267101 fresh_fault_delay_noise
  severity_proxy: 3.953864 -> 3.987916
  likely driver: obstacle_penetration_proxy_worsened
  metric artifact: not supported

M2655 mitigation-preserving repair:
  selected diagnostic candidate: m2655_softened_gap_bias
  target_preservation_gates_all_passed: true
  protected_component_gates_all_passed: false
  target_and_protected_gates_all_passed: false
  failed protected gates:
    severity_proxy_non_regression
    obstacle_penetration_non_regression
    minimum_obstacle_clearance_preservation

M2657 target/protected report:
  scenario-role metric rows: 4
  target/protected tradeoff rows: 9
  protected regression focus rows: 8
  report gate rows: 8
  target roles: stable_avoidable, stable_aes, drift_required_recovery
  protected role: unavoidable_mitigation

M2659 refreshed evidence index:
  evidence rows: 12
  gap rows: 6
  claim-boundary rows: 16
  next-action rows: 5
  target evidence rows: 5
  protected blocking evidence rows: 9
  admitted next action before M2660: result audit only
```

M2660 accepts M2659 for branch synthesis only. The Route A near-term artifact
named in `docs/post-m2470-route-plan.md` is now present: the scenario-role
metric report exists and the baseline evidence index has been refreshed after
that report. The remaining blocker is not missing bookkeeping; it is the
protected mitigation failure surface.

## Supported Claims

M2661 supports these bounded claims:

```text
Route A has traceable source-only target improvement evidence.
Target roles are separated from protected mitigation rows.
M2655 target preservation passed while protected component gates failed.
The protected mitigation failure is behavior-level evidence, not a known metric artifact.
The M2655 selected candidate is diagnostic trace only, not a winner.
No checkpoint in this branch is promoted.
The actor/action boundary remains P0 observation 72 / action 3 with no hidden/oracle actor input.
The refreshed M2659 index and M2660 audit are ready to seed a new evidence route.
```

The supported engineering state is therefore:

```text
target improvements are usable diagnostic evidence
protected mitigation remains a blocking negative result
the current repair/index branch should close
```

## Falsified Claims

M2661 rejects these interpretations:

```text
Target gate pass proves repair success.
M2655 status_pass means the selected candidate is a winner.
The protected unavoidable_mitigation row can be included in an ordinary success denominator.
The protected severity, obstacle-penetration, and clearance gates can be weakened.
Another same-row public repair sweep is justified before a new evidence axis is selected.
The refreshed index is a validation result or driver-performance result.
The branch supports paper, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver, or self-ID claims.
```

## Failure Taxonomy Summary

Active failure:

```text
behavior_regression:
  form: protected mitigation severity / obstacle penetration / clearance regression
  M2648: 1/8 protected mitigation reference rows regressed
  M2655: protected severity, obstacle-penetration, and clearance component gates failed
  blocking role: unavoidable_mitigation
```

Active process risk:

```text
objective_overfit:
  form: repeated repair family preserves target rows while protected mitigation remains failed
  same-row public repair loop: closed by M2656

proof_washout:
  risk if protected mitigation gates are weakened or hidden inside aggregate success

metric_artifact:
  not supported by M2650 localization

contract_violation:
  not observed; P0 72/action 3 and no hidden/oracle actor boundary remain intact

lineage_invalid:
  not observed; M2657-M2660 keep M2641/M2648/M2650/M2655 lineage traceable
```

## Public-Gate Overfit Risk

Risk is high for another same-row source-only repair loop. The branch already
ran target-only and gate-aware mitigation-preserving repair attempts, then
reanalyzed and indexed the target/protected tradeoff. Repeating candidate
tuning against the same protected public rows would mostly optimize visible
gates and blur the negative result.

Risk is lower for a new protected mitigation failure-surface panel because it
changes the evidence axis:

```text
from: same-row target/protected repair and index loop
to: fresh source-only protected mitigation failure-surface panel
```

That next route must use fresh seeds or dynamics axes, preserve the human-view
actor contract, and avoid ranking, validation, training, promotion, or success
claims.

## Next Branch Decision

Decision:

```text
pivot_to_route_a_protected_mitigation_fresh_failure_surface_panel
```

Register M2662:

```text
m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-preflight
```

M2662 should materialize a fresh Route A source-only protected mitigation
failure-surface panel. Its purpose is to expand evidence around the blocking
protected mitigation behavior, not to repair or rank controllers.

Required boundary for M2662:

```text
consume M2657-M2661 evidence as design inputs only
sample fresh protected mitigation rows or axes
preserve target/protected split
preserve P0 observation 72 / action 3
keep taxonomy, localization, gate, and route labels actor-invisible
emit claim-boundary rows that reject repair success and driver performance
```

M2662 must not run training, PPO, promotion, controller-family ranking,
success-rate verdict computation, paper comparison, current-sim verdict, high-
fidelity validation, or self-identification tests.

## Claim Boundary

M2661 is synthesis-only. It executed no reset, step, rollout, replay,
validation, training, PPO, source build, adapter probe, external simulation,
ranking, winner selection, promotion, or success-rate computation.

No repair-success, driver-performance, validation, paper-level,
finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver,
or self-ID claim is made.
