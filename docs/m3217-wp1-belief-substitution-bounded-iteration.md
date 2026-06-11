# M3217 WP1 Belief-Substitution Bounded Iteration (terminal G-B adjudication)

Status: completed (harness run
`runs/research/m3217-wp1-belief-substitution-bounded-iteration_20260611T151842Z`,
returncode 0, 24.9 s to the pre-registered stop, 16 workers). Manual-takeover
mixed bookkeeping: registered and executed as a formal harness milestone per
the Phase-2 plan (`docs/research-plan-phase2-capability-boundary-tracking.md`
WP1.4 route). Branch `phase2_wp1_belief`; auxiliary measurement; the
engineering incumbent and `ActiveSafetyReflexDriver` are unchanged.

`self_id_evidence_discipline.claim_level`: `not_applicable`.

## 1. What this milestone is

The **single** bounded excitation/representation iteration granted by the
M3216 all-arms-fail route
(`all_arms_fail_one_bounded_iteration_then_accept_bound`, <= 1 week, <= 4 h
CPU). The full iteration design was frozen BEFORE any run in
`experiments/feasibility_audit/wp1_iter1_prereg.json`; the gated criteria
(primary rule, floor/oracle definitions, 240-episode paired validation
budget, two-way SE) are UNCHANGED from
`experiments/feasibility_audit/wp1_prereg.json`. The outcome is **terminal
for WP1 either way** -- there is no second iteration.

Two repairs scoped by the M3216 FAIL diagnosis, both frozen ex ante:

- **Repair A (distribution shift)**: 50/50 mix of closed-loop trajectories
  (rolled out by the frozen M3216 best-selection seeker configs, no belief,
  collection-only mu-free dv jitter U(-0.75,+0.75)) into the leak-gated
  training data, on fresh re-based seed streams (base 20270301, layout
  unchanged -- every M3216 subst_val outcome had been read by the diagnosis).
  The pre-registered dataset leak gate (decision-frame single-frame -> mu
  out-of-fold R^2 <= 0.1, linear + MLP probes) is **rerun on the pooled
  mixed set**; any cell failing stops the run before training, and the stop
  is terminal.
- **Repair B (injection timing)**: heteroscedastic 3-member ensembles
  (Gaussian-NLL heads, per-tick supervision) emit per-tick (mu_hat,
  sigma_total = aleatoric + ensemble disagreement); the seeker consumes the
  estimate CONTINUOUSLY pre-reveal (entry-speed law `_v_target`, force-limit
  `_limit_est`) iff sigma_total <= 0.12 (frozen), freezes the belief at the
  reveal, and FALLS BACK to its internal detector when never confident
  (`RampPolicyController` `injection_mode="continuous"`, inert by default;
  the 10 existing hook bit-compat tests and 15 WP1 pipeline/trainer tests
  pass unchanged). The --quick smoke verified the fallback path bit-exact:
  never-confident ensembles leave the injected arm paired-identical to the
  floor (Delta exactly 0.000).

## 2. Measured result: pre-registered terminal stop at the mixed-set leak gate

The --full run collected the full mixed dataset (606 episodes/cell = 280
scripted + 280 closed-loop train/sel + 23 + 23 validation; 2,424 episodes
total, 0 invalid) and **stopped at the rerun dataset leak gate in all four
cells** (`status stopped_dataset_leak_gate_failed_iter1`), exactly as the
frozen route prescribes. Decision-frame single-frame -> mu out-of-fold R^2:

| cell | pooled lin / MLP (gate, bar 0.1) | scripted-only lin / MLP | closed-loop-only lin / MLP | gate |
|---|---|---|---|---|
| delay5 | **0.399 / 0.329** | -0.023 / -0.257 (pass) | 0.915 / 0.906 | **FAIL** |
| delay12 | **0.336 / 0.325** | +0.047 / -0.184 (pass) | 0.914 / 0.893 | **FAIL** |
| delay25 | **0.436 / 0.457** | +0.021 / -0.180 (pass) | 0.967 / 0.959 | **FAIL** |
| noise0.05 | **0.234 / -0.046** | -0.080 / -0.779 (pass) | 0.632 / 0.470 | **FAIL** (linear) |

The structure is mechanistically clean (measured, not inferred-only):

1. The scripted half passes the double-probe gate in all four cells on the
   fresh streams -- an independent replication of the M3216 repaired
   pipeline's mu-decoupling under a new seed base.
2. The closed-loop half is massively current-frame mu-readable at the
   decision frame (linear OOF R^2 0.63-0.97) **even with the +/-0.75 dv
   jitter**: the seeker's approach state at the reveal (speed tracked to
   `v_target(mu_hat)`, longitudinal actuator state) encodes its own internal
   detector belief mu_hat ~ mu. This is not harness-label leakage; it is the
   behavior policy's belief being legible in its behavior -- which the
   frozen attribution gate (correctly, for the history-borne C2 claim)
   cannot and does not distinguish from a leak.

Inference (labeled as such): on this construction the two requirements of
the substitution protocol are **mutually incompatible** -- training data that
matches the eval-time closed-loop distribution (the M3216-diagnosed failure
mechanism) is inherently single-frame mu-readable, so it cannot pass the
gate that protects the claim the estimator exists to support. The bounded
iteration therefore terminates at the gate, before training, with no
training/selection/validation episode of the gated streams consumed.

## 3. Terminal adjudication (pre-registered routes applied as written)

1. **WP1 primary verdict: FAIL** (`primary_fail_mode =
   mixed_dataset_leak_gate_failed`; route `terminal_bound_accepted`). The
   single pre-authorized iteration is consumed. **G-B does not open WP2.**
2. **The accepted C2 bound**: the mu belief is *learnable* from history on
   this testbed (M3216 estimator-level GRU R^2 0.91-0.99 in the delay cells,
   history-borne by the reset control) but is **not redeemable through this
   substitution interface** at the pre-registered recapture bar -- and the
   interface cannot be repaired by on-policy data without breaking the
   attribution gate (this milestone's measured sharpening of the bound).
3. **Paper scope contracts as pre-registered** to C1 + the estimator-level
   positive + this bound. The M3216 delay12 result (+0.185, lo97.5 +0.110,
   recapture 0.38) remains the only standing substitution-level positive.
4. No threshold was weakened; no second iteration is permitted or planned.

## 4. Per-cell recapture table (standing WP1 numbers vs this iteration)

The iteration stopped before any substitution measurement, so the M3216
table remains the standing WP1 substitution evidence; iter1 contributes the
gate table above and no recapture numbers.

| cell | prize (M3216, re-measured) | L3 recapture (M3216) | L3 lo97.5 (M3216) | iter1 recapture |
|---|---|---|---|---|
| delay5 | +0.217 | -0.65 | -0.227 | not measured (terminal gate stop) |
| delay12 | +0.483 | **0.38** | **+0.110** | not measured (terminal gate stop) |
| delay25 | +0.133 | -1.27 | -0.285 | not measured (terminal gate stop) |
| noise0.05 | +0.117 | -2.04 | -0.322 | not measured (terminal gate stop) |

## 5. Claim boundary

Allowed: the pre-registered bounded-iteration outcome (the mixed-set gate
table, the terminal stop, the accepted C2 bound and its measured sharpening)
on the scripted B2K2 prefix-carrying construction, and the terminal G-B
adjudication exactly as pre-registered. Rejected (explicit): any
driver-performance, current-sim, high-fidelity, full-driver, repair-success,
robustness-result, feasibility-proof, validation/ranking/promotion,
paper-result, or self-ID capability claim; any reading of the closed-loop
collection seekers or estimator code as deployable drivers; any second
substitution iteration.

## 6. Artifacts

- `runs/feasibility_audit/wp1_iter1_full/summary.json` (both prereg echoes,
  per-cell probe tables, terminal verdict; status
  `stopped_dataset_leak_gate_failed_iter1`) + `progress.jsonl` (4 data units)
- `experiments/feasibility_audit/wp1_iter1_prereg.json` (frozen iteration
  design incl. the continuous-injection appendix and terminal routes);
  `experiments/feasibility_audit/wp1_prereg.json` (unchanged criteria)
- `scripts/feasibility_audit/wp1_iter1_full_run.py` (orchestrator; `--quick`
  smoke artifacts in `runs/feasibility_audit/wp1_iter1_full_quick/`);
  `scripts/feasibility_audit/ramp_policy_voi_regime.py` (inert-by-default
  `injection_mode="continuous"` extension)
- harness record: `runs/research/m3217-wp1-belief-substitution-bounded-iteration_20260611T151842Z/command.log`
- review: `docs/reviews/m3217-wp1-belief-substitution-bounded-iteration.md`
