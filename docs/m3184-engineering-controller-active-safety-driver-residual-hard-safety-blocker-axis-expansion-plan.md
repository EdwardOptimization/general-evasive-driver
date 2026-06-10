# M3184 Residual Hard-Safety Blocker Axis Expansion Plan

## Summary

- status: completed
- decision: `route_to_m3185_blocker_axis_expansion_pack_materialization_preflight`
- source synthesis: `docs/m3183-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-equivalence-synthesis.md`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3185-engineering-controller-active-safety-driver-residual-hard-safety-blocker-axis-expansion-pack-materialization-preflight`

## Purpose

M3184 turns the M3183 pivot into a concrete route plan. The steer-delta branch
has recovered the single M3170/M3172 regression but did not improve over M3105.
The next branch must therefore focus on the seven inherited residual blockers
instead of continuing local steer-delta or action-delta tuning.

M3184 is design/plan only. It does not reset or step the environment, run a
policy, mutate a driver, rank candidates, promote a checkpoint, or claim
validation, repair success, driver performance, current-sim verdict,
high-fidelity readiness, paper evidence, full-driver completion, feasibility,
or self-ID.

## Current Evidence

Accepted current-sim incumbent evidence:

```text
M3105/M3103:
  rows: 64
  success: 57
  collision: 5
  offtrack: 2
  speed-too-low: 0
  public runtime: ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]
```

Accepted steer-delta branch evidence:

```text
M3172:
  success: 56
  collision: 6
  offtrack: 2
  delta vs M3105: success -1, collision +1

M3177:
  single new regression localized to M3170 steer delta
  steer-delta ablation succeeds on the target row

M3179/M3181:
  success: 57
  collision: 5
  offtrack: 2
  delta vs M3105: success 0, collision 0, offtrack 0
```

Residual blocker evidence from M3156/M3161 remains:

```text
known residual blockers: 7
collision blockers: 5
offtrack blockers: 2
M3153 fixed action-channel sensitivity: 0/21
M3161 public execution blocker resolution: 0/7
```

## Problem

The remaining failure evidence is not a single unsafe steer delta. It spans:

- collision lateral intrusion rows with high-speed obstacle proximity;
- offtrack boundary recovery rows that terminate as either collision or
  offtrack;
- high sideslip and lateral error cases;
- terminal-invariant counterfactual rows where simple fixed action-channel
  variants did not change the outcome.

Continuing to tune a direct action delta without changing the evidence axis is
unlikely to create a credible driver improvement claim. The next step should
materialize a blocker-axis pack that separates actor-visible feature families
from offline labels.

## Route Decision

Route to M3185 blocker-axis expansion pack materialization.

M3185 should be no-new-execution and should write a machine-readable pack from
existing artifacts:

- `residual_blocker_axis_rows.csv`: the seven inherited blockers with proposed
  actor-visible evidence axis labels.
- `blocker_family_summary_rows.csv`: counts by blocker family, scenario axis,
  binding role, and termination type.
- `actor_visible_axis_candidate_rows.csv`: candidate evidence axes that can be
  computed from obs72 or internal public runtime telemetry without hidden
  labels.
- `forbidden_label_guard_rows.csv`: source ids, blocker labels, row outcomes,
  baseline outcomes, route labels, progress labels, verdict labels, target
  labels, TTC, and other hidden signals that remain forbidden actor inputs.
- `evidence_gap_rows.csv`: why M3153/M3177/M3181 do not justify another local
  action-delta loop.
- `candidate_admission_rows.csv`: what evidence is required before a future
  repair implementation is admitted.
- `gate_matrix.csv`, `summary.json`, doc, and a result-audit manifest.

## Candidate Evidence Axes

M3185 should materialize, but not implement, these route axes:

- `clearance_timing_axis`: actor-visible obstacle geometry, ego speed, and
  relative corridor cues for collision-lateral-intrusion rows.
- `boundary_recovery_stability_axis`: actor-visible lane/boundary geometry,
  lateral error, heading alignment, sideslip-like public state, and previous
  action response for offtrack-boundary-recovery rows.
- `action_authority_saturation_axis`: final/raw action bounds, clip fraction,
  action rate, and whether authority is already saturated before termination.
- `scenario_role_split_axis`: offline-only grouping by axis, binding role, and
  task family for analysis; these labels are not runtime actor inputs.

The route is admitted only if M3185 keeps runtime actor inputs inside obs72 and
uses labels only for offline evidence accounting.

## Stop Rules

Stop or synthesize again if:

- M3185 cannot produce all seven blocker rows with traceable source ids.
- proposed axes require hidden labels, target/source/route/outcome/progress
  fields, TTC, or baseline outcomes as runtime actor inputs.
- the pack would only re-open fixed action-channel delta tuning.
- the next implementation would mutate the public driver before a result audit.
- the branch tries to claim repair success, validation, current-sim verdict, or
  promotion from a no-new-execution artifact.

## Claim Boundary

M3184 is route planning only. M3105/M3103 remains the deployable incumbent.
M3179 remains an archived regression-neutral candidate artifact. No validation,
ranking, promotion, public driver default mutation, driver-performance,
current-sim verdict, high-fidelity, full-driver, repair-success,
robustness-result, feasibility-proof, paper, finite-window-vs-GRU, or self-ID
claim is made.
