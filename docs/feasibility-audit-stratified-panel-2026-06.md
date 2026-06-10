# Feasibility Audit: Stratified Panel Report + Fresh-Seed Retest (2026-06)

## Scope / claim boundary

Route step 2 of `docs/feasibility-takeover-2026-06-route-decision.md`
(manual takeover order): stratified generator-feasibility reporting on the
fixed M3082/M3084 64-row panel, plus a disjoint fresh-seed retest of the
M3105 incumbent (`src/autodrift/active_safety_reflex_driver.py`,
`active_safety_reflex_driver_m3105_incumbent_v4_no_regression`) to test
whether the 100% feasible-row success rate is a property of the controller
or an artifact of the 64 fixed seeds. Measurement and counting only; no
driver-performance verdict, repair-success, robustness-result, validation,
ranking, promotion, high-fidelity, paper, or self-ID claim is made.

All runs are deterministic (CPU only, `AutoDriftEnv.reset(seed=...)` fully
re-seeds the env RNG); a full re-execution of the Part B measurement produced
byte-identical per-row outcomes
(`runs/feasibility_audit/fresh_panel_retest_rows_rerun.csv`).

## Method

- Environment reconstruction reuses the exact measurement code path of
  M3088/M3090/M3095/M3105: per panel row, the executable spec is taken from
  `runs/m3012_.../executable_source_specs.json`, joined with
  `executable_workload_rows.csv` via `m3090.full_fresh_plan`, then
  `profile_config_for_runtime` -> `env_config_for_executable_profile` ->
  `wrap_env_with_profile_mask(AutoDriftEnv(env_config))`.
- Generator feasibility label = `env.obstacle_scenario.label` after
  `reset(seed=eval_seed)` (`autodrift.scenarios.classify_obstacle_scenario`,
  evaluated at reset-time `speed_ref`/`mu`).
- Closed-loop rollouts use the shared `run_episode_with_policy` loop with the
  deployable `ActiveSafetyReflexDriver` (M3105 v4 incumbent policy config).
- Old-panel seeds: `401500 + axis*100 + pair*10 + role` (M3082
  `FRESH_SEED_BASE = 401500`, verified against all 64 recorded rows).
  Retest seeds: same formula at base **501500** (501500-501871); overlap with
  the old panel asserted to be **0**. Part C scan base 601500, stride 1000.

Reproduction:

```
PYTHONPATH=src python scripts/feasibility_audit/stratified_panel_report.py
PYTHONPATH=src python scripts/feasibility_audit/fresh_panel_retest.py --feasible-only-panel
```

## Part A: fixed 64-seed panel, stratified by generator label

Reconstructed label counts: **55 aeb_feasible / 0 aes_feasible /
3 drift_required / 6 unavoidable** — exactly matching the independent
route-decision audit. Joined with the recorded M3105 incumbent outcomes
(57 success / 5 collision / 2 offtrack):

| label (old panel) | n | success | collision | offtrack | speed_too_low | success rate |
|---|---|---|---|---|---|---|
| aeb_feasible | 55 | 55 | 0 | 0 | 0 | **100%** |
| drift_required | 3 | 0 | 1 | 2 | 0 | 0% |
| unavoidable | 6 | 2 | 4 | 0 | 0 | 33% |
| total | 64 | 57 | 5 | 2 | 0 | 89.06% |

Notes:
- All 7 residual failures sit on infeasible-labeled rows, confirming the
  route-decision conclusion. Attribution detail: the 5 collisions are
  4 unavoidable + 1 drift_required (row 0025), the 2 offtracks are both
  drift_required (rows 0013/0024) — the route-decision doc's "5 unavoidable +
  2 drift_required" split assigns row 0025 differently, but the label counts
  and the feasible-row 55/55 result are identical.
- 2 of 6 unavoidable-labeled rows nonetheless succeeded: the generator label
  is computed at reset (initial speed_ref/mu) and is conservative with respect
  to realized runtime outcomes (e.g. friction step changes).

Per-row artifact: `experiments/feasibility_audit/panel_feasibility_labels.csv`
(64 rows: fresh_panel_row_id, eval_seed, spec, label, m3105_outcome, ...).

## Part B: fresh-seed retest (seeds 501500-501871, zero overlap)

Same 16 spec x profile-binding panel structure, same per-row bindings, new
seed base. Label draw on the fresh seeds: **53 aeb_feasible /
0 aes_feasible / 4 drift_required / 7 unavoidable** (the unfiltered
generator again produces ~17% infeasible rows, concentrated on specs
0008/0010/0014 — the three high-speed `friction_limited_speed=false`,
`speed_range=[14,20]` specs — on both panels).

| label (fresh panel) | n | success | collision | offtrack | speed_too_low | success rate |
|---|---|---|---|---|---|---|
| aeb_feasible | 53 | 52 | 0 | 1 | 0 | **98.11%** |
| drift_required | 4 | 2 | 0 | 2 | 0 | 50% |
| unavoidable | 7 | 0 | 4 | 3 | 0 | 0% |
| total | 64 | 54 | 4 | 6 | 0 | 84.38% |

The single aeb_feasible failure (`fa-fresh-retest-episode-0053`,
panel row m3082-fresh-panel-0053, seed 501820, spec
m3012-executable-source-spec-0005, T4 stability_action_pressure, candidate
binding): `off_track` at step 212 with min clearance margin **20.77 m** and
mean speed 4.9 m/s — a low-speed track-keeping/stability failure far from the
obstacle, not an avoidance failure.

Per-row artifact: `experiments/feasibility_audit/fresh_panel_retest_rows.csv`;
summary: `experiments/feasibility_audit/fresh_panel_retest_summary.json`.

## Old vs fresh panel comparison

| label | old n | old success | old rate | fresh n | fresh success | fresh rate |
|---|---|---|---|---|---|---|
| aeb_feasible | 55 | 55 | 100% | 53 | 52 | 98.11% |
| drift_required | 3 | 0 | 0% | 4 | 2 | 50% |
| unavoidable | 6 | 2 | 33.3% | 7 | 0 | 0% |
| total | 64 | 57 | 89.06% | 64 | 54 | 84.38% |

Reading:
1. **The feasible-row ~100% essentially holds off the fixed seeds**: 52/53
   (98.1%; Wilson 95% CI roughly [0.90, 1.00]) vs 55/55, with the one miss
   being an off-obstacle stability offtrack rather than a failed avoidance.
   Pooled across both panels: aeb_feasible 107/108 = 99.1%.
2. The headline 57/64-style number is **not** stable across seed draws
   (89.1% -> 84.4%) because the unfiltered generator's infeasible-row count
   itself fluctuates (9 -> 11) and infeasible rows fail at 80-100%. Stratified
   reporting, not the raw 64-row rate, is the meaningful metric.
3. Infeasible-row outcomes are seed-noisy in both directions (old: 2/9
   "lucky" successes; fresh: 2/11), consistent with these rows being outside
   the controller's (and largely physics') reachable set.

## Part C: feasible-only ("deployment-criterion") panel

For each of the 64 row bindings, deterministic seed scan
(601500 + offset + k*1000) until the generator label is
aeb_feasible/aes_feasible; resulting panel: 57 aeb_feasible +
7 aes_feasible, all 64 rows feasible-labeled.

| label (feasible-only panel) | n | success | collision | offtrack | speed_too_low | success rate |
|---|---|---|---|---|---|---|
| aeb_feasible | 57 | 55 | 0 | 2 | 0 | 96.49% |
| aes_feasible | 7 | 5 | 0 | 2 | 0 | 71.4% |
| total | 64 | 60 | 0 | 4 | 0 | **93.75%** |

All 4 failures are offtracks (no collision anywhere on this panel), and all 4
sit on the three high-speed unfiltered specs (0008/0010/0014) at mean speeds
14-15 m/s: panel rows 0024 (seed 602631, aeb_feasible, parent), 0029 (seed
614660, aeb_feasible, candidate), 0010 (seed 605541, aes_feasible), 0013
(seed 607560, aes_feasible). The `aeb_feasible` label certifies braking
feasibility against the obstacle, not track-keeping feasibility at 14-20 m/s
on the r=18 m track, so a residual offtrack mode on the high-speed specs
survives even under the deployment criterion.

Per-row artifact: `experiments/feasibility_audit/feasible_only_panel_rows.csv`
(summary embedded in `fresh_panel_retest_summary.json` under
`feasible_only_panel`).

## Pooled feasible-row evidence (all fresh-seed measurements of the incumbent)

aeb_feasible: 55/55 (old) + 52/53 (retest) + 55/57 (feasible-only) =
**162/165 = 98.2%**; aes_feasible: 5/7. All 5 feasible-row failures are
offtracks (0 collisions on feasible rows across 172 episodes); 4 of 5 are on
the three high-speed specs, 1 is a low-speed stability offtrack.

## Conclusions

1. Part A reproduces the independent audit exactly (55/3/6 label split;
   M3105 100% on aeb_feasible; all 7 failures infeasible-labeled).
2. The fresh-seed retest **supports** the route decision: feasible-row
   success survives off the fixed seeds at 98-100%; the residual-repair
   branch's target rows remain infeasible-labeled rows that fail at ~100%.
3. New actionable finding: a small but real **high-speed offtrack mode on
   feasible rows** (specs 0008/0010/0014) appears once feasibility filtering
   is applied — 2/57 aeb_feasible + 2/7 aes_feasible offtracks on the
   deployment-criterion panel. If a follow-up repair branch is ever resumed,
   it should target track-keeping at 14-20 m/s on these specs, not the
   unavoidable obstacle rows.
4. Recommended reporting change: panel scoreboards should report
   per-label stratified rates (with the generator label re-derived by the
   measurement-path env rebuild) instead of the raw 64-row success rate.

## Artifacts

- `scripts/feasibility_audit/stratified_panel_report.py` (Part A)
- `scripts/feasibility_audit/fresh_panel_retest.py` (Parts B + C)
- `experiments/feasibility_audit/panel_feasibility_labels.csv`
- `experiments/feasibility_audit/fresh_panel_retest_rows.csv`
- `experiments/feasibility_audit/fresh_panel_retest_summary.json`
- `experiments/feasibility_audit/feasible_only_panel_rows.csv`
- `runs/feasibility_audit/stratified_panel_report_summary.json`
- `runs/feasibility_audit/fresh_panel_retest_rows_rerun.csv` /
  `fresh_panel_retest_summary_rerun.json` (determinism re-execution)
