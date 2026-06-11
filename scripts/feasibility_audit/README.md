# Feasibility Audit Measurement Index (2026-06)

Index of every script in this directory (37 as of 2026-06-12), mapped to its
primary result artifacts and the conclusion document that interprets them.
All scripts are deterministic, CPU-only, and run as
`PYTHONPATH=src python scripts/feasibility_audit/<script>.py` from the repo
root (most have a `--quick` smoke mode; see each docstring). Aggregated
results live in `experiments/feasibility_audit/`; per-episode rows, logs,
traces, and determinism re-runs live in `runs/feasibility_audit/`.

Created as WP6.3 of `docs/research-plan-phase2-capability-boundary-tracking.md`.

## 1. Oracle certification (physical ceiling)

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `oracle_certification.py` | `experiments/feasibility_audit/oracle_certification_results.json`; `runs/feasibility_audit/oracle_certification_sequences.json`, `oracle_certification_run.log` | `docs/feasibility-audit-oracle-certification-2026-06.md` | Can ANY controller (full-preview or reveal-constrained, 43,372 privileged rollouts) repair the 7 residual hard-safety rows? No — 7/7 hard-fail in both tiers; the 57/64 panel ceiling is measured, not just computed. |

## 2. Panels: stratified reporting, fresh-seed retest, v5 candidate

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `stratified_panel_report.py` | `experiments/feasibility_audit/panel_feasibility_labels.csv`; `runs/feasibility_audit/stratified_panel_report_summary.json` | `docs/feasibility-audit-stratified-panel-2026-06.md` | What are the generator feasibility labels of the fixed 64-row panel, stratifying the incumbent's outcomes? 55 aeb_feasible (100% success) / 3 drift_required / 6 unavoidable. |
| `fresh_panel_retest.py` | `experiments/feasibility_audit/fresh_panel_retest_rows.csv`, `fresh_panel_retest_summary.json`, `feasible_only_panel_rows.csv`; rerun copies in `runs/feasibility_audit/` | `docs/feasibility-audit-stratified-panel-2026-06.md` | Does the incumbent's feasible-row ~100% hold off the fixed seeds? Yes: 52/53 fresh (98.1%), pooled 162/165 aeb_feasible, 0 collisions on 172 feasible episodes; exposes a residual high-speed offtrack mode. |
| `v5_offtrack_diagnosis.py` | `experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json`; `runs/feasibility_audit/v5_offtrack_diagnosis_traces.json` | `docs/feasibility-audit-v5-highspeed-tracking-repair-2026-06.md` | What is the mechanism of the 5 known zero-collision offtrack failures? Born over the friction speed limit + reactive edge braking eats lateral grip; coast beats braking on all 4 high-speed rows. |
| `v5_offtrack_ceiling_probe.py` | `experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv` | `docs/feasibility-audit-v5-highspeed-tracking-repair-2026-06.md` | Are the 4 high-speed offtrack rows reachable by reflex-family control? 84 privileged action schedules per row: only 0024 passes (40/84); 0010/0013/0029 = 0/84, beyond the probe ceiling. |
| `v5_panel_validation.py` | `experiments/feasibility_audit/v5_panel_validation_rows.csv`, `v5_panel_validation_summary.json`; byte-identical rerun copies in `runs/feasibility_audit/` | `docs/feasibility-audit-v5-highspeed-tracking-repair-2026-06.md` | Does the v5 candidate fix tracking offtracks without regressing v4? 4 panels x 64 rows x 2 drivers (512 episodes): fixes 2 rows, 0 regressions, feasible-row collisions 1 -> 0. |

## 3. Chrono dual-backend (high fidelity)

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `chrono_backend_worker.py` | (no JSON/CSV; subprocess worker run inside the `chrono` conda env) | `docs/feasibility-route-hf-backend-2026-06.md` | Infrastructure: hosts the pychrono Sedan backend behind a line-protocol subprocess so the project env never imports pychrono. |
| `chrono_worker_client.py` | (no JSON/CSV; client library) | `docs/feasibility-route-hf-backend-2026-06.md` | Infrastructure: client side of the worker protocol (spawn, scenario load, step, teardown). |
| `chrono_backend_smoke.py` | `runs/feasibility_audit/chrono_smoke_summary.json` | `docs/feasibility-route-hf-backend-2026-06.md` | Does the incumbent run closed-loop on the Chrono backend at all (reset/step/outcome contract)? Yes, status_pass=true. |
| `chrono_mini_discrepancy.py` | `experiments/feasibility_audit/chrono_mini_discrepancy.csv`; `runs/feasibility_audit/chrono_mini_discrepancy_summary.json` | `docs/feasibility-route-hf-backend-2026-06.md` | 23-row mini panel: which current-sim outcomes survive Chrono::Vehicle dynamics, before paying for the full HF4 run? |
| `chrono_hf4_full_discrepancy.py` | `experiments/feasibility_audit/chrono_hf4_full_rows.csv`; `runs/feasibility_audit/chrono_hf4_full_summary.json`, `chrono_hf4_scenarios/` | `docs/feasibility-route-hf4-full-discrepancy-2026-06.md` | Full HF4: 256 same-scenario dual-backend rows. 249/256 identical; zero success->collision/offtrack flips; the 7-row ceiling holds under Chrono. |
| `s4_hf_lite_variant_selector_smoke.py` | `experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json` | `docs/m3219-s4-hf-lite-chrono-variant-selector-smoke.md` | Does the new Chrono vehicle selector preserve the default Sedan path and reset/step explicit BMW_E90/UAZBUS variants through obs72/action3? Yes; pricing preregistration admitted, pricing run still blocked. |

## 4. VoI series (task design: does knowing mu pay?)

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `voi_current_task_family.py` | `experiments/feasibility_audit/voi_current_task_family.json`; `runs/feasibility_audit/voi_current_task_family/skeleton_details.json` | `docs/capability-boundary-tracking-thesis-2026-06.md` (Section 1); cited in `docs/selfid-commitment-task-voi-design-2026-06.md` | Did the OLD task family ever make mu worth knowing? No: VoI(success)=0 on 24/24 scenario skeletons — the root cause of ~1500 null milestones. |
| `voi_commitment_task_design.py` | `experiments/feasibility_audit/voi_commitment_task_design.json`; `runs/feasibility_audit/voi_commitment_task_design/episode_rows.csv` | `docs/selfid-commitment-task-voi-design-2026-06.md` | Can a commitment task family be designed with VoI(success) >= 0.25? Yes: B2 family, validated VoI 0.5625. |
| `voi_commitment_adversarial_audit.py` | `experiments/feasibility_audit/voi_commitment_adversarial_audit.json`; `runs/feasibility_audit/voi_commitment_adversarial_audit/` | `docs/selfid-gate-protocol-v2-2026-06.md`; `docs/selfid-task-final-spec-2026-06.md` | Does the B2 design leak? Yes: any post-probe single frame regresses mu (R^2 ~ 0.975) — probes write mu into the speed register; motivated gate protocol v2. |
| `voi_conditional_prior.py` | `experiments/feasibility_audit/voi_conditional_prior.json`; `runs/feasibility_audit/voi_conditional_prior/episode_rows.csv` | `docs/selfid-conditional-voi-2026-06.md` | Do coarse side-channel priors (+/-0.2 mu) substitute for precise identification? No at loose windows (VoI hedged to ~0), and tight reveal windows (K2) restore VoI 0.29-0.39: precision pays where windows are tight. |
| `selfid_task_health_check.py` | `experiments/feasibility_audit/selfid_task_health_check.json` | `docs/selfid-commitment-task-voi-design-2026-06.md` (health-check input) | Is the commitment task trainable at all (reward sanity, PPO short-run health) before spending gate budget? |
| `selfid_task_final_spec.py` | `experiments/feasibility_audit/selfid_task_final_spec.json`; `runs/feasibility_audit/selfid_task_final_spec/` | `docs/selfid-task-final-spec-2026-06.md`; `docs/selfid-gate-protocol-v2-2026-06.md` | What is the frozen B2K2_final spec (reveal 9.5 m, jitter, rewards 40/60) and its acceptance table after 3 fix iterations? |

## 5. G1 series (learnability ignition gates)

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `selfid_gate_pipeline_check.py` | `experiments/feasibility_audit/selfid_gate_pipeline_check.json` | `docs/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate.md` | Is the observation-degradation wrapper actually mounted on every train/eval/gate entry point? Pre-M3214: no (4 bare-env call sites found); M3214 ships the integration. |
| `selfid_g1_ignition_gate.py` | `runs/feasibility_audit/selfid_g1_ignition_gate/summary.json` | `docs/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate.md` | Minutes-scale RL ignition gate: does the delay-25 condition produce a seed-paired outcome difference vs wrapped-clean? Verdict FAIL (variance bed) — cancelled the 20-cell RL matrix. |
| `selfid_g1prime_ignition_gate.py` | `experiments/feasibility_audit/selfid_g1prime_preregistration.json`, `selfid_g1prime_summary.json`; `runs/feasibility_audit/selfid_g1prime/full/` | `docs/selfid-g1prime-ignition-gate-2026-06.md` | Supervised (minutes-scale) probe->commit gate: can a history learner beat single-frame? Verdict FAIL_TEACHER_TASK_REWORK (BC compounding + speed-register leak). |
| `selfid_deployable_probe_protocol.py` | pre-registered outputs `experiments/feasibility_audit/selfid_deployable_probe_{preregistration,tradeoff}.json` (full mode never run; smoke only at `runs/feasibility_audit/selfid_deployable_probe/smoke/`) | none (G1' rework stage 1, superseded by the threshold-seeking paradigm before the full run) | Could a deployable steering micro-excitation replace the leaking brake probe? Designed + pre-registered; superseded when embedded identification (measurement A/B) removed the need for a separate probe phase. |
| `selfid_positive_control_pilot.py` | `runs/selfid_positive_control_pilot_smoke/` smoke-chain artifacts (default `--output-dir runs/selfid_positive_control_pilot` unused; no experiments/ JSON; numbers non-scientific by design) | `docs/selfid-completion-experiment-design-2026-06.md` | Does the privileged positive-control twin (obs76) pass end-to-end through train -> hidden-swap gate, proving the gate machinery can detect a real signal? |

## 6. Regime measurements (A/B/C + degraded final)

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `slip_onset_detectability.py` (A) | `experiments/feasibility_audit/slip_onset_detectability.json`; `runs/feasibility_audit/slip_onset_detectability/episodes.csv`, `traces/` | `docs/selfid-threshold-seeking-onset-2026-06.md` | Is incipient slip detectable from obs72 alone, and how deep is the resulting overshoot? Yes: 140-400 ms latency at task-relevant ramps, zero false positives; identifies the combined capability, not mu. |
| `ramp_policy_voi_regime.py` (B) | `experiments/feasibility_audit/ramp_policy_voi_regime.json`; `runs/feasibility_audit/ramp_policy_voi_regime/episode_rows.csv` | `docs/selfid-threshold-seeking-regime-2026-06.md` | Where does a mu belief beat a belief-free threshold-seeker under CLEAN sensing? Nowhere: VoI(belief)=0.000 at every reveal window 9.5-30 m (11,280 episodes). |
| `reflex_overshoot_recovery.py` (C) | `experiments/feasibility_audit/reflex_overshoot_recovery.json`; `runs/feasibility_audit/reflex_overshoot_recovery/episodes.csv` | `docs/selfid-reflex-recovery-budget-2026-06.md` | How deep an overshoot can the reflex layer recover (the belief layer's safety budget)? v4 saves 92.6%; boundary unbroken to 150% for mu>=0.45; v4-vs-v5 pairing: v4_only 26/28, v5_only 0. |
| `degraded_regime_final.py` | `experiments/feasibility_audit/degraded_regime_final.json`; `runs/feasibility_audit/degraded_regime_final/episode_rows.csv`, `latency_rows.csv` | `docs/selfid-degraded-regime-final-2026-06.md` | Does belief value re-emerge under delayed/noisy ego observation? Yes: VoI revives in 12/14 cells (0.17-0.88), all 7 tightest-window cells — the two-regime law (23,040 episodes). |

## 7. Belief decomposition

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `belief_decomposition.py` | `experiments/feasibility_audit/belief_decomposition.json`; `runs/feasibility_audit/belief_decomposition/episode_rows.csv` | `docs/selfid-belief-decomposition-2026-06.md` | Vehicle knowledge vs road knowledge: which carries the degraded-regime prize? The road (mu) component ~ equals the whole prize; the vehicle share is <= 0.19, recoverable for free by 5 s sub-limit familiarization; sub-limit driving is structurally mu-blind. |

## 8. Phase-2 WP0/WP1 measurements

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `family2_design.py` | `experiments/feasibility_audit/family2_spec.json`, `family2_prereg.json`, `family2_prereg_repair1.json`; `runs/feasibility_audit/family2_design/episode_rows*.csv` | `docs/selfid-family2-design-2026-06.md`; summarized by `docs/m3215-wp0-degraded-sweep-bridge-validation.md` | What is the frozen second task family for C1? F2C1 offset/gap-choice geometry, accepted after one pre-registered repair and used by M3215. |
| `wp0_degraded_sweep.py` | `experiments/feasibility_audit/wp0_degraded_sweep_prereg.json`; `runs/feasibility_audit/wp0_degraded_sweep/summary.json`, `progress.jsonl` | `docs/m3215-wp0-degraded-sweep-bridge-validation.md` | Does the two-regime law replicate on family #2 and do richer degradation models follow the noise-buys-delay bridge? G-A FAIL: law scopes family-specific; bridge falsified. |
| `wp1_data_pipeline.py` | `runs/feasibility_audit/wp1_dataset_quick/summary.json`; `runs/feasibility_audit/wp1_construction_pilot/pilot.json`; `experiments/feasibility_audit/wp1_seed_streams.json` | `docs/m3216-wp1-modular-belief-experiment.md` | Infrastructure: builds leak-gated WP1 prefix/dataset artifacts with frozen seed-stream discipline for the modular-belief substitution experiment. |
| `wp1_estimator_trainer.py` | `runs/feasibility_audit/wp1_estimator_quick/summary.json`; estimator checkpoints under `runs/feasibility_audit/wp1_estimator_quick/` | `docs/m3216-wp1-modular-belief-experiment.md` | Infrastructure: trains/evaluates the L0/L2/L3 supervised mu estimators used by the WP1 full runner. |
| `wp1_full_run.py` | `experiments/feasibility_audit/wp1_prereg.json`; `runs/feasibility_audit/wp1_full/summary.json`, `progress.jsonl`; archived leak stop in `runs/feasibility_audit/wp1_full_leakstop1/` | `docs/m3216-wp1-modular-belief-experiment.md` | Does the primary L3_GRU estimator recapture the matched degraded-regime prize through modular substitution? Primary FAIL 0/4 cells; estimator-level belief signal is positive but substitution does not clear G-B. |
| `wp1_iter1_full_run.py` | `experiments/feasibility_audit/wp1_iter1_prereg.json`; `runs/feasibility_audit/wp1_iter1_full/summary.json`, `progress.jsonl` | `docs/m3217-wp1-belief-substitution-bounded-iteration.md` | Does the single authorized bounded iteration rescue WP1? Terminal FAIL at the mixed-data leak gate; C2 bound accepted and WP2 stays closed. |

## 9. C5 / WP-RL pricing

| script | artifacts | conclusion doc | answers |
|---|---|---|---|
| `c5_reflex_degradation.py` | `experiments/feasibility_audit/c5_prereg.json`, `c5_reflex_degradation.json`; `experiments/feasibility_audit/c5_lateral_prereg.json`, `c5_lateral_spread_rider.json`; `experiments/feasibility_audit/c5prime_prereg.json`, `c5prime_target_consolidation.json`; `runs/feasibility_audit/c5_reflex_degradation/episode_rows.csv`; `runs/feasibility_audit/c5_lateral_spread_rider/episode_rows.csv`; `runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv` | `docs/c5-reflex-degradation-2026-06.md`; `docs/m3220-a1-s4-lateral-spread-rider-pricing.md`; `docs/m3222-a3-c5prime-target-consolidation.md` | Does passenger-car spread open a priced gap for RL over fixed reflex and classical kappa-RLS retuning, and does the C5-prime structural ceiling target survive fresh-seed consolidation? Original S0-S3 spread formulation rejected 0/8 cells; A1 cg/Iz lateral rider also rejected 0/4 cells; A3 confirmed the C5-prime target 3/4 T-limit cells, with Track C still blocked on CP-1. |
| `obs_normalization_audit.py` | `experiments/feasibility_audit/obs_normalization_prereg.json`, `obs_normalization_audit.json`; `runs/feasibility_audit/obs_normalization_audit/channel_stats.csv`, `episode_summary.csv` | `docs/m3221-a2-obs-normalization-audit.md` | Are canonical obs72 normalization constants population/high-speed ready? No: road_y/20, high-speed ego speed/accel, and obstacle rel-vy/12 saturate; population/high-speed training remains blocked on a follow-up normalization/preview implementation. |
| `s4_hf_lite_backend_inventory.py` | `experiments/feasibility_audit/s4_hf_lite_backend_inventory.json` | `docs/m3218-s4-hf-lite-backend-inventory-preflight.md` | At M3218, could S4-HF-lite passenger-car-population pricing run on the then-current Chrono backend wiring? No: Chrono resources supported extension, but repo wiring had no vehicle/tire variant selector; routed to M3219 variant-selector smoke before pricing. |

## Artifacts without a script in this directory

- `experiments/feasibility_audit/selfid_matrix_cost_estimate.json` — manual
  throughput/cost audit (pre-launch design audit of the since-cancelled
  20-cell RL matrix); its throughput numbers (16 concurrent jobs ~12.9k
  env steps/s, CUDA 2.6x slower) are cited in the Phase-2 plan, Section 1.4.
  Raw job logs: `runs/feasibility_audit/selfid_cost/`.
- `runs/feasibility_audit/summarize_results.py` — ad-hoc result summarizer
  kept with the run artifacts, not a measurement.
