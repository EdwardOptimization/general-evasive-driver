# Current Status

This file is the compact official state for the project. Milestone documents
and `docs/research-log.md` remain the detailed log of the autonomous-harness
era; the Phase-2 plan and thesis (pointer table below) define the active
program. Last full refresh: 2026-06-12 (the 2026-06-11 WP6.3 refresh
replaced the stale paper-route state; this update folds in M3215-M3242,
the C5 pricing disposition, the S4-HF-lite backend connector/pricing work,
WP6.2 guardrails, the A1 lateral-channel rider, the A2 obs-normalization
audit, the A3 C5-prime target consolidation, B1/B2/B3/B4 env-engineering
smokes, D1 Chrono pricing, the first C1 warm-start failure/localization, the
D1b Chrono-native oracle protocol smoke plus full direction-pricing panel,
the C1 v2 tail-balanced quick-smoke negative, the M3233 C1
synthesis/repricing pivot, M3234 C1 admission-interface pricing, M3235 C1
tail-family interface smoke, the M3236 tail-family interface pretrain quick
negative, the M3237 C1 interface synthesis/repricing pivot, and the M3238
C1 family-selector repricing negative, the M3239 B1b moving-obstacle
pricing protocol smoke, the M3240 full B1b moving-obstacle pricing
negative, the M3241 B2b high-speed pricing protocol smoke, and the M3242
full B2b high-speed pricing negative).

## Project Identity

- Repository: `general-evasive-driver`
- Python package: `autodrift`
- Working title: General Evasive Driver
- Core direction (Phase-2): capability-boundary tracking — when and how a
  driving policy at the handling limit needs a belief about its own
  capability envelope, on top of a certified reflex safety layer
  (the two-regime law).

## Project State: manual-takeover Phase-2

History in one paragraph: the autonomous harness loop ran through M3214
before manual takeover; the manual takeover has since registered
M3215-M3242. `experiments/research_status.json` now records
3244 completed / 7 failed / 2 blocked task entries, with `next_task:
null`. On
2026-06-11 an independent feasibility audit showed the M3108–M3212
residual-repair branch was repairing physically unsolvable rows, and the
session was taken over manually (M3213 blocked;
`docs/feasibility-takeover-2026-06-route-decision.md`). The takeover route
then certified the reflex layer at the physical ceiling: oracle
certification measured all 7 residual hard-safety rows unrepairable by any
controller, causal or privileged (43,372 privileged rollouts, 7/7 hard-fail
in both tiers, `docs/feasibility-audit-oracle-certification-2026-06.md`);
feasible-row success is 55/55 on the fixed panel and 162/165 = 98.2% pooled
aeb_feasible with 0 collisions on all 172 feasible fresh-seed episodes
(`docs/feasibility-audit-stratified-panel-2026-06.md`); the HF4 dual-backend
measurement found 249/256 identical outcomes under Chrono::Vehicle with zero
new hard-safety failures
(`docs/feasibility-route-hf4-full-discrepancy-2026-06.md`). The ~1500-
milestone self-ID question was reformulated as capability-boundary tracking
(`docs/capability-boundary-tracking-thesis-2026-06.md`) and measured to the
**two-regime law**: under clean sensing, VoI(belief) = 0.000 at every reveal
window 9.5–30 m — a belief-free threshold-seeker matches the per-mu oracle;
under degraded sensing (delay/noise on the ego channels), belief value
revives to 0.17–0.88 in 12/14 cells (11/14 against the best belief-free
arm). Phase-2 (`docs/research-plan-phase2-capability-boundary-tracking.md`,
v2) started 2026-06-11 to test the law's generality (C1), belief
learnability (C2), FIR-vs-IIR (C3), and the deployable
belief→verifier→reflex stack (C4).

## Program Progress Ledger (refresh 2026-06-12)

Claims:

| claim | status | verdict artifact |
|---|---|---|
| C1 generality of the two-regime law | **family-specific scope** (G-A FAIL per pre-registration): family #2 replicates the clean half (VoI +0.025) but its degraded revival is mode-dependent — noise-type degradation revives belief everywhere, delay-type stays ~0 because the drive-ramp seeker identifies ~1 s before commitment. The noise-buys-delay bridge was falsified on its pre-registered double criterion. | `docs/m3215-wp0-degraded-sweep-bridge-validation.md` |
| C2 belief learnability | **terminal bound accepted** (G-B FAIL, the single authorized iteration consumed): belief is learnable — the project's first working history-borne capability estimator (GRU R^2 0.91-0.99, reset-control-destroyed, window arms at predict-the-mean) — but not monetizable through the substitution interface; the bounded iteration was stopped by the leak gate because on-policy closed-loop data is necessarily single-frame mu-readable (the thesis Section-10 capstone). delay12 +0.185 (lower bound +0.110) remains the only substitution-level positive. | `docs/m3216-wp1-modular-belief-experiment.md`, `docs/m3217-wp1-belief-substitution-bounded-iteration.md` |
| C3 FIR vs IIR | **not adjudicated** (pre-registered condition not triggered: no history arm cleared the floor) | M3216 doc |
| C4 deployable stack | **closed** (WP2 never opened per G-B) | plan Section 2 |
| C5 one policy for all passenger cars (RL as engineering) | **spread formulation rejected by pricing**. S0-S3 mass/brake/drive/tau spread failed its pre-registered bar (0/8 cells): the fixed reflex's degradation curve was flat, per-instance grid tuning had nothing to buy, and kappa-RLS retuning self-harmed at corners. M3220 then gave the final cheap current-sim lateral-channel rider (cg/Iz S4L): 0/4 cells qualified; S4L/T-limit prize was only +0.007 with CI95 [-0.014, 0.028]. **Measured current-sim survivor (C5' candidate): the reflex structural ceiling gap. M3222 fresh-seed A3 consolidation confirmed the C5-prime target by the frozen rule: 3/4 T-limit cells qualified with oracle - per-tuned gaps +0.1597 to +0.2153 and CI lower bounds > 0; S0 was positive but below the +0.15 effect-size bar (+0.1389).** M3218/M3219 completed the Chrono connector inventory + selector smoke. M3227 then ran the preregistered S4-HF-lite multi-vehicle direction-pricing proxy on frozen A3 structured-gap rows and found the direction **reversed in all three Chrono variants**: structured current-sim oracle-tail replay underperformed `v4_pertuned` on Sedan, BMW_E90, and UAZBUS. CP-1 then conditionally opened C1, but M3228's first structured-oracle demo + MLP BC warm-start failed its frozen full gate (validation action MSE 0.234184 vs <=0.12); M3229 localized the failure to selection/validation tail-action generalization. M3232 then tried the revised v2 rare-tail-balanced quick smoke and failed the same frozen action-MSE gate (0.291470 vs <=0.12), despite demo replay/checkpoint/dataset success. M3230 completed the D1b Chrono-native oracle protocol smoke, and M3231 completed the full native Chrono direction-pricing panel: native_oracle beat same-row `v4_pertuned` in both preregistered variants (Sedan +0.2222, BMW_E90 +0.1111), satisfying the CP-2 D1b direction-positive precondition. M3233 synthesized the evidence: A3/D1b keep the C5-prime target priced, but the local direct-MLP/action-MSE warm-start branch pivots after two gate failures. M3234 then priced the successor admission interface positive: structured tail-family oracle anchor removes 0.369957 validation tail MSE vs the 0.15 threshold, and v2 held-out family train coverage is 1.0. M3235 ran the no-PPO tail-family interface smoke and passed all frozen gates: 11/11 demo replays succeeded, held-out family train coverage was 1.0, tail reconstruction MSE/max error were 0, 831 tail frames were encoded, and no policy checkpoint was written. M3236 then tested the first supervised interface pretrain quick on the full v2 split plus rare-tail support: 43/43 demos replayed and aggregate validation accuracy beat simple floors (0.766082 vs 0.538012), but `structured:coast_steer_-0.7` failed 0/101 validation frames and predicted-family reconstruction MSE was 0.276010 vs <=0.1. M3237 synthesized the evidence: target pricing and exact representation remain alive, but local frame-wise interface pretraining is closed; aggregate validation accuracy is unsafe because it masked a complete rare-family collapse. M3238 then priced the local family-selector route negative: the best train-only row selector reached validation accuracy 0.803119 over the 0.538012 majority floor, but predicted-family reconstruction MSE was 0.268415 vs <=0.1 and `structured:coast_steer_-0.7` stayed 0/101, predicted as `structured:brake_steer_-1.0`. C1 local selector/interface training is blocked pending PI or a new nonlocal-interface pricing route. C2 is not admitted. C3 remains blocked on C2 plus PI CP-2. | `docs/c5-reflex-degradation-2026-06.md`, `docs/m3220-a1-s4-lateral-spread-rider-pricing.md`, `docs/m3222-a3-c5prime-target-consolidation.md`, `docs/m3219-s4-hf-lite-chrono-variant-selector-smoke.md`, `docs/m3227-d1-s4-hf-lite-chrono-pricing.md`, `docs/m3228-c1-c5prime-oracle-demo-bc-warmstart.md`, `docs/m3229-c1-bc-warmstart-failure-localization.md`, `docs/m3230-d1b-chrono-native-oracle-pricing-smoke.md`, `docs/m3231-d1b-chrono-native-oracle-pricing-full.md`, `docs/m3232-c1-v2-tail-balanced-warmstart-smoke.md`, `docs/m3233-c1-synthesis-repricing.md`, `docs/m3234-c1-admission-interface-pricing.md`, `docs/m3235-c1-tail-family-interface-smoke.md`, `docs/m3236-c1-tail-family-interface-pretrain-quick.md`, `docs/m3237-c1-tail-family-interface-synthesis-repricing.md`, `docs/m3238-c1-family-selector-repricing.md` |

Work packages: WP0 **complete** (wrapper modes M3215-validated, family #2
frozen with clean acceptance after one pre-registered repair, statistical
hardening, governance refresh); WP1 **terminal** (M3216/M3217); WP2/WP3
**closed by gates**; WP-RL S0-S3 spread pricing **completed / original C5
rejected**, A1 lateral-channel rider **completed / negative**, A3 C5-prime
target consolidation **completed / target confirmed; CP-1 conditionally approved**, S4-HF-lite
connector **completed / selector smoke passed**, D1 Chrono multi-vehicle
direction-pricing **completed / negative** (all three variants reversed for
structured current-sim oracle-tail replay), CP-1 **conditionally opened C1**,
C1 first warm-start attempt **failed** (M3228), M3229
**localized the failure** to selection/validation tail-action generalization,
M3232 v2 rare-tail-balanced quick smoke **failed** the unchanged action-MSE
gate (0.291470 vs <=0.12; demo replay/checkpoint/dataset succeeded),
M3233 C1 synthesis/repricing **completed / pivot** (C5-prime target still
priced, but local direct-MLP/action-MSE warm-start branch closed), M3234 C1
admission-interface pricing **completed / positive** (tail-family quick smoke
priced, no full training or C2 admission), M3235 C1 tail-family interface
smoke **completed / passed** (exact target reconstruction, no policy checkpoint),
M3236 C1 tail-family interface pretrain quick **failed** (rare-family collapse;
route to synthesis/repricing before more local pretraining), M3237 C1
tail-family interface synthesis/repricing **completed / pivot** (close local
frame-wise pretraining), M3238 C1 family-selector repricing **completed /
negative** (best row selector clears aggregate accuracy but fails rare-family
and reconstruction gates; local selector/interface training blocked pending PI
or new nonlocal-interface pricing), D1b
Chrono-native oracle protocol smoke **passed** (M3230), and D1b full
direction-pricing **completed / positive** (M3231: Sedan +0.2222,
BMW_E90 +0.1111; CP-2 D1b precondition satisfied);
A2 obs-normalization audit **completed / blocker found**
(`road_y/20`, high-speed ego speed/accel, and obstacle `rel_vy/12` require a
follow-up normalization/preview implementation before population or high-speed
training); B1 moving-obstacle env axis **completed / smoke passed** (flagged
constant-velocity crosser, dynamic labels, deterministic replay, legacy
zero-relvel preserved); B1b moving-obstacle pricing **completed / negative**
(M3239 passed the protocol smoke; M3240 full panel rejected the current
moving-crosser formulation with 0/4 cells qualifying, oracle-minus-pertuned
gap 0.0000 in every cell, oracle solvability 1.0, and fixed_star/v4_rls/
v4_pertuned all succeeding 32/32; all rows were `aeb_feasible`); B2
high-speed env axis **completed / smoke passed**
(explicit 36 m/s profile, selected-channel max abs 0.900, 2.5 s road preview,
high-speed labels 592/592; env-contract only, no training admission); B2b
high-speed pricing **completed / negative** (M3241 passed the protocol smoke;
M3242 full panel rejected the current high-speed formulation with 0/6 cells
qualifying, oracle solvability 1.0, oracle-minus-pertuned gap 0.125 in two
cells and 0.0000 in four cells, all paired CI95 lower bounds 0, and
scale-aware fixed_star/v4_pertuned succeeding 46/48 versus raw incumbent
42/48; weak high-speed pockets and scale-adapter transfer effects were
measured, but no priced type-(b) window-compression prize was admitted); B3
geometry-channel degradation **completed / smoke passed** (config-gated road
boundary plus active-obstacle continuous-channel noise, 16 episodes / 400
paired frames, ego/command and present/size/empty-slot channels unchanged,
deterministic replay 4/4; split-mu recorded as not expressible in the current
`DriftObstacleEnv` single-track outcome path); B4 minute-scale drive structure
**completed / smoke passed** (4 full seeds reached 3000 steps / 60.0 s,
warmup gate passed at steps 215-216, emergency obstacle appeared at step 250,
raw pass recorded at steps 991-999, minimum post-pass continuation 2001 steps,
deterministic replay 2/2; env-contract only, no controller outcome claim); WP4 spot
checks **partially updated**
(Chrono outcome coverage now includes D1 Sedan/BMW_E90/UAZBUS direction
pricing plus D1b Sedan/BMW_E90 native oracle direction-pricing, but not UAZBUS
D1b native search or continuous lateral/tire channel mapping); WP5 papers
**pending**
(scope fixed: family-scoped mode-dependent two-regime law + estimator
positive + the capstone bound; plus C5' only if PI accepts the structural
ceiling route); WP6 **current guardrails live** (6.0/6.1/6.2/6.3 done;
validator V7, escalation protocol, and managed-run helper are merged).

Harness ledger: M3215, M3216, M3217, M3218, M3219, M3220, M3221, M3222,
M3223, M3224, M3225, M3226, M3227, M3228, M3229, M3230, M3231, M3232, M3233, M3234, M3235, M3236, M3237, M3238, M3239, M3240, M3241, and M3242 registered and
executed through the harness (research-validate passed in pending state;
M3228 failed its full gate, M3229 completed, M3230 completed after a
same-turn rerun tightened the quick gate to require both structured and CEM
candidate coverage, M3231 completed after one infrastructure retry with
resume cleanup, M3232 failed the revised C1 v2 quick behavior gate, M3233
completed the C1 synthesis/repricing pivot, M3234 completed positive
admission-interface pricing, M3235 completed the no-PPO tail-family
interface smoke, M3236 failed the supervised tail-family pretrain quick,
M3237 completed the interface synthesis/repricing pivot, M3238 completed
the family-selector repricing negative, M3239 completed the B1b
moving-obstacle pricing protocol smoke, M3240 completed the full B1b
moving-obstacle pricing negative, M3241 completed the B2b high-speed pricing
protocol smoke, and M3242 completed the full B2b high-speed pricing negative);
leak gates stopped two dataset leaks and one terminal
iteration, all per pre-registration.

PI dispositions (2026-06-12): **v5 promotion is deferred — not a live
question while research is ongoing**; v4 stays deployed, v5 remains a
filed candidate, revisit at research completion
(`docs/v5-promotion-decision-packet-2026-06.md`). **C5 next decision**:
S0-S3 rejected the original spread formulation and M3220 rejected the cheap
current-sim cg/Iz lateral rider. M3222 confirmed the C5-prime
structural-ceiling target on a fresh-seed A3 panel. **CP-1 disposition
(PI, 2026-06-12, option 1): conditional approval** — C1 opens on the frozen
C5-prime target; D1b (Chrono-native oracle pricing, searched in-backend)
added as a CP-2 precondition after the M3227 tail-replay reversal
(price-before-train rule). M3223 completed B1 moving-obstacle env engineering as a smoke-only
axis: default static obstacles and zero-relvel contracts are preserved, while
the non-default constant-velocity crosser exposes dynamic labels and ego-mode
relative velocity. M3221 found an obs-normalization/preview blocker for any
population or high-speed training; M3224 implemented the non-default B2
high-speed profile and smoke-tested it at 36 m/s, closing that env-contract
blocker for the explicit profile only. M3225 completed B3 geometry-channel
degradation and split-mu expressibility: road/active-obstacle continuous
channels can now be degraded behind an explicit config gate, while current-sim
split-mu is a documented non-expression in the `DriftObstacleEnv` single-track
outcome path. M3226 completed B4 minute-scale drive structure: raw obstacle
pass is now distinct from pass-triggered truncation, and a 60 s same-episode
warmup -> emergency obstacle -> post-pass continuation smoke passed. M3227
completed D1 Chrono S4-HF-lite direction-pricing: 108 Chrono episodes over
Sedan/BMW_E90/UAZBUS, finite reset obs72 and variant matching passed, but the
structured-oracle-tail direction was reversed in all three variants. M3228
then executed the first C1 structured-oracle demo + BC warm-start: quick smoke
passed, but the full run failed the frozen validation action-MSE gate
(0.234184 vs <=0.12). M3229 localized the failure: validation prefix MSE was
0.026446, validation tail MSE was 0.369957, and brake-channel MSE dominated
at 0.201318. M3230 then implemented the D1b Chrono-native oracle pricing
protocol smoke: the accepted rerun took 276.6 s over two row-variant pairs,
with finite obs72 resets, variant matches, and structured plus CEM native
search on both `sedan_tmeasy` and `bmw_e90_tmeasy`. Quick mode was not a
direction-pricing verdict. M3231 completed the full D1b managed panel after
an infrastructure retry: the first attempt reached 14/18 row-variant pairs
before a Chrono worker IPC deadlock, the retry dropped 1 partial row and
completed the frozen panel. Final verdict: D1b direction-positive in both
preregistered variants, with native_oracle minus same-row `v4_pertuned`
+0.2222 on Sedan (9/9 vs 7/9) and +0.1111 on BMW_E90 (8/9 vs 7/9). C1
remains open pending a revised preregistered warm-start design; C2 remains
blocked on C1, and C3 remains blocked on C2 plus PI CP-2. The D1b
direction-positive precondition for CP-2 is satisfied.
M3232 then tested the next C1 revision: the v2 preregistration added distinct
rare coast-steer train support and validation probes while keeping the M3228
MSE gate unchanged. Quick mode replayed all demos and wrote checkpoint/dataset
artifacts, but failed validation action MSE at 0.291470 (zero-action baseline
0.559903, validation rollout context 2/3 success). M3233 then synthesized the
two C1 failures with A3/D1b pricing: the C5-prime structural target remains
priced, but the local direct-MLP/action-MSE warm-start branch pivots. M3234
then priced a structured tail-family admission interface positive: direct
tail MSE 0.369957 can be represented exactly by the structured family anchor,
and the M3232 v2 preregistration has 1.0 held-out-family train coverage. C1
remains open under `c5prime_track_c_c1_tail_family_interface_smoke`; do not
run full v2, full C1 training, or C2 from the failed direct-MLP artifacts.
M3235 then passed the no-PPO tail-family interface smoke: all 11 frozen demo
replays succeeded, held-out family train coverage was 1.0, tail reconstruction
was exact over 831 tail frames, and no policy checkpoint was written. C1 now
continues under `c5prime_track_c_c1_tail_family_interface_pretrain_design`;
C2 remains blocked.
M3236 then quick-smoked the supervised pretrain path using full v2 rows plus
extra rare-tail train support. The run replayed all 43 demos and trained an
interface head, but the frozen gates failed: aggregate validation accuracy
was 0.766082, yet `structured:coast_steer_-0.7` validation accuracy was 0/101
frames and predicted-family reconstruction MSE was 0.276010 vs the <=0.1 bar.
C1 now routes to `c5prime_track_c_c1_tail_family_interface_reprice`; do not
continue local interface pretraining or controlled rollout design without
synthesis/repricing.
M3237 completed that synthesis: the C5-prime target remains priced and the
structured representation remains exact if the family is known, but local
frame-wise pretraining is closed because the aggregate validation pass hid a
complete rare-family failure. C1 now routes to
`c5prime_track_c_c1_family_selector_repricing`; no further local pretraining,
controlled rollout design, full C1 training, or C2 work is admitted before a
read-only family-selector/separability repricing milestone.
M3238 completed that repricing and rejected the local family-selector route:
no deterministic train-only selector cleared all gates. The best row-level
selector reached validation accuracy 0.803119 over the 0.538012 majority
floor, but predicted-family reconstruction MSE was 0.268415 vs <=0.1 and
`structured:coast_steer_-0.7` stayed 0/101, predicted as
`structured:brake_steer_-1.0` with negative margin. C1 local selector/interface
training is now blocked pending PI or a new nonlocal-interface pricing route;
C2/C3 remain blocked.
M3239 then moved to the next independent roadmap unit, B1b moving-obstacle
pricing, but only as a quick protocol smoke. It passed all protocol gates in
3.4 s: two moving-obstacle cells, disjoint selection/validation streams,
fixed*/inert RLS/per-cell tuned/oracle arms, and reveal-constrained oracle
attempts on every validation row. M3240 then ran the full four-cell panel and
rejected the current B1b formulation: 0/4 cells qualified, oracle-minus-
pertuned gap was 0.0000 in every cell, oracle solvability was 1.0, and
fixed_star/v4_rls/v4_pertuned all succeeded 32/32. All rows were
`aeb_feasible`, so the moving-crosser axis as priced here does not create a
type-(b) timing/prediction prize. No moving-obstacle Track C extension,
C2 admission, training, or driver-performance claim is admitted.
M3241 then moved to B2b high-speed pricing as the next independent roadmap
unit, but only as a quick protocol smoke. It passed all protocol gates in
2.0 s: two high-speed cells, disjoint selection/validation streams, raw
incumbent plus scale-aware fixed*/inert RLS/per-cell tuned/oracle arms, and
reveal-constrained oracle attempts on every validation row. M3242 then ran
the full six-cell panel and rejected the current B2b formulation by the frozen
rule: 0/6 cells qualified, oracle solvability was 1.0, oracle-minus-pertuned
gap was 0.125 in `hs24_tight_mu055` and `hs36_tight_mu075` and 0.0000 in
the other four cells, and all paired CI95 lower bounds were 0. Scale-aware
fixed_star/v4_pertuned succeeded 46/48 versus raw incumbent 42/48, so the
panel shows weak high-speed pockets and a scale-adapter transfer effect but
no priced type-(b) window-compression prize. No high-speed Track C extension,
C2 admission, training, or driver-performance claim is admitted. With B1b and
B2b closed negative, the roadmap has no dependency-satisfied autonomous OPEN
unit unless PI reopens C1 or registers a new independent unit.

## Pointer Table

| object | path |
|---|---|
| Governing thesis (two-regime law: Section 8) | `docs/capability-boundary-tracking-thesis-2026-06.md` |
| Phase-2 plan v2 (active program definition) | `docs/research-plan-phase2-capability-boundary-tracking.md` |
| Takeover decision (why M3213 was blocked) | `docs/feasibility-takeover-2026-06-route-decision.md` |
| Gate protocol v2 (anchors before informative actions; R²≤0.1 self-check) | `docs/selfid-gate-protocol-v2-2026-06.md` |
| Latest harness milestone (M3242: B2b high-speed pricing full) | `docs/m3242-b2b-high-speed-pricing-full.md` |
| Thesis capstone + RL re-entry (Sections 10-11) | `docs/capability-boundary-tracking-thesis-2026-06.md` |
| Data coverage map (C5 sampling design authority) | `docs/data-coverage-map-2026-06.md` |
| Incumbent deployed driver (v4, untouched) | `src/autodrift/active_safety_reflex_driver.py`, `DRIVER_ID = active_safety_reflex_driver_m3105_incumbent_v4_no_regression` |
| v5 candidate (NOT promoted; decision pending with the PI) | `src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py` + `docs/v5-promotion-decision-packet-2026-06.md` |
| Measurement index (script → artifact → conclusion doc) | `scripts/feasibility_audit/README.md` |

## Hard Constraints (takeover discipline)

1. **The incumbent does not move.** `ActiveSafetyReflexDriver` (v4/M3105)
   stays the deployed driver; v5 remains a candidate until the promotion
   decision packet is adjudicated by the PI, and any merged controller must
   re-run the three pre-promotion panels (recovery / fixed feasible-row /
   fresh-seed) before WP2 consumes any recoverable-set surface.
2. **Codex/autonomous execution follows the Phase-3 roadmap only.** WP6.2
   guardrails are live: validator V7 enforces feasibility-oracle-first rules,
   blocked-dependency escalation exists under `docs/escalations/`, long
   measurements use `scripts/run_managed.sh`, and task state stays explicit in
   `experiments/research_queue.csv` / `experiments/research_status.json` /
   `experiments/scoreboard.csv`.
3. **Long measurements run as managed background processes only** (the
   agent-dies-measurement-dies failure occurred 3x and is a banned pattern).
4. **Acceptance criteria are pre-registered before any run**; selection /
   validation / training seed streams are mutually disjoint and frozen in
   pre-registration JSONs.
