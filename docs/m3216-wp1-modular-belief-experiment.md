# M3216 WP1 Modular Belief Experiment (Phase-2 C2+C3 learning gate, G-B adjudication)

Status: completed (harness run
`runs/research/m3216-wp1-modular-belief-experiment_20260611T135504Z`,
returncode 0, 47.6 min, 16 workers). Manual-takeover mixed bookkeeping:
registered and executed as a formal harness milestone per the Phase-2 plan
(`docs/research-plan-phase2-capability-boundary-tracking.md` WP1, Section 0).
Branch `phase2_wp1_belief`; auxiliary measurement; the engineering incumbent
and `ActiveSafetyReflexDriver` are unchanged.

`self_id_evidence_discipline.claim_level`: `not_applicable`.

## 1. What was measured

Pre-registration (frozen before the `--full` run, echoed into `summary.json`):
`experiments/feasibility_audit/wp1_prereg.json`. Routing basis: M3215 G-A fail
-> WP1 on **family #1 only**; eligible cells frozen by the M3215 hardened
matched panel = {delay5, delay12, delay25, noise0.05}.

- Construction (stage-2 freeze of the handover design stage 1 deferred):
  prefix-carrying B2K2_final (5 s sub-limit familiarization prefix + vehicle
  RLS fixture, vehicle randomization OFF = the M3215 measurement condition);
  obstacle prefix offset re-frozen at **40 m = the measured nominal prefix
  travel (39.85 m, mu/seed-invariant)** replacing the stage-1 60 m value
  (measured defect: ~20 m of unmodeled offset at handover made every
  v-target-law arm, oracle included, decelerate prematurely and time out);
  standard deadline = 250 + 0 + 285 steps (allowance 0 from the declared
  pilot grid {0,25,50}: delay5 sel oracle 0.958, prize +0.167; 25/50 inflate
  the floor to 0.917/0.833 and collapse the prize); C3 handover at the reveal
  with per-episode deadline = scripted-probe reveal tick + 110 steps (pilot
  grid {90..150}: budget 110 maximizes the delay5 sel prize +0.583 at oracle
  0.917). Pilot (subst_sel stream only, all grid points reported):
  `runs/feasibility_audit/wp1_construction_pilot/pilot.json`.
- Arms per cell on **identical 240-episode validation sets** (12 mu x 20
  disjoint subst_val seeds, episode-paired): floor = max(best-sel seeker over
  the M3215 per-cell tau grid x 24-48 configs, best-sel fixed plan of 11),
  matched per-mu oracle (per-point dv from subst_sel), and 5 estimator arms
  (L0_frame, L2_window_25/50/100, L3_GRU) x 8 training seeds injected at the
  decision tick into the cell's best-sel seeker config (zero eval-time
  estimator freedom).
- Pre-registered primary: **L3_GRU recaptures >= 50% of the re-measured
  matched prize in >= 3 of 4 cells**, each with the one-sided 97.5% lower
  bound of the episode-paired (arm - floor) difference > 0 under the frozen
  two-way (episode + training-seed cluster) SE. All other arms exploratory.
- C3 conditional readout (FIR vs IIR, M1182): L3 vs L2_100 on the
  excitation-gap variant, reported only if a history arm clears the C3
  floor; floor = best of {no-belief, constant-mu 0.45/0.70/0.95} handover.
- L4 class-prior block: exploratory only (vehicle randomization ON, delay5).
- Volume: 1,948 dataset episodes (487/cell) + 320 supervised training runs
  (5 arms x 8 seeds x 4 cells x 2 variants; capacity non-input-projection
  spread 0.24%, compute-matched 200 epochs x LR grid on the sel split) +
  ~4,300 selection + 82,032 validation/C3/L4 episodes; 686 resume units in
  `progress.jsonl`.

## 2. Leak-gate stop and the single pre-authorized data iteration — MEASURED

The first `--full` attempt **stopped at the pre-registered dataset leak
gate** (archived: `runs/feasibility_audit/wp1_full_leakstop1/summary.json`):
decision-frame single-frame->mu out-of-fold R^2 on the standard subset =
delay5 0.125/0.142 (linear/MLP), delay12 0.300/0.250, delay25 0.253/0.082 —
above the 0.1 bar; noise0.05 and all C3 subsets passed. Mechanism (measured
on the stopped run): decision tick ~ d(mu) (Spearman 0.93) x the
constant-speed-target convergence transient left a mu signature in the
longitudinal actuator/command channels (obs 8/11/3/7; top Spearman -0.44 on
the brake actuator state). The single pre-authorized bounded data iteration
applied the longitudinal mirror of the stage-1 lateral-dither repair: a
seed-derived mu-free **multi-sine speed schedule** (base U(6.0,8.5), 3
sinusoids, amp U(1.0,2.25) m/s) replacing constant tracking targets in the
standard behaviors (C3 untouched). Re-run gate results (all PASS):

| cell | linear OOF R^2 | MLP OOF R^2 | C3 subset (lin/MLP) | C3 telemetry |
|---|---|---|---|---|
| delay5 | -0.111 | -0.865 | -0.048 / -0.404 | PASS |
| delay12 | -0.002 | -0.091 | -0.047 / -0.754 | PASS |
| delay25 | +0.042 | -0.137 | -0.216 / -0.115 | PASS |
| noise0.05 | -0.143 | -0.512 | -0.096 / -0.595 | PASS |

Honest fixture residual: per-cell max truth-frame prefix utilization over
487 episodes = 0.525 / 0.614 / 1.020 / 0.633 (delay5/12/25/noise) — rare
single-episode tail events above the stage-1 < 0.5 bulk claim (delayed/noisy
closed-loop steering x low mu spikes lateral utilization). These are genuine
physical contact events, not probe artifacts; the decision-frame gate (the
pre-registered criterion) passed regardless. Prefix RLS kappa_b median 1.000
in delay cells; 0.534 under noise 0.05 (the known EIV attenuation pathology,
consumed by nothing here since vehicle randomization is OFF in gated blocks).

## 3. Estimator-level result (dataset validation split) — MEASURED, not gated

Val MAE (mean over 8 seeds), standard variant:

| cell | L0 | L2_25 | L2_50 | L2_100 | **L3_GRU** | L3 R^2 | L3 off-grid MAE | L3 reset-control MAE |
|---|---|---|---|---|---|---|---|---|
| delay5 | 0.218 | 0.217 | 0.201 | 0.163 | **0.045** | 0.909 | 0.040 | 0.293 |
| delay12 | 0.241 | 0.243 | 0.244 | 0.226 | **0.025** | 0.984 | 0.023 | 0.246 |
| delay25 | 0.214 | 0.209 | 0.194 | 0.161 | **0.021** | 0.988 | 0.024 | 0.233 |
| noise0.05 | 0.221 | 0.201 | 0.199 | 0.184 | **0.142** | 0.335 | 0.158 | 0.238 |

The mu signal is learnable and strongly architecture-dependent ON the
training distribution: the GRU reaches R^2 0.91-0.99 in the delay cells
(off-grid mu equally good — no grid memorization), the equal-capacity window
arms stay near predict-the-mean, and truncating the GRU state to 25 frames
(reset control) destroys the estimate (MAE 0.23-0.29) — the information is
genuinely history-borne. C3-variant training found NO signal in any arm
(MAE 0.237-0.262 = predict-mean): 128 train episodes with the excitation
~800 frames before the label-relevant tick did not train through.

## 4. Substitution validation (the gated readout) — MEASURED

Per-cell, 240 paired episodes/arm; floor/oracle re-measured on the same
episodes; injected arms = mean over 8 training seeds; lo97.5 = one-sided
97.5% lower bound (two-way SE); recapture = Delta / prize.

| cell | floor (arm) | oracle | prize [Newcombe95] (M3215 ref) | L3_GRU succ | L3 Delta vs floor | L3 lo97.5 | L3 recapture | cell PASS |
|---|---|---|---|---|---|---|---|---|
| delay5 | 0.675 seeker_r20000_w1_t0.08_d0.15_v+0.75 | 0.892 | **+0.217** [0.144,0.287] (0.333) | 0.535 | -0.140 | -0.227 | -0.65 | FAIL |
| delay12 | 0.413 seeker_r20000_w1_t0.08_d0.06_v+0.75 | 0.896 | **+0.483** [0.406,0.552] (0.458) | 0.597 | **+0.185** | **+0.110** | **0.38** | FAIL (recapture < 0.5) |
| delay25 | 0.350 fixed_v9.5 | 0.483 | **+0.133** [0.045,0.219] (0.183) | 0.181 | -0.169 | -0.285 | -1.27 | FAIL |
| noise0.05 | 0.371 fixed_v9.5 | 0.488 | **+0.117** [0.028,0.203] (0.150) | 0.133 | -0.238 | -0.322 | -2.04 | FAIL |

Exploratory arms (Delta vs floor, lo97.5): L0 / L2_25 / L2_50 / L2_100 are
negative everywhere except delay12 (L0 +0.012 [-0.024], L2_25 +0.060
[+0.029], L2_50 +0.052 [+0.022], L2_100 -0.083) — no exploratory arm passes
any cell. Pooled fractions (descriptive): L3 -0.38, others -0.71..-0.89.
Injection fired in 99.6-100% of episodes. **The construction is valid: all
four re-measured prizes are positive with CIs excluding 0** (0.117-0.483,
direction consistent with the M3215 references).

**Primary verdict: FAIL (0 of 4 cells; bar = 3).** L0 leak route not
triggered (0 cells). Frozen route applied:
`all_arms_fail_one_bounded_iteration_then_accept_bound`.

The interpretable structure behind the FAIL (substitution-time mu error vs
dataset-val MAE, L3_GRU): 0.157 vs 0.045 (delay5), 0.137 vs 0.025 (delay12),
0.263 vs 0.021 (delay25), 0.251 vs 0.142 (noise). The estimator that is
near-perfect on the mu-decoupled training behaviors degrades 3-10x when
watching the seeker's own closed-loop approach (whose ramp STOPS at the
detector onset — a trajectory family never seen in training), and the
reveal-tick override then replaces the seeker's internal detector estimate —
at delay5 a competent one (floor 0.675) — with the worse learned one. Only
at delay12, where the internal detector is weakest relative to the prize,
does the learned belief produce a real, CI-excluding-zero gain (+0.185,
38% of the prize, p<0.025 one-sided).

## 5. C3 readout (FIR vs IIR, M1182) — MEASURED: condition not met

C3 floors selected the **constant-mu handover** everywhere (const0.7 x3,
const0.95 in noise): floor 0.879/0.892/0.879/0.679 vs oracle
0.846/0.838/0.842/0.633 — the "prize" of TRUE mu over the best belief-free
arm at a pure-reaction handover is **negative in all four cells**
(-0.033..-0.054): with the deadline budget fixed and the approach scripted,
assuming mu=0.7 at the reveal does everything knowing mu does. On top of
that, the C3-trained estimators are flat (Section 3), so the injected arms
coincide with the const-prior floor (paired Delta exactly 0.000 in the delay
cells). No history arm clears the floor in any cell -> the pre-registered
condition fails and the L3-vs-L2_100 comparison is **not reported**
(verdict `not_reported_no_history_arm_clears_floor` x4). M1182 remains
unresolved on this testbed; the C3 *construction* result — the reaction-only
belief prize is captured by a coarse constant prior — is itself a finding
consistent with the plan's "coarse +/-0.2 priors do not substitute" applying
to the *approach commitment*, not to the post-reveal reaction.

## 6. L4 exploratory block (NOT gated) — MEASURED, descriptive

Vehicle-randomized delay5, 12 mu x 6 seeds = 72 episodes/arm, prefix-RLS
kappa belief feeding the cell's best floor seeker:

| arm | success [Wilson95] | kappa_b / kappa_d abs err (median) |
|---|---|---|
| nominal (kappa=1) | 0.250 [0.164,0.361] | 0.097 / 0.089 |
| RLS 1 s, uniform prior | 0.250 [0.164,0.361] | 0.097 / 0.089 |
| RLS 1 s, class prior (0.15 bins) | 0.556 [0.441,0.665] | 0.041 / 0.043 |
| RLS 5 s, uniform prior | 0.625 [0.510,0.728] | 0.008 / 0.018 |
| RLS 5 s, class prior | 0.639 [0.524,0.740] | 0.025 / 0.012 |
| truth kappa (ceiling) | 0.611 [0.496,0.715] | 0 / 0 |

Direction (descriptive, n=72): 5 s of prefix RLS recovers the full vehicle
share (0.625 ~ truth 0.611); 1 s alone recovers nothing; a coarse class
prior lets 1 s recover most of it (0.556) — supporting the plan's "a class
prior can at most shorten the prefix" scoping of L4.

## 7. Verdicts and G-B routing (pre-registered rules applied as written)

1. **Primary (C2 substitution): FAIL, 0/4 cells.** Route =
   `all_arms_fail_one_bounded_iteration_then_accept_bound`: ONE bounded
   excitation/representation iteration (<= 1 week, <= 4 h CPU) is available
   before the bound is accepted as the result; WP2 does not open on this
   verdict. The measured structure scopes the iteration: close the
   behavior-policy gap (estimator data from seeker-generated approaches
   and/or continuous injection instead of the reveal-tick-only override) —
   the delay12 result (+0.185, CI excluding 0, 38% recapture) shows the
   substitution channel works in the cell where the internal detector is
   weakest.
2. **Estimator-level C2 (not the gated claim): strongly positive** — the
   history-borne mu signal is learnable to R^2 0.91-0.99 under pure delay by
   the recurrent arm only, with the reset control confirming history
   dependence. This is the first measured separation of estimator
   learnability from substitution value on this testbed.
3. **C3/M1182: not adjudicated** (condition not met); the constant-prior
   floor capturing the reaction-only prize is reported as a C3-construction
   finding.
4. **L0 leak audit: not triggered.**
5. Dataset leak gate: one pre-authorized iteration consumed (longitudinal
   multi-sine repair), gates pass on the measurement dataset.

## 8. Claim boundary

Allowed: pre-registered feasibility-audit substitution-measurement outcomes
(recapture fractions, paired CIs, the C3 non-qualification, exploratory L4
descriptives) on the scripted B2K2 prefix-carrying construction, and the
G-B adjudication exactly as pre-registered. Rejected (explicit): any
driver-performance, current-sim verdict, high-fidelity, full-driver,
repair-success, robustness-result, feasibility-proof, validation/ranking/
promotion, paper-result, or self-ID capability claim; any reading of
seeker/oracle/estimator configurations as deployable drivers.

## 9. Artifacts

- `runs/feasibility_audit/wp1_full/summary.json` (prereg echo, all tables,
  verdicts; status completed) + `progress.jsonl` (686 resume units) +
  `rows/` (82,032 validation/C3/L4 episode rows) + `models/` (320 .pt)
- `runs/feasibility_audit/wp1_full_leakstop1/summary.json` (archived
  pre-registered leak-gate stop, iteration 1)
- `runs/feasibility_audit/wp1_construction_pilot/pilot.json` (construction
  pilot, subst_sel only, all grid points)
- `experiments/feasibility_audit/wp1_prereg.json` (frozen criteria),
  `experiments/feasibility_audit/wp1_seed_streams.json` (stage-1 streams)
- `scripts/feasibility_audit/wp1_full_run.py` (orchestrator; `--pilot` /
  `--quick` / `--full`), `wp1_data_pipeline.py` (+ multi-sine repair),
  `wp1_estimator_trainer.py`
- harness record: `runs/research/m3216-wp1-modular-belief-experiment_20260611T135504Z/command.log`
- review: `docs/reviews/m3216-wp1-modular-belief-experiment.md`
