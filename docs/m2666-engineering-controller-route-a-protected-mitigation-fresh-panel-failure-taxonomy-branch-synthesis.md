# M2666 Engineering Controller Route A Protected Mitigation Fresh Panel Failure Taxonomy Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_engineering_baseline_readiness_index_after_protected_taxonomy`
- manifest: `experiments/manifests/m2666-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-branch-synthesis.json`
- route reference: `docs/post-m2470-route-plan.md`
- parent audit: `docs/m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-result-audit.md`
- parent taxonomy summary: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json`
- parent fresh panel summary: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/summary.json`
- follow-up manifest: `experiments/manifests/m2667-engineering-controller-route-a-engineering-baseline-readiness-index-after-protected-taxonomy-materialization-preflight.json`
- next: `m2667-engineering-controller-route-a-engineering-baseline-readiness-index-after-protected-taxonomy-materialization-preflight`

## Evidence Summary

M2666 synthesizes the M2662-M2665 protected mitigation branch. This branch did
not change driver capability evidence. It changed the blocker description from
a same-row protected mitigation regression into a broad known-failure taxonomy.

Accepted evidence:

```text
M2662 fresh protected mitigation panel:
  status_pass: true
  fresh protected seeds: 268200, 268201, 268202, 268203
  panel spec rows: 12
  measured behavior rows: 60
  protected gate rows: 27
  protected gate blocking rows: 25
  protected gate regressed row count: 79
  actor contract: P0 observation 72 / action 3, no hidden/oracle actor input

M2663 result audit:
  accepted M2662 as protected blocker evidence only
  rejected repair success, ranking, promotion, validation, performance, paper,
    current-sim, high-fidelity validation, full ideal driver, and self-ID claims

M2664 failure taxonomy:
  status_pass: true
  subject taxonomy rows: 3
  axis taxonomy rows: 3
  metric taxonomy rows: 3
  combined taxonomy rows: 9
  claim boundary rows: 16
  gate matrix rows: 37
  all_policy_subjects_blocking: true
  all_axes_blocking: true
  all_metrics_blocking: true
  broad_protected_blocker_preserved: true

M2665 result audit:
  accepted M2664 as blocker-structure evidence only
  routed to branch synthesis before repair or interpretation
```

The current branch clarifies that protected mitigation is not a one-off public
row or a single-metric artifact. It remains broad across policy subjects,
fresh-protected axes, and protected metrics.

## Supported Claims

M2666 supports these bounded claims:

```text
Route A has a fresh protected mitigation failure-surface panel.
The panel was taxonomized into subject, axis, metric, and subject-axis rows.
The protected mitigation blocker is broad across policy subjects, axes, and metrics.
The protected blocker remains outside success denominators.
The actor/action boundary remains P0 observation 72 / action 3 with no hidden/oracle actor input.
M2662-M2665 provide known-failure evidence for Route A engineering baseline packaging.
```

The supported engineering state is:

```text
target improvement evidence exists from earlier Route A branches
protected mitigation remains a blocking known limitation
the next useful artifact is an engineering baseline readiness index that includes both facts
```

## Falsified Claims

M2666 rejects these interpretations:

```text
The protected mitigation issue is isolated to one checkpoint.
The protected mitigation issue is isolated to one fresh dynamics axis.
The protected mitigation issue is isolated to one metric.
M2664 taxonomy proves repair success.
M2664 taxonomy ranks controller families or selects a winner.
M2664 taxonomy supports checkpoint promotion.
Protected mitigation rows may be folded into ordinary success denominators.
Another same-row public repair loop is justified by the taxonomy alone.
The branch supports driver performance, validation, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID.
```

## Failure Taxonomy Summary

Active failure:

```text
behavior_regression:
  form: protected mitigation severity / obstacle penetration / clearance degradation
  broadness: all policy subjects, all axes, and all metrics block at least one claim row
  blocking rows: 25 / 27
  regressed row counts: 79
  protected role: unavoidable_mitigation
```

Saturated blocker groups:

```text
subject: m1154_original_policy, 9/9 blocking
axis: fresh_protected_close_cut_in_fault, 9/9 blocking
axis: fresh_protected_fault_delay_noise, 9/9 blocking
metric: obstacle_penetration_proxy_m, 9/9 blocking
metric: minimum_obstacle_clearance_m, 9/9 blocking
```

Mixed blocker groups:

```text
subject: m2532_guarded_repair_policy, 8/9 blocking
subject: m2537_mitigation_preserving_policy, 8/9 blocking
axis: fresh_protected_nominal, 7/9 blocking
metric: severity_proxy, 7/9 blocking
```

Controlled process risks:

```text
contract_violation:
  not observed. P0 72/action 3 and no hidden/oracle actor boundary remain intact.

metric_artifact:
  not supported as the explanation. The blocker appears across clearance,
  penetration, and severity semantics.

lineage_invalid:
  controlled. M2662-M2665 artifacts are present and traceable.
```

Active process risks:

```text
objective_overfit:
  high if the next step is another repair tuned against the same protected rows.

proof_washout:
  high if protected mitigation is hidden in aggregate success or weakened gates.
```

## Public-Gate Overfit Risk

Risk is high for another same-row protected mitigation repair loop. The branch
already moved through repair, mitigation-preserving objective design, repeated
repair execution, target/protected reporting, fresh protected panel
materialization, taxonomy, and audit. Reopening repair directly from M2664
would optimize the known protected public surface without changing the evidence
axis.

Risk is lower for Route A engineering baseline readiness indexing because it
changes the question:

```text
from: can we repair the protected mitigation row now?
to: what engineering baseline artifacts are ready, what limitations are known,
    and what remains missing before packaging or validation?
```

This pivot follows `docs/post-m2470-route-plan.md`, whose Route A near-term
artifacts include:

```text
baseline checkpoint list
actor input/output contract
public benchmark pack
known failure taxonomy
runtime/inference-cost report
scenario-role metric report
```

Several of these artifacts already exist. The missing piece is a current
post-M2665 readiness index that brings them together without implying
performance, ranking, or validation.

## Next Branch Decision

Decision:

```text
pivot_to_route_a_engineering_baseline_readiness_index_after_protected_taxonomy
```

Register M2667:

```text
m2667-engineering-controller-route-a-engineering-baseline-readiness-index-after-protected-taxonomy-materialization-preflight
```

M2667 should materialize a Route A engineering baseline readiness index from
existing artifacts only:

```text
M2541 baseline checkpoint list and actor contract
M2505 public benchmark pack
M2508/M2509 runtime inference-cost report and audit
M2657 scenario-role target/protected report
M2659/M2660 refreshed evidence index and audit
M2664/M2665 protected mitigation known-failure taxonomy and audit
docs/post-m2470-route-plan.md
```

The purpose is to make the engineering baseline state explicit:

```text
what is ready as an engineering baseline artifact
what is blocked by protected mitigation
what remains missing before validation or packaging
which next evidence route is admissible
```

M2667 must not run reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or success-rate computation.

No repair-success, driver-performance, validation, paper-level,
finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver,
or self-ID claim is made.

## Claim Boundary

M2666 is synthesis-only. It executed no reset, step, rollout, replay,
validation, training, PPO, source build, adapter probe, external simulation,
ranking, winner selection, promotion, or success-rate computation.

The current branch is closed as a taxonomy branch. The long-term driver goal
remains active and unproven.
