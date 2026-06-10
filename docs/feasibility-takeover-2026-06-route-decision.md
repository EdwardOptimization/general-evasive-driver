# Feasibility Takeover Route Decision (2026-06-11)

## Status

- decision: `manual_takeover_block_m3213_residual_repair_route`
- scope: route decision only; no driver-performance, current-sim, high-fidelity,
  repair-success, robustness-result, or self-ID claim is made by this document.
- author: manual analysis session (outside the autonomous milestone loop),
  2026-06-10/11.

## Why M3213 is blocked

An independent feasibility audit of the seven residual hard-safety failures
(`m3084-measurement-episode-0007/0010/0025/0026/0029` collisions,
`0013/0024` offtrack) reconstructed the hidden physical parameters of each
episode deterministically (`AutoDriftEnv(spec.env_config).reset(seed)`,
verified against recorded artifacts to 1e-6) and computed physical
avoidability bounds that no prior milestone had computed:

1. The M3082 fresh panel was generated **without feasibility filtering**:
   all 16 source specs in
   `runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_source_specs.json`
   allow `unavoidable` labels and set `require_aeb_infeasible: false`; three
   specs combine `friction_limited_speed=false` with `speed_range=[14,20]` on
   an r=18 m track, so required centripetal acceleration (10.9-22.2 m/s^2)
   exceeds the grip ceiling (mu*g <= 9.32 m/s^2) from step 0.
2. Reconstructed generator labels for the 64 panel rows:
   **55 aeb_feasible / 3 drift_required / 6 unavoidable**. The M3105 incumbent
   succeeds on **55/55 aeb_feasible rows**; all 7 residual failures are
   unavoidable (4) or drift_required (3) rows (correction 2026-06-11: the five
   collisions are 4 unavoidable + 1 drift_required row 0025; both offtrack
   rows are drift_required — see
   `experiments/feasibility_audit/panel_feasibility_labels.csv`).
3. Point-mass / friction-circle upper bounds (generous toward the controller)
   show the five collision rows require 22.5-85.4 m/s^2 of braking against
   2.2-4.2 m/s^2 available, and both offtrack rows cross the boundary before
   the pass point under any control sequence (0024/0025 at medium confidence).
4. The union of per-row successes across all 13 historical full-panel
   controller variants is exactly 57/64; the 7 rows were passed 0/13 times.

Conclusion: 57/64 = 0.890625 is at (or within one row of) the physical
ceiling of this fixed 64-seed panel. Continuing the
M3108-M3212 residual-repair branch (and its planned continuation M3213)
cannot produce outcome changes; the ~107 behavior-neutral milestones since
M3105 are consistent with this, not anomalous.

## New route (manual takeover order)

1. **Oracle certification** of the 7 residual rows: privileged search over
   control sequences (full-preview and reveal-constrained tiers) to convert
   the computed ceiling from inference to measurement.
   Artifacts: `scripts/feasibility_audit/`, `docs/feasibility-audit-oracle-certification-2026-06.md`.
2. **Stratified reporting + fresh-seed retest**: add generator feasibility
   labels to panel reporting; regenerate a disjoint fresh panel and re-measure
   the incumbent to test whether feasible-row 100% holds off the fixed seeds.
   Artifacts: `docs/feasibility-audit-stratified-panel-2026-06.md`.
3. **Unblock Chrono (HF backend)**: install the pinned Chrono/pychrono
   dependency per M2880 and proceed to the HF4 discrepancy report.
4. **Self-ID completion experiments**: observation-degradation task family in
   the environment and a privileged positive-control detector through the
   existing hidden-swap gates, upgrading `not_admitted` to a complete
   conditional negative result.
5. Papers (conditional-negative/methodology; autonomous-loop case study).

Resume condition for the autonomous loop: a pre-repair feasibility oracle gate
and a blocked-dependency escalation hook are added to the loop process, so the
M3108-M3212 failure mode (repairing physically unsolvable rows) cannot recur.
