# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Actor Contract

Mainline actor:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deployable inputs:

- ego kinematics / IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road / free-space / obstacle geometry in ego frame;
- recurrent state from past command-response history.

Not allowed in the deployable actor:

- `mu`, mass, CG, tire stiffness, brake scale, actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode or rule branch;
- `speed_ref`, `beta_target`, path error, heading error, path curvature;
- TTC, required clearance, oracle stopping distance, reference trajectory;
- collision/success/progress labels or any precomputed answer.

## Current Checkpoints

Latest public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Status: M400 promoted M399 alpha `0.05` as the current public-gate base after
six public replay surfaces and behavior seeds passed. M487-M606 did not promote
a new public-gate driver checkpoint.

Latest active diagnostic BC checkpoint:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

Status: M568 scaled BC L3 checkpoint selected by M569 and used for M570-M752
diagnostics. It is not the public-gate base and is not promoted as the current
driver checkpoint.

## Current Blocker

```text
m764-v4-residual-closed-loop-replay-implementation
```

M764 should implement the no-PPO closed-loop replay evaluator designed in M763.
It should compare base alpha `0.0` with residual alphas `0.2`, `0.5`, and
`1.0`, reconstruct M755/M761 source rows, report normal retention separately
from intervention sensitivity, stratify by variant/horizon/fault family, and
keep training, PPO, and checkpoint promotion blocked.

## Recent Evidence Line

- M763 designs a no-PPO closed-loop replay evaluator for the M761 residual
  head. It compares base alpha `0.0` with residual alphas `0.2`, `0.5`, and
  `1.0`, reconstructs M755/M761 source snapshots, applies the residual wrapper
  at every rollout step, and reports normal retention separately from
  intervention action/outcome sensitivity. Required metrics include success,
  collision, road departure, spin, terminal reason, clearance margin,
  first-action drift, sequence-action drift, variant/horizon/fault-family
  stratification, and hard-negative/sentinel diagnostics. Training, PPO, and
  promotion remain blocked.
- M762 audits M761 as a clean objective-only positive, not a promoted driver.
  It supports that the v4 sequence corpus has residual actor-coupling signal:
  alpha `0.2`, `0.5`, and `1.0` improve exact gap metrics while keeping normal
  first-action drift inside gates. It keeps `scenario_sampling_failure` visible
  because hard-negative availability remains `0.721352` and rows are dominated
  by `zero_command_obs` and long horizons. The next admitted step is only a
  no-PPO closed-loop residual replay design.
- M761 implements and runs the no-PPO frozen-backbone residual objective probe.
  It reconstructs `1213/1213` M755 positive rows with `0` metadata misses and
  `0` rejected rows, trains only a `4355`-parameter residual head for `40`
  epochs, and keeps the base actor checksum unchanged. Result class is
  `v4_sequence_objective_probe_candidate`: alpha `0.2`, `0.5`, and `1.0` pass
  exact candidate gates. At alpha `0.2`, normal first-action drift mean/p95 is
  `0.000480/0.000939`, gap mean/p10 is `0.029079/0.023874`, and gap deficit
  mean is `0.012637`. At alpha `1.0`, gap mean reaches `0.047347` and gap
  deficit mean drops to `0.000000337` while normal drift remains within gates.
  No PPO or checkpoint promotion occurred.
- M760 designs a conservative no-PPO objective-only probe: frozen BC5660 actor
  backbone, bounded residual head, normal residual target zero, existing
  intervention direction preservation/amplification, optional sparse
  hard-negative calibration, and alpha ladder `0.02,0.05,0.10,0.20,0.50,1.00`
  with exact M758 metrics. No PPO or promotion is allowed.
- M759 audits M758 as a clean no-training exact objective sanity result, not a
  trained-driver improvement. It admits only objective-only probe design with
  exact before/after metrics and normal-retention gates. PPO/promotion remain
  blocked.
- M758 implements and runs the no-training exact/offline v4 sequence objective
  sanity evaluator. It reconstructs `1213/1213` M755 positive groups with no
  metadata misses, no missing normals, no missing snapshots, and no rejected
  rows. Exact metrics are finite: gap mean `0.024908`, gap p10 `0.021141`,
  target gap mean `0.041716`, gap deficit mean `0.016809`. The result is
  `v4_sequence_objective_hard_negative_sparse` because hard-negative
  availability is `0.721352`.
- M757 designs a constrained v4 sequence objective from the M755 corpus. It
  treats M755 as an index/evidence corpus, not a tensor dataset, and requires
  M758 to reconstruct samples by replay. The objective keeps normal behavior
  retention, an intervention branch anchor, outcome-weighted gap preservation,
  and optional hard-negative calibration. Actor update/PPO/promotion remain
  blocked.
- M756 audits M755 as a valid v4 positive corpus export with sparse hard
  negatives. It admits only constrained objective design: use positives and
  matched normals as required contrast, treat hard negatives as optional sparse
  contrast, preserve claim-boundary metadata, and keep PPO/promotion blocked.
- M755 implements the deterministic v4-aware sequence-outcome corpus exporter
  and runs the registered export. It writes `1213` clean positive rows, `1213`
  matched normal rows, `1009` hard-negative action-only rows, and balance
  artifacts. Positive corpus gates pass with `0` sentinel positives, `0`
  missing normals, `0` missing metadata rows, `27` seeds, `17` fault-family
  pairs, max seed dominance `0.171476`, and
  `claim_boundary_level=current_model_or_proxy`. Hard-negative contrast remains
  sparse, so objective work remains blocked pending M756 audit.
- M754 designs a v4-aware deterministic corpus export for M752's non-sentinel
  outcome positives. Precheck values are `1213` positives, `0` positive
  sentinels, `27` positive seeds, `17` fault-family pairs, max seed dominance
  `0.171476`, `0` missing normal matches, `source_kind=v4_reset_source`, and
  `claim_boundary_level=current_model_or_proxy`. Hard negatives are useful but
  sparse: `1009` capped hard negatives for `1213` positives.
- M753 audits M752 as a clean diagnostic positive, not trained-driver
  improvement. It supports the coverage-mining hypothesis and promotes only to
  a v4-aware corpus export design. Objective training, PPO, promotion, and true
  per-wheel/four-wheel fault claims remain blocked.
- M752 implements and runs v4 reset-source sequence interventions over M749
  reset-only rows. It selects `512` source rows with `461` primary rows and
  `51` sentinels across `31` seeds, `9` preferred fault families, `7` wrong
  fault families, and `21` fault-family pairs. It evaluates `12288` rollout
  rows and finds `5429` action-critical rows plus `1213` outcome-critical rows
  across `27` seeds and `17` fault-family pairs. Outcome rows are dominated by
  `zero_command_obs` (`1044`) and grow with horizon (`H=2:25`, `H=4:168`,
  `H=6:455`, `H=8:565`). Actor parameters are unchanged, sentinel
  false-positive rate is `0.0`, and no training/PPO/promotion occurs.
- M751 designs the v4 reset-source sequence intervention branch over M749
  reset-only rows. It requires source-balanced selection, `10%` sentinels,
  preserved `source_kind=v4_reset_source`, and `current_model_or_proxy` claim
  boundary metadata before any source export or objective design.
- M750 audits M749 as broad, clean reset-only v4 evidence rather than
  wrong-history proof. V4 source generation increases reset rows from M740's
  `744` to M749's `1171`, but wrong-history action-critical rows remain `0`.
  The audit selects source-balanced v4 sequence intervention as the next
  branch.
- M749 runs the no-training v4 extreme-fault coverage wave with `28`
  executable current/proxy faults and `14` future-only fault labels. It
  generates `14848` scenarios, `100624` snapshots, `12288` matched pairs, and
  `1171` reset-only rows. Actor parameters are unchanged and no training/PPO
  occurs.
- M689 implements gate-margin response amplification and passes exact
  actor-coupling gates for `3/3` seeds at `alpha=1.0`. Source-holdout selected
  metrics: normal mean `0.001380-0.001461`, gap mean `0.010731-0.011165`, gap
  ratio `3.734864-3.885905`, wrong-target improvement `0.782311-0.795998`,
  first drift p95 `0.003748-0.004017`; actor checksum unchanged, no base actor
  checkpoint, no PPO, no promotion. Caveat: normal gate remains moderately open,
  so this is an exact diagnostic pass, not a clean gate-factorization claim.
- M688 designs gate-margin response amplification after M686 gate collapse. It
  keeps the split/gated head and exact gates, but adds detached-normal
  wrong-vs-normal gate margin, hard low-gate wrong rows, stronger wrong
  gate-open pressure, and gate-margin diagnostics. PPO and promotion remain
  blocked.
- M687 audits M686 as `gate_collapse`, not amplifier capacity failure. The raw
  wrong amplifier is large, but wrong gates stay near normal gates and do not
  open toward target `0.50`. The next branch should add explicit gate-margin
  and hard low-gate wrong-row pressure.
- M686 implements split/gated response amplification. It is implementation-clean
  with gated residual heads active and actor checksum unchanged. Normal
  retention is strong (`alpha=1.0` normal mean `0.001097-0.001159`), but gates
  collapse (`normal_gate_mean` about `0.098`, `wrong_gate_mean` about
  `0.102-0.105`) and wrong gap stays around `0.0064`, so no seed/alpha passes.
- M685 designs a split/gated residual head after the M680/M683 scalar-loss
  tradeoff. The proposed head factors output into `gate(feature) *
  amplifier(feature)`, adds normal gate close and wrong gate open losses, keeps
  normal sequence/first-step safety and detached-normal wrong-history gap
  losses, and reports gate diagnostics without using them as promotion
  evidence.
- M684 audits M683 as `wrong_gap_suppressed_by_normal_sequence_anchor`. M680 and
  M683 now bracket the scalar-loss conflict: wrong pressure can restore gap but
  moves normal sequence residuals; normal sequence pressure improves retention
  but suppresses wrong-history gap. The next design target is a split/gated
  residual response amplifier, not PPO, gate weakening, or input changes.
- M683 implements normal-sequence-safe branch-specific response amplification.
  It is implementation-clean: `648` rows, `216` sources, `3` residual heads,
  actor checksum unchanged, no base actor checkpoint, no PPO, and no promotion.
  It improves normal retention versus M680 (`alpha=1.0` best normal mean
  `0.002769` versus `0.003753`) but suppresses wrong-history gap (`alpha=1.0`
  best gap mean `0.008320`, ratio `2.895718`, wrong-target improvement
  `0.438964`), so no seed/alpha passes.
- M682 designs normal-sequence-safe branch-specific response amplification. It
  preserves M680's detached-normal wrong-history pressure and adds full
  normal-sequence mean/top-k retention losses with initial thresholds `0.0020`
  mean and `0.0045` top-k. This targets M680's normal full-sequence mean
  failure without weakening exact gates.
- M681 audits M680 as
  `branch_specific_gap_partial_normal_sequence_retention_failure`. M680's
  branch-specific wrong-history pressure is useful, but normal full-sequence
  retention is now the blocker. The next design should add normal sequence
  mean/top-k pressure while keeping wrong-history pressure and first-step
  safety.
- M680 implements branch-specific response amplification. It is a clean negative
  result with progress: branch-specific pressure restores wrong-history gap
  enough for seed `6801` at `alpha=1.0` to pass gap, p10, ratio, wrong-target,
  and first-drift gates, but normal full-sequence mean is `0.003753`, above the
  `0.0025` retention gate. The next blocker is normal sequence retention, not
  first-step safety or missing wrong-history signal.
- M679 designs branch-specific response amplification. It keeps frozen BC5660,
  fused-plus-next-hidden features, first-residual execution, alpha ladder,
  exact-first evaluation, no PPO, no promotion, and no input changes, while
  adding detached-normal gap losses, stronger wrong-history branch pressure,
  wrong first/sequence gap hinges, and hard low-gap row pressure.
- M678 audits M677 as `first_step_safety_positive_wrong_gap_suppressed`.
  First-step normal safety is now controllable, but wrong-history gap collapses.
  The next design target is branch-specific wrong-history pressure with
  detached-normal gap losses, not more normal anchoring, PPO, or gate weakening.
- M677 implements the first-step-safe residual objective. It is a clean negative
  result: actor checksum unchanged, no base actor checkpoint, no PPO, no
  promotion, but `0` seed/alpha candidates pass. It fixes first-step normal
  drift (`alpha=1.0` p95 down to `0.0025-0.0033`) but suppresses wrong-history
  sequence gap (`alpha=1.0` gap mean `0.0036-0.0069`, ratio `1.25-2.40`). The
  next step is an audit and branch-specific redesign.
- M676 designs the first-step-safe residual objective. It keeps frozen BC5660,
  fused-plus-next-hidden features, residual sequence head, first-residual
  execution, alpha ladder, and exact-first evaluation, but adds
  `L_normal_first_zero`, top-k/p95 normal first-residual hinge
  (`threshold=0.004`, fraction `0.10`), and wrong-history first-gap target
  `0.006` while preserving the M671 sequence target. PPO and promotion remain
  blocked.
- M675 audits M674 as `first_action_drift_vs_sequence_gap_conflict`, not a
  representation failure. The next step is a first-step-safe residual objective
  with strong normal first-action anchoring, top-k/p95 first residual penalty,
  wrong-history sequence target, and wrong-history first-gap objective. Frozen
  backbone, fused-plus-next-hidden view, alpha ladder, exact-first evaluation,
  no PPO, no promotion, and no actor-input changes remain required.
- M674 implements the frozen-backbone residual sequence-head actor-coupling
  exact probe. It is a clean negative result: actor checksum unchanged, no base
  actor checkpoint, no PPO, no promotion, but `0` seed/alpha candidates pass.
  The blocker is an alpha conflict: `alpha=1.0` has enough sequence gap but
  first-action normal drift p95 fails; `alpha=0.5` is mostly safe but sequence
  gap and gap ratio are below threshold. The next step is an audit and a
  first-step-safe redesign, not PPO.
- M673 designs the first conservative actor-coupling probe after the positive
  M671 shadow result. The probe freezes the BC5660 actor backbone and trains
  only a residual sequence head on fused-plus-next-hidden features. It predicts
  a short residual sequence but executes only the first residual in closed loop,
  with alpha ladder `0.02,0.05,0.10,0.20,0.50,1.00`. Exact source-heldout
  metrics must pass before replay; PPO, promotion, actor-input changes, and
  base actor checkpoint writing remain forbidden.
- M672 audits M671 as
  `shadow_positive_representation_action_boundary_evidence`, not closed-loop
  self-ID proof. Fused-plus-next-hidden supports source-heldout wrong-history
  sequence amplification in `2/3` seeds; fused alone fails and next-hidden
  alone misses normal-retention mean. PPO, promotion, and actor-input changes
  remain blocked. The next admitted step is a design-only exact-gated
  actor-coupling milestone.
- M671 implements and runs the frozen-actor response-amplification shadow
  objective. It reconstructs `648` source-balanced rows from M667 candidates
  across `216` sources and `100` physical pairs. The fused view fails, the
  next-hidden view has enough wrong-history gap but slightly too much normal
  residual, and fused-plus-next-hidden passes in `2/3` seeds with source-heldout
  gap ratios above `4.22` and wrong-target MSE improvements around `0.90`.
  Actor checksum is unchanged, no actor checkpoint is written, no PPO is used,
  and no checkpoint is promoted. The result is shadow-positive but not
  closed-loop proof.
- M670 designs the concrete frozen-actor response-amplification shadow
  objective. M671 should reconstruct source-heldout shadow data from M667
  candidates, anchor normal residuals to zero, amplify existing wrong-normal
  action-delta directions to a bounded target gap, compare fused/next-hidden/
  fused-plus-hidden views, and require exact source-heldout metrics before any
  actor coupling is considered.
- M669 designs a conservative no-PPO action-boundary response-amplification
  ladder. The next step is a frozen-actor shadow objective over fused,
  next-hidden, and fused-plus-hidden feature views with normal-history anchors,
  wrong-history sequence-separation targets, source-heldout exact evaluation,
  and no actor mutation.
- M668 audits M667 as `near_boundary_exists_but_wrong_history_outcome_insensitive`.
  Valid near-boundary preferred windows exist and first-action differences are
  common, but short-horizon action separation is weak and outcome gaps are
  absent. The next branch should address the action boundary directly through a
  no-PPO response-amplification design with exact/replay gates before any actor
  coupling.
- M667 implements and runs the normal-success near-boundary source miner. It
  finds `204` valid near-boundary preferred windows, so source-window coverage
  is not the active blocker. It still accepts `0` rows: wrong history changes
  first actions often, but only `4` rows pass the sequence threshold, `0` pass
  preferred-vs-rejected `0.010`, `0` pass margin threshold, and success-drop
  rate is `0.000`. Normal and wrong-history branches both succeed at rate
  `1.000`.
- M666 designs a normal-success near-boundary source miner. The source order is
  now: wider obstacle decision-window bank, normal-history prepass, margin-band
  classification, then wrong-history pairing only for
  `near_boundary_preferred` windows. This directly addresses M664's issue where
  action-sensitive rows were already failed under normal history.
- M665 audits M664 as `action_gap_positive_outcome_gap_negative`. M664 found
  wrong-history action gaps, but the rows that crossed all action thresholds
  were already failed under normal history and had no success-drop or
  margin-gap evidence. The likely root cause is source-window quality:
  close-obstacle windows expose action sensitivity too late. The next branch is
  a normal-success near-boundary source filter before wrong-history pairing.
- M664 implements and runs the broader no-training action-critical
  wrong-history source miner. It builds `473` snapshots and scores `7200`
  candidate sequence rows. The result is still negative: `0` accepted rows.
  Compared with M661, action sensitivity improved (`5352` first-action
  threshold rows, `60` sequence-threshold rows, `3` all-action-threshold rows,
  max sequence mean L2 `0.010464`), but outcome sensitivity is absent: `0`
  margin-threshold rows and success-drop rate `0.000`. The all-action-threshold
  rows are already failed under normal history, so they are not usable
  self-ID supervision.
- M663 designs the action-critical wrong-history source miner. The key change
  is to invert source selection: first build a broader snapshot bank and test
  many compatible wrong-history candidates, then accept rows only when wrong
  history creates explicit short-horizon action-sequence divergence plus
  margin/success sensitivity. Hidden distance may rank proposals but cannot be
  an acceptance criterion.
- M662 audits M661 as implementation pass but corpus gate fail. M661 evaluated
  `3207` candidates and wrote valid preferred/rejected artifacts, but the
  existing matched-current surfaces produce neither meaningful wrong-history
  action sequence divergence nor margin divergence. The next branch is
  action-critical wrong-history source mining, not threshold weakening,
  objective tuning, actor coupling, or PPO.
- M661 implements and runs the no-training action-divergent wrong-history corpus
  miner. It is a clean negative result: `0/3207` candidates accepted. The max
  wrong-history sequence mean L2 is only `0.001850` versus the `0.006`
  threshold, max preferred-vs-rejected sequence mean L2 is `0.001850` versus
  `0.010`, max margin gap is `0.000031` versus `0.010`, and both normal and
  wrong-history success rates are `1.000`. Actor checksum is unchanged and no
  actor checkpoint is written. This means the existing M586/M636
  matched-current surfaces are hidden/feature-different but not usable
  action-divergent wrong-history supervision.
- M660 designs the action-divergent wrong-history corpus. The next miner should
  stop accepting hidden-difference-only rows and require explicit
  preferred/rejected action sequences, first-action divergence, short-horizon
  action divergence, margin gap, and source-heldout split coverage before any
  new objective is considered.
- M659 audits M658 as
  `partial_relative_signal_but_absolute_wrong_history_gap_negative`.
  `next_hidden` carries more wrong-history signal than fused features, but not
  enough: wrong-history L2 remains below threshold and mean gap MSE is negative.
  The next blocker is corpus/target design, not actor coupling or more fused
  contrast tuning.
- M658 implements the frozen feature-view comparison probe. It is negative:
  `diagnostic_passed=false`, with no passed views. `next_hidden` improves
  wrong-history prediction L2 by about `3.71x` over fused on average, but only
  reaches `0.001732`, below the `0.005` threshold, and wrong validation gap MSE
  remains negative on average. Actor checksum is unchanged and no actor
  checkpoint is written.
- M657 designs the fusion-boundary probe. The implementation should evaluate
  three frozen feature views: fused actor features, next recurrent hidden state,
  and their concatenation. The decision rule is diagnostic: if next-hidden or
  fused-plus-hidden creates source-heldout wrong-history separation while fused
  remains weak, the fusion boundary becomes the next design target; no actor
  checkpoint may be written.
- M656 audits M655 and admits a fusion-boundary probe design. The strongest
  interpretation is that wrong-history information exists in recurrent state
  and survives the current-response GRU update, but is too weak at the fused
  feature and actor-action boundary. The next branch should compare fused,
  next-hidden, and fused-plus-hidden diagnostic heads before actor coupling or
  PPO.
- M655 implements and runs the no-training feature separability audit. The
  result is `fusion_washout`: wrong-history raw hidden L2 is `0.097340` and
  next-hidden retention is `0.409547`, so the signal is not absent, but fused
  feature L2 is only `0.014905` and actor action L2 is only `0.000685`.
  Wrong-history feature/action gaps are only `20.27%` and `5.12%` of the
  delayed-history gaps. Actor checksum is unchanged and no checkpoint is
  written.
- M654 designs the wrong-history feature separability audit. The next diagnostic
  should measure raw hidden, next hidden, fused feature, actor mean, and tanh
  action distances for normal versus variant histories, with group summaries by
  variant, split, source, target, and surface. Actor coupling, contrast tuning,
  PPO, and promotion remain blocked until M655 localizes where the
  normal-vs-wrong signal collapses.
- M653 audits M652 as `normal_retention_positive_wrong_history_gap_negative`.
  Normal validation retention is good, but wrong-history gap MSE/L2 are one to
  two orders of magnitude below threshold. The likely blocker is weak
  normal-vs-wrong separability in frozen BC5660 recurrent features. M653 rejects
  actor coupling and rejects increasing contrast coefficients before a feature
  separability audit.
- M652 implements and runs the frozen-head wrong-history contrast smoke. It is
  a clean negative result: `0/3` seeds pass. Normal validation MSE remains good
  (`0.000491`, `0.000508`, `0.000509`), but wrong-history gaps stay near zero:
  validation gap MSE is negative for all seeds and validation gap L2 is only
  `0.000624-0.000748`, far below the `0.005` threshold. Actor checksum is
  unchanged and no actor checkpoint is written.
- M651 designs the frozen-head wrong-history contrast objective. It keeps actor
  parameters frozen and trains only the auxiliary head. The design uses normal
  target loss plus a wrong-history margin loss on `wrong_matched_history` rows,
  with delayed-history rows reported but not forced into the rejection loss.
  M652 must preserve normal validation MSE `<= 0.0010` while creating
  wrong-history train/heldout gap thresholds.
- M650 audits M649 as `pass_with_wrong_history_limitation`. The 3/3 head-only
  repeat proves frozen-feature sequence-delta learnability, but wrong-history
  sources `30` and `32` have normal/variant prediction gaps around
  `0.0005-0.0007`. This is not self-ID separation. M650 rejects direct adapter
  or actor coupling and admits wrong-history contrast design.
- M649 implements the early-stopped multi-seed frozen-head repeat. All three
  seeds pass best-validation thresholds, all best/final head checkpoints are
  written, and actor checksum remains unchanged. Best validation MSE is
  `0.000486`, `0.000458`, and `0.000502` for seeds `6460`, `6461`, and `6462`.
  The limitation is wrong-history separation: sources `30` and `32` have
  normal/variant prediction gaps only about `0.0005-0.0007`, so actor coupling
  remains blocked pending M650 audit.
- M648 designs the early-stopped multi-seed head-only repeat. The next run
  should use seeds `6460`, `6461`, and `6462`, save best-validation heads, use
  a lower `240` epoch cap, and require at least `2/3` seeds to reach train
  improvement `>= 30%`, validation improvement `>= 50%`, best validation MSE
  `<= 0.00075`, and final-vs-best ratio `<= 3.0`. Actor coupling remains
  blocked.
- M647 audits M646 as `pass_with_overfit_caveat`. The correct best validation
  epoch is `120` with normal delta-MSE `0.000490287`; final epoch `300` is
  `0.001331890`, or `2.72x` the best value. Source-level summaries show
  wrong-history source separation remains weak, especially source `32`, whose
  variant loss is lower than normal loss. M647 admits an early-stopped
  multi-seed head-only repeat, not actor coupling.
- M646 implements and runs the frozen-actor BC-v2 sequence-delta head-only
  smoke. It passes the pre-registered gate: train delta-MSE improves
  `97.28%`, source-heldout validation improves `84.50%`, the actor checksum is
  unchanged, only `sequence_delta_head.pt` is written, and no actor checkpoint
  or promotion occurs. Caveat: validation is best at epoch `120`
  (`0.000490287`) and worsens by epoch `300` (`0.001331890`), so M647 must audit
  before actor coupling.
- M645 designs the frozen-actor head-only smoke. The later implementation may
  train only `SequenceDeltaHead(features) -> delta_action_sequence`; all BC5660
  actor/recurrent/critic parameters remain frozen. The pass criterion is
  train delta-MSE improvement `>= 30%`, source-heldout validation not worse,
  actor checksum unchanged, only a head checkpoint written, and no promotion.
- M644 implements and runs the exact no-update BC-v2 evaluator. Normal-hidden
  first-action loss is `0.002101438`; variant-hidden first-action loss is
  `0.002599709`; sequence-delta target MSE is `0.002039985`; and actor checksum
  is unchanged. Normal actions reconstruct stored base first actions to
  `4.04e-8` weighted mean L2, confirming the evaluator is live and no-update.
  Wrong-history sources still have very small normal/variant action gaps, so
  M644 admits only a frozen-actor head-only smoke design, not an actor update.
- M643 designs the source-balanced BC-v2 objective. The key constraint is that
  M641 has initial observation/hidden plus target sequences, but not the
  closed-loop post-target observation sequence. Therefore the next step is not
  a direct full-actor update. The safe ladder is M644 exact evaluator, then a
  frozen-actor shadow/head-only smoke, then only later a tightly gated adapter
  or actor update. Metadata remains objective-only and cannot enter actor
  inputs.
- M642 runs exact objective sanity on the M641 sequence corpus. The NPZ and
  metadata align for `431` rows; all rows have nonzero target/base deltas;
  `outside_mask_abs_max` is `0.0`; weighted sequence MSE is `0.002039985`; and
  source weights are balanced with max absolute source-weight error
  `8.28e-10`. Train and source-heldout validation objective scales are close:
  weighted MSE `0.002054882` versus `0.002010192`. This admits BC-v2 objective
  design, not training or promotion.
- M641 implements and runs the source-balanced sequence target corpus builder.
  It selects `431` rows across `9` source rows, `8` physical pairs, `6` left
  seeds, `2` surfaces, `3` targets, and `2` variants. It writes
  `balanced_sequence_targets.csv`, `balanced_sequence_target_corpus.npz`,
  source-balance summaries, and top-k diagnostics. The split is group-aware:
  train has `271` rows and source-heldout validation has `160` rows, with
  sources `20` and `32` held out together because they share a physical pair.
  Equal source total weights are written. This is corpus infrastructure only;
  actor training, PPO, and promotion remain blocked pending exact objective
  sanity.
- M640 designs the source-balanced sequence target corpus. M641 should cap M639
  accepted candidates per source/grid/family, use equal source total weights,
  and write both `balanced_sequence_targets.csv` and
  `balanced_sequence_target_corpus.npz`. Source labels and target metadata
  remain training metadata only and must not enter actor input.
- M639 implements and runs the no-training broad source-diversity expansion.
  It selects `9` M627 trust-primary non-collision source rows and all `9` have
  accepted projected candidates. Accepted evidence covers `8` physical pairs,
  `6` left seeds, `2` surfaces, `3` targets, and `2` variants, with trust limits
  preserved. This passes the target-corpus admission-candidate gate, but it does
  not yet admit training because raw accepted candidates are dominated by a few
  high-count sources.
- M638 designs the broader source-diversity expansion. M639 should select the
  M627 trust-primary non-collision near-miss rows, run the combined projected
  shape grids over that expanded set, and classify target-corpus admission only
  if accepted evidence reaches at least `8` source rows, `6` physical pairs,
  `6` left seeds, `2` surfaces, and `2` targets. If the result remains close to
  the four-source M636 footprint, the branch should stop pure sequence-grid
  mining and move to local QP / hidden-to-action forcing / BC-v2.
- M637 audits M636 as strong positive but not source-diverse enough for target
  corpus admission. M636 proves projection plus local shape design can recover
  four focused sources, but accepted candidates still come from only `4` source
  rows, `4` physical pairs, and `3` left seeds. M638 should expand the source
  set before any optimizer or actor-update design.
- M636 implements and runs the two-grid combined projected search. It evaluates
  `7884` candidates, accepts `1424`, preserves trust limits, and produces
  accepted candidates for all four focused sources: source `8` `664`, source
  `30` `430`, source `0` `196`, and source `7` `134`. Accepted targets include
  both `future_braking_deceleration` and `future_yaw_response`.
- M635 designs a two-grid combined projected search. Grid A preserves M633's
  source8/source0/source30 recovery. Grid B restores M630's source7 pattern
  around steer `0.08`, throttle `0.00`, and brake `0.00/0.04`. M636 should
  implement this as a no-training artifact pass with source-level outcomes for
  all four sources.
- M634 audits M633 as strong targeted-positive with sentinel grid regression.
  The source-7 failure is likely coverage, not a fundamental conflict: M633 did
  not include M630's source-7 pattern around steer `0.08`, throttle `0.00`,
  brake `0.00/0.04`. M635 should design a combined grid that merges source8
  recovery and source7 preservation.
- M633 implements and runs the source-8 targeted projected search. It evaluates
  `10080` candidates, preserves trust limits, recovers source `8` with best
  improvement `0.026789`, recovers source `0` with `0.022995`, and improves
  source `30` with `0.029507`. Source `7` regresses from accepted to best
  improvement `0.019965`, just below threshold, so this remains diagnostic and
  requires M634 audit.
- M632 designs a source-8 targeted projected shape search. Source `8` is only
  `0.001248` below the margin threshold after M630. The design focuses a local
  microgrid around K=7 constant-delta signs (`throttle_delta=-0.06`, steer near
  `0.00` to `0.04`, brake near `0.04`) and adds K=5/K7/K9 targeted projected
  shape families. Source `0` is secondary; sources `7` and `30` are sentinels.
- M631 audits M630 as narrow diagnostic-positive but not optimizer-ready.
  Projection preserved all trust limits and recovered one zero-accepted source,
  but accepted evidence still covers only sources `7` and `30`, `2` physical
  pairs, and `1` target. Source `8` is near threshold with best projected
  improvement `0.018752`, so M632 should design a targeted source-8 local shape
  search before any optimizer discussion.
- M630 implements and runs the trust-projected sequence pass. It evaluates
  `7596` candidates on focused sources `0`, `7`, `8`, and `30`, preserves all
  trust limits, accepts `9` projected candidates, and recovers source `30` from
  zero accepted candidates. Source `7` improves from `3` to `5` accepted
  candidates, while sources `0` and `8` remain below the margin threshold. This
  is diagnostic-positive but still source-narrow.
- M629 designs the projected/smoother sequence-shape pass. It specifies a
  focused source filter (`accepted_candidate_count <= 3`, trust-primary best
  failure, no collision near miss), radial projection of raw `delta_sequence`
  into the existing trust limits, and source-level recovery artifacts. M630
  should implement this as another diagnostic-only pass.
- M628 audits M627 and chooses the next branch. The strongest high-count
  near-miss sources already have many accepted candidates, so the diversity
  opportunity is in low/zero accepted trust-primary sources. M628 selects a
  design-only projected/smoother sequence-shape branch focused on sources
  `30`, `7`, `0`, and `8`, while keeping collision-primary sources separate and
  keeping optimizer admission blocked.
- M627 implements and runs the no-training near-miss trust-geometry analyzer on
  M624 candidates. It finds `802` unaccepted-but-useful near-miss candidates
  across `13` source rows: primary failures are mean L2 excess `542`, max L2
  excess `185`, and collision `75`; off-road and spin are `0`. All `13` source
  rows have trust near misses and `4` have collision near misses. This supports
  a projected/smoother candidate-shape audit but does not admit optimizer
  training, PPO, promotion, threshold changes, or trust-region relaxation.
- M626 designs the near-miss trust-geometry analyzer. M627 should filter M624
  unaccepted-but-useful candidates, compute mean/max/delta-delta L2 excess,
  keep collision/off-road/spin flags visible, aggregate by source row, and
  write near-miss candidate/source artifacts. This is still diagnostic-only.
- M625 audits M624. K=7 is useful for stronger candidates but negative for
  source-diversity recovery: accepted sources stay at `6` rows, `5` physical
  pairs, and `4` left seeds. The next signal is near misses: `7` unaccepted rows
  have best margin improvement `>= 0.02`, with `6` blocked by
  `outside_sequence_trust_region` and `1` by collision; `775` trust-blocked
  candidates exceed the margin threshold across `13` source rows. M626 should
  design trust-geometry analysis without relaxing constraints.
- M624 runs the K=3/5/7 low-amplitude sequence diagnostic. It increases
  accepted candidates from `189` to `607` and selected mean margin improvement
  from `0.056784` to `0.068523`, but source-level accepted diversity stays at
  `6` selected rows, `5` physical pairs, and `4` left seeds. K=7 strengthens
  already-accepted source rows but does not solve the source-diversity blocker.
- M623 designs a K=7 low-amplitude sequence diagnostic. M624 should use the
  M616 expanded source table, add `K=7`, add intermediate steer deltas `±0.06`,
  and keep all M621 trust-region and acceptance thresholds unchanged. The run
  remains diagnostic-only and must compare source-level selected/candidate
  diversity against M621 before any optimizer discussion.
- M622 audits M621's `189` accepted candidate rows. They show useful
  candidate-family diversity but not enough source diversity: accepted
  candidates still cover only `5` physical pairs and `4` left seeds, and
  core-boundary evidence is only `2` accepted candidates. Optimizer admission
  remains blocked. M623 should design a longer K=7 low-amplitude diagnostic
  rather than widening trust regions or lowering thresholds.
- M621 formally reruns the tier-aware sequence target miner. It reproduces M617
  selected metrics exactly and writes `accepted_candidate_sequences.csv` with
  `189` accepted candidate rows. Candidate-level family diversity exists
  (decay_pulse `86`, constant_delta `64`, steer_then_brake `22`,
  brake_release_then_steer `17`), but accepted candidates still cover only `5`
  physical pairs and `4` left seeds. M622 should audit before any longer K=7
  diagnostic or optimizer design.
- M620 implements source-tier metadata propagation and
  `accepted_candidate_sequences.csv` in `sequence_target_miner`. A real
  tier-aware smoke on M616 expanded rows reproduces M617's `6` selected
  accepted sequences and exposes `189` accepted candidate rows. Candidate-level
  family diversity exists, but source-level diversity remains narrow: accepted
  candidates still cover only `5` physical pairs and `4` left seeds. Optimizer
  admission remains blocked.
- M619 designs the next no-training sequence diversity step. M617 has `6`
  selected accepted sequences but `189` accepted candidate rows, and accepted
  source-tier interpretation required a manual join to M616. M620 should make
  the sequence miner source-tier and accepted-candidate-set aware before any
  larger search, optimizer design, training, or PPO.
- M618 audits M617 as diagnostic-positive but not optimizer-ready. M617
  increases selected accepted sequences from `1` to `6`, but it still misses
  the pre-registered breadth target: `6 < 8` accepted sequences, `5 < 6`
  physical pairs, `4 < 6` left seeds, and all selected sequences are `K=5`
  `constant_delta` with `+0.08` steer. M619 should design source-tier metadata
  propagation, accepted candidate-set audit, and possibly longer low-amplitude
  sequence families while keeping target thresholds and trust regions intact.
- M617 repeats the unchanged M613 sequence target miner on the M616 expanded
  source table. It evaluates `10440` candidates across `30` source rows and
  selects `6` accepted sequences with mean margin improvement `0.056784` and
  max `0.093048`. This is a clear repeatability improvement over M613's one
  accepted sequence, but it remains diagnostic-only: accepted diversity is `5`
  physical pairs and `4` left seeds, and all selected sequences are `K=5`
  `constant_delta` with `+0.08` steer. M618 should audit before any optimizer
  or training design.
- M616 implements and runs the expanded sequence-source miner. From `33` M609
  source rollout rows it writes `30` expanded rows and `3` rejected rows. The
  expanded set includes all `17` original M609 boundary rows plus `6` near
  boundary and `7` support boundary rows; it covers `27` physical pairs, `15`
  left seeds, `2` surfaces, `2` variants, and `3` targets with max pair
  dominance `0.066667`. Diversity passes, so M617 can rerun the unchanged
  sequence target miner on this expanded source table.
- M615 designs source expansion before another sequence miner run. Lowering
  `min_capability_z_distance` is not useful on the current two-variant source
  pool: z thresholds from `0.10` down to `0.00` deduplicate to the same `33`
  rows. The next implementation should instead tier M609 `source_rollouts.csv`
  by baseline boundary window: core collision/margin `<= 0.50`, near margin
  `<= 1.00`, and support margin `<= 2.00`. This can expand from `17` original
  boundary rows to up to `30` rollout-backed rows while preserving deterministic
  wrong/delayed hidden provenance. Sequence target acceptance thresholds remain
  unchanged.
- M614 audits the M613 result and admits source expansion design. M613 produced
  a real sequence-target signal, but accepted diversity is only one source row,
  one physical pair, one left seed, one surface, one variant, and one target.
  Optimizer admission, training, PPO, and promotion remain blocked; M615 should
  expand source diversity and repeatability criteria before another sequence
  mining run.
- M613 implements and runs sequence target mining on M609 boundary rows. It
  evaluates `5916` sequence candidates and selects one accepted `K=5`
  `constant_delta` sequence on a fresh delayed braking row, with margin
  improvement `0.020817`. `sequence_target_corpus.npz` is written, but accepted
  diversity is one source/physical pair/surface/variant/target, so it is
  diagnostic-only and cannot feed training.
- M612 designs the sequence target miner: structured `K in {3, 5}` action
  prefixes, per-step action L2 `<= 0.10`, sequence mean L2 `<= 0.08`, sequence
  max L2 `<= 0.10`, unchanged `0.02` margin / `0.05` risk acceptance
  thresholds, and diagnostic-only artifacts.
- M611 audits M610 and classifies the blocker as first-action locality / myopia,
  not source-boundary distance or horizon length. A single first-action
  override followed by unchanged BC5660 is too weak; M612 should design
  bounded 3-5 step action-sequence targets before any training.
- M610 runs diagnostic target search on the `17` M609 boundary rows using an
  `80`-step continuation horizon. It evaluates `3332` first-action candidates
  and accepts `0` targets. Max candidate improvement is `0.017662`, and max
  trust-region improvement is `0.015549`, still below the `0.02` threshold.
  No target corpus is written; sequence/trajectory target audit is admitted.
- M609 implements and runs the boundary-conditioned source miner. It selects
  `33` reconstructable full-pool source rows, admits `17` near-boundary rows,
  and rejects `16` far rows. The `17` rows cover `16` physical pairs, `9` left
  seeds, `2` surfaces, `2` variants, and `3` targets, but miss the desired
  `24`-row threshold, so `diversity_pass=false`. A limited diagnostic target
  search is admitted; training and optimizer admission remain blocked.
- M608 designs the next source-screen step. M609 should scan the full
  reconstructable M604 source pool, initially `wrong_matched_history` and
  `delayed_history`, run an `80`-step normal baseline continuation, and admit
  rows only when collision, margin `<= 0.50`, or high baseline risk makes them
  boundary/risk candidates. M609 should write source-rollouts, boundary-source
  rows, rejected/far rows, and summary artifacts, but no action targets.
- M607 audits M606 and classifies the zero-accepted result as primarily
  source-row boundary-distance. Baseline source margins are mostly far from the
  short-horizon boundary: median `2.729036`, mean `2.833607`, only `3 / 23`
  below zero, and `4 / 23` at or below `0.5`. A diagnostic `0.015` margin
  threshold would still accept no rows. The next branch is boundary/risk-
  conditioned source re-mining design; actor training and PPO remain blocked.
- M606 implements and runs the grounded target miner. It selects `23` unique
  wrong/delayed source rows from M604 and evaluates `4508` first-action
  candidate rollouts. Result: `0` accepted targets, `23` unaccepted rows, max
  candidate margin/risk improvement `0.014268`, and max trust-region
  improvement `0.013046`. No target corpus is written; actor training, PPO,
  promotion, and direct use of belief-only gaps as labels remain blocked.
- M605 designs the grounding step. M606 should run a local first-action search
  around M604 candidates and accept targets only when they improve simulator
  margin/risk within a small action trust region. Actor training, PPO, and
  direct use of belief-only gaps as labels remain blocked.
- M604 implements and runs the no-update evaluator. It joins `6776` rows and
  finds `262` real-history `belief_only_gap` candidates: fresh shuffled `84`,
  fresh delayed `24`, fresh wrong-matched `8`, OOD shuffled `77`, OOD
  wrong-matched `49`, and OOD delayed `20`. These are grounding candidates,
  not action labels.
- M603 designs that guarded action-coupling branch. The immediate next step is
  an exact no-update evaluator that joins M591 action distances and M601
  capability z-distances, then classifies `belief_only_gap` rows before any
  grounded recovery/boundary target mining or optimizer step.
- M602 audits M601. The supported diagnosis is belief-level signal without
  action-use proof: hidden capability movement exists, but M591 still shows
  real wrong/delayed histories barely move action. M602 admits a design-only
  guarded action-coupling objective and keeps actor training, PPO, promotion,
  and ungrounded action separation blocked.
- M601 implements and runs that probe. Fresh has `329` pairs and OOD has `287`
  pairs. `shuffled_history` passes the admission rule on both surfaces, and
  `wrong_matched_history` passes on OOD with mean z-distance `0.140707` and
  `49 / 287` above-threshold rows. Fresh `wrong_matched_history` is mixed
  (`0.099081`, `8 / 329`), and `delayed_history` is weak on both surfaces.
  This admits M602 audit but not actor training, PPO, promotion, or a driver
  improvement claim.
- M600 designs the capability-belief intervention probe. It uses the M598
  capability head on recurrent `next_hidden` under M591-style hidden variants
  and measures z-scored capability prediction distance. Actor fine-tuning is
  admitted only if real-history variants show capability movement; random
  hidden remains diagnostic only.
- M599 audits M598: the frozen BC5660 hidden state contains learnable
  capability signal, but this is not driver improvement and does not show action
  use. Before actor fine-tuning, M600 should test whether the learned capability
  belief changes under wrong/delayed hidden interventions on M586/M591-style
  surfaces.
- M598 implements and runs the frozen-actor capability-head smoke. Train/val
  regression losses drop `79%` / `67%`, train rank loss drops `32%`, validation
  rank loss also decreases, action-anchor MSE is `0`, actor parameters are
  unchanged, and no checkpoint is promoted. This proves data/objective signal,
  not driver improvement.
- M597 designs the first capability repair objective smoke as a frozen-actor,
  head-only test. It trains only `CapabilityHead` on `base_next_hidden_seq` and
  M596 capability targets, uses regression plus pair ranking losses, and treats
  action anchor as a near-zero drift metric. It explicitly makes no driver
  improvement or self-ID claim.
- M596 exports train and validation BC capability corpora. Train has `112`
  rows and `240` pair rows; validation has `58` rows and `240` pair rows. Both
  preserve `student_obs_dim = 72`, `target_dim = 3`,
  `labels_enter_actor_input = false`, and
  `contains_privileged_actor_inputs = false`. M597 should design the first
  objective smoke before any training.
- M595 implements `bc_capability_corpus`: closed-loop BC5660 corpus export with
  P0 observations, base action anchors, future-response target labels,
  recurrent hidden diagnostics, and same-corpus matched-current pair rows. A
  real 3-seed smoke produced `24` rows and `18` pair rows with
  `labels_enter_actor_input = false`. M596 should export train/validation
  corpora; still no repair training or promotion.
- M594 designs the real capability corpus/runner. It chooses closed-loop
  BC5660 rollout collection so P0 observation, recurrent hidden diagnostics,
  base action anchor, and future-response label correspond to the same state.
  Matched-current ranking rows should be mined from the new corpus rather than
  blindly reusing M586 indices. M595 should implement exporter and tests only.
- M593 implements the capability-repair objective utilities:
  training-only capability head, z-score regression, matched-current ranking,
  action BC/anchor losses, and metadata preservation. Synthetic tests pass, but
  no real checkpoint training was run. M594 must design the corpus/runner that
  aligns future-response labels with rollout hidden states before smoke
  training.
- M592 selects the first repair direction: train hidden state with
  training-only future-response/capability targets, using regression plus
  matched-current ranking and an action anchor. It explicitly rejects
  ungrounded action separation, PPO continuation, promotion, and any actor
  input expansion. M593 should implement objective infrastructure and tests
  only.
- M591 implements and runs the hidden-action sensitivity probe. Fusion weights
  have non-trivial hidden/context/interaction shares for BC5660/5661/5662, but
  BC5660 real wrong/delayed hidden states remain action-equivalent on fresh and
  OOD matched-current surfaces. Fresh wrong/delayed mean action distances are
  `0.000552` / `0.001658`; OOD values are `0.000764` / `0.001218`. Zero-current
  stays dominant. The next step is hidden-use objective/corpus design, not
  PPO, promotion, or outcome rollout.
- M590 designs the hidden-action sensitivity probe needed after M589. M591
  should measure fusion weight chunk norms, real wrong/delayed hidden variants,
  shuffled/scaled/random hidden variants, positive observation controls, and
  hidden-distance/action-distance correlations. Random-hidden movement is
  diagnostic only and must not be treated as self-ID proof.
- M589 audits the scaled L3 BC objective after the negative M587
  wrong/delayed-history action screen. The `human_view_online_gru` actor has a
  structural hidden-to-action path, but the BC optimizer trains only recurrent
  one-step teacher-action MSE and the corpus lacks matched-current
  history-contrast targets. M590 should design a hidden-action sensitivity
  probe before any repair training.
- M520 valid-offset projected replay produced only a margin-only projected
  history signal: `1` source-narrow wrong-history proof candidate and `0` event
  rows.
- M524 found stronger natural history-value diagnostics: `480` L0 diagnostic
  candidates and `18` obstacle-completion event rows across natural M497/M487
  surfaces.
- M526 audited those event rows as source-diverse diagnostic evidence:
  `18` obstacle-completion drops across `2` surfaces, `5` probe seeds, and
  `2` targets, with projected event rows excluded.
- M527 defined the matched baseline family: L0 feedforward/current observation,
  L1 one-step command-response annotation, L2 finite command-response window,
  and L3 online GRU recurrent belief.
- M528 implemented explicit baseline metadata and an L0 smoke path while
  preserving the P0 no-wheel/no-oracle actor contract.
- M529 pre-registered the staged matched-baseline evaluation ladder so later
  L0/L2/L3 comparisons use shared budgets, seeds, configs, artifacts, and
  holdout discipline.
- M530 repeated the L0 current-observation smoke on seeds `3530` and `3531`.
  Both completed and wrote stable `L0_current_observation` plus
  `P0_human_view_no_wheel_no_oracle` metadata. The smoke returns are not
  interpreted as baseline evidence.
- M531 added machine-checkable L0/L2/L3 short-train configs with shared PPO
  budget, seed, task distribution, and P0 contract checks. L2 is the only config
  with `history_length = 4`; L0 and L3 use `history_length = 1`.
- M532 ran all three short-train configs on seed `3530`. L0 and L2 terminated
  in all eval episodes, while L3 had lower termination rate (`0.6`) and higher
  return on this one seed. This is route/artifact evidence only; repeat seeds
  and natural history-value surface evals are still required.
- M533 repeated the frozen configs on seeds `3531` and `3532`. Across seeds
  `3530`-`3532`, L3 has the best average return/termination (`45.7765`/`0.6`),
  L2 is second (`39.9082`/`0.6667`), and L0 is third (`27.3016`/`0.8667`).
  This is preliminary route evidence only; natural history-value surface eval is
  the next evidence layer.
- M534 designed that next layer. Existing recurrent-only tail gates are not
  enough for matched L0/L2/L3 evaluation, so the next tool must reconstruct
  natural source states with M399, replay L0/L2/L3 from the same frozen
  state/history, keep M526 rows as public diagnostics, and exclude projected
  surfaces from natural claims.
- M535 implemented that evaluator. It supports L0 current-frame replay, L2
  current-first stacked history replay, and L3 hidden construction from source
  observation prefixes. Focused tests pass, and a real 2-pair short-reveal smoke
  produced `6` outcome rows with `0` invalid rows.
- M536 scaled the evaluator to all nine matched short-train checkpoints on
  small short-reveal and warmup natural subsets. It produced `279` valid outcome
  rows total with one diagnosed short-reveal source-tail miss. L0/L2/L3 tied on
  success/completion/collision, while L3 had the best mean clearance margin.
  This is still route evidence only.
- M537 ran the full public frozen-source natural-surface matrix across M497
  short/warmup and M487 near/late splits. It produced `20196` valid outcome rows
  and no metadata or actor-contract failures. L3 leads aggregate success
  (`0.851901`), collision rate (`0.148099`), and mean clearance margin
  (`1.654668`) versus both L0 and L2, and is best on every per-surface success
  and margin table. The public M526 event overlay also favors L3, but this is
  still public diagnostic evidence rather than private generalization or
  checkpoint promotion.
- M538 converted the M537 result into exact paired source-key deltas. The join
  is complete (`6732` triplets, `0` incomplete). L3-L0 is robust across all
  surfaces and all three training seeds, with paired success delta `+0.020351`
  and margin delta `+0.144301`. L3-L2 is aggregate-positive and positive on all
  surfaces, but not seed-uniform: seed `3531` favors L2 with success delta
  `-0.013815` and margin delta `-0.143703`.
- M539 diagnoses the seed `3531` L2-over-L3 counterexample. It is broad rather
  than an event artifact: all four surfaces, all target groups, and all
  tail-offset groups have negative mean L3-L2 margin deltas. The `31` success
  regressions are all `L2 obstacle_completed -> L3 collision`, and non-event
  rows carry the success/collision regression. L3 seed `3531` has a systematic
  first-action shift relative to L2, so the next step should address matched
  training variance rather than promote L3 from public diagnostics.
- M540 designs the matched training-variance escalation. It keeps L2 as a real
  finite-window baseline, defines a staged ladder starting with 4096-step
  matched configs, separates L3-vs-L0 from L3-vs-L2 pass rules, and requires
  public paired diagnostics before any fresh-holdout claim. It also corrects the
  current lineage config paths to `configs/ppo_m531_matched_*_short_train.json`.
- M541 implements the matched 4096-step variance config family:
  `configs/ppo_m541_matched_l0_variance_4096.json`,
  `configs/ppo_m541_matched_l2_variance_4096.json`, and
  `configs/ppo_m541_matched_l3_variance_4096.json`. Tests verify valid P0
  history-baseline metadata, shared task distribution, and that the new configs
  differ from M531 only in `total_steps` and default seed. No training or
  promotion was performed.
- M542 runs the seed-3540 4096-step route pilot for all three levels. All runs
  complete and write valid P0 history-baseline metadata. Route eval strongly
  favors L2 (`return_mean = 77.992665`, `termination_rate = 0.2`) over L0
  (`20.334296`, `1.0`) and L3 (`21.645978`, `1.0`), but this is route evidence
  only and not a stable ranking or promotion claim.
- M543 evaluates those M542 checkpoints on the public M497/M487 frozen-source
  natural surfaces. L2 dominates aggregate success/margin (`0.866310`/`1.777833`)
  while L3 regresses below L0 (`0.670677`/`0.984809`). Paired L3-L2 deltas are
  strongly negative: success `-0.195633`, collision `+0.190731`, margin
  `-0.793024`. L3 is worst on every public surface, so the current recurrent
  recipe should be audited before expanding seeds.
- M544 audits that L3 regression. There is no P0 contract violation: config and
  metadata differences are the intended finite-window versus online-GRU fields.
  The issue is training behavior: L3 peaks early (`best_return = 52.598733` at
  step `1792`) but collapses late (`last4_return_mean = 23.259713`, final return
  `15.771149`), while L2 improves late. M543 failures include `423` L2-completed
  to L3-collision pairs and a large L3-L2 action shift. The next step is L3
  recurrent recipe repair design, not more runs of the same L3 setup.
- M545 designs that repair path. It keeps P0 inputs and L2 as a serious
  finite-window baseline, allows only L3 optimization/checkpoint-selection
  controls, pre-registers interval-checkpoint selection from route artifacts
  before public eval, and admits three M546 diagnostic configs: `fast_select`,
  `lr1e4`, and `lr5e5`. This is design-only and does not promote a checkpoint.
- M546 implements those L3-only repair configs and tests. `fast_select` adds
  `checkpoint_interval_steps = 512` while keeping `learning_rate = 0.0003`;
  `lr1e4` and `lr5e5` lower recurrent update aggressiveness and set
  `max_grad_norm = 0.25`. Tests verify all three keep the M541 L3 environment
  exactly and differ only by approved optimization/checkpoint-selection fields.
- M547 runs the three M546 repair configs and evaluates all saved interval/final
  checkpoints under the route-only selection rule. The result is negative:
  `0/27` saved checkpoints pass route health, and the best saved checkpoint
  (`fast_select` step `1024`) has return `22.941196` with termination `1.0`.
  The useful diagnostic is that all three variants peak in training at step
  `1792`, but that step is unsaved by the 512-step checkpoint cadence.
- M548 adds update-aligned `checkpoint_interval_steps = 256` configs for the
  same three L3 repair variants. Tests verify the only PPO difference from each
  M546 parent is checkpoint cadence, so every PPO update step can be saved and
  evaluated in the next route pilot.
- M549 runs that update-aligned route pilot. The previously missed step `1792`
  is now saved but fails deterministic route health for all variants. One saved
  checkpoint passes the M545 route-health gate: `fast_select_ckpt256` step
  `2816`, with route return `27.858686`, termination `0.8`, and mean clearance
  margin `0.594595`. Public frozen-source diagnostics are now admitted for that
  selected checkpoint, but no checkpoint is promoted.
- M550 runs those public diagnostics. M549 selected L3 improves over original
  M542 L3 (`success +0.053922`, margin `+0.164015`), but it still regresses
  against L0 (`success -0.076203`, margin `-0.235235`) and L2 (`success
  -0.141711`, margin `-0.629009`) on the same public surfaces. The next step is
  to redesign route-health screening, not to promote or matched-repeat this
  checkpoint.
- M551 redesigns the route-health screen. Route-screen v2 must use at least
  `64` public-neutral route episodes, include L0/L2/original-L3 references, and
  rank checkpoints by obstacle success, clearance margin, collision rate, then
  return. A candidate below L0 on route-screen v2 is blocked from public
  frozen-source eval.
- M552 retrospectively validates route-screen v2. It uses level-matched env
  configs so L2 keeps `history_length = 4`, evaluates 64 public-neutral route
  episodes, and rejects M549 selected L3 before public eval: M549 success
  `0.046875` is below L0 `0.062500` and far below L2 `0.609375`.
- M553 implements route-screen v2 as reusable harness infrastructure:
  `autodrift.route_screen_v2` supports named checkpoint policies, per-policy
  level-matched env configs, required L0/L2 references, candidate selection,
  `episodes.csv`, `policy_summary.csv`, `summary.json`, and explicit
  `uses_public_frozen_source_rows = false` provenance. The runner reproduces
  the M552 rejection of M549 selected L3.
- M554 designs the next L3 recurrent repair branch under route-screen v2. It
  freezes P0/env/task boundaries, restricts repair v2 to PPO stability controls,
  and admits exactly three small L3-only variants for M555:
  `epoch1_clip01`, `longseq_epoch1`, and `lowentropy_epoch1`.
- M555 implements those three L3-only configs and tests. All preserve the M548
  L3 env/task distribution, P0 actor contract, and update-aligned
  `checkpoint_interval_steps = 256`; differences are limited to M554-approved
  PPO stability controls.
- M556 trains those configs and evaluates `43` L3 interval/final candidates
  with route-screen v2. No checkpoint is admitted. `35/43` candidates pass L0
  binary success, but `0/43` pass L0 clearance margin and `0/43` pass collision
  tolerance. Public frozen-source diagnostics are blocked.
- M557 classifies that failure as collision-dominated after a small binary
  success gain. The best candidate converts `5` L0 collisions to completions,
  but also converts `7` L0 non-collision terminations and `3` L0 completions to
  collisions. Versus L2, `38` L2 completions become L3 collisions.
- M558 designs a targeted repair branch using existing obstacle collision and
  clearance-margin reward terms. It keeps P0 inputs, rotates the next
  route-screen v2 selection seed to `16560`, and admits exactly three M559
  reward variants.
- M559 implements those three reward configs and tests. P0 L3 actor inputs and
  M555 `epoch1_clip01` PPO controls are unchanged; only M558-approved obstacle
  reward fields differ.
- M560 trains the reward configs and evaluates `51` L3 candidates on fresh
  route-screen seed `16560`. No candidate is admitted. All candidates pass L0
  binary success, but all fail L0 margin and collision tolerance, so public
  frozen-source diagnostics remain blocked.
- M561 designs the pivot from failed from-scratch L3 PPO branches to L2-to-L3
  distillation. L2 remains a training-only teacher using finite-window P0
  observations, while the deployable L3 student remains P0 online-GRU with
  current 72-value frames and recurrent hidden state. The next admitted step is
  M562: export `student_obs_seq`, `teacher_action_seq`, done masks, and terminal
  diagnostics on non-public route seeds without training or promotion.
- M562 implements that exporter in `autodrift.l2_teacher_corpus`. The real
  smoke export on non-public seeds `18000:18001` wrote `116` transitions with
  `student_obs_seq` shape `(116, 72)`, `teacher_action_seq` shape `(116, 3)`,
  done/start masks, and terminal diagnostics. The NPZ does not contain
  `teacher_obs_stack_seq`, and `uses_public_frozen_source_rows = false`.
- M563 implements offline L3 behavior cloning in
  `autodrift.l3_behavior_cloning`. A smoke run trained on the M562 corpus and
  validated on seeds `18128:18129`. It reduced train action MSE from `0.083840`
  to `0.0000705` and validation action MSE from `0.076715` to `0.000131` while
  saving a P0 `L3_online_gru` checkpoint with `ppo_used = false` and
  `promoted = false`. Closed-loop route behavior is still untested.
- M564 runs route-screen v2 on fresh selection seed `17560`. M563_BC is
  admitted for public diagnostics: success `0.656250`, collision `0.343750`,
  and mean margin `0.770803`, matching L2 success/collision and remaining
  within L2 margin tolerance while strongly outperforming L0. No checkpoint is
  promoted from this route-screen smoke.
- M565 evaluates M563_BC on the four public frozen-source natural surfaces from
  M543/M550. M563_BC matches L2 success/collision (`0.866310` / `0.133690`),
  has nearly identical mean margin (`1.770749` vs L2 `1.777833`), and strongly
  repairs original M542 L3 (`+0.195633` paired success, `+0.785940` paired
  margin). This is public diagnostic evidence only; no checkpoint is promoted.
- M566 designs the scaled BC repeat. It freezes the L2-teacher/L3-student
  boundary, assigns fresh non-public train seeds `18200-18327`, validation seeds
  `18328-18391`, BC optimizer seeds `5660/5661/5662`, and fresh route-screen
  seed `18560`. PPO remains blocked until scaled BC route/generalization
  evidence is stable.
- M567 exports the scaled corpora. Train has `128` episodes and `8024`
  transitions; validation has `64` episodes and `3900` transitions. Both corpora
  keep `student_obs_seq` at 72 dimensions, store `teacher_action_seq` plus
  done/start masks, omit `teacher_obs_stack_seq`, and report
  `uses_public_frozen_source_rows = false`.
- M568 trains scaled BC seeds `5660`, `5661`, and `5662`. All three improve
  train and validation MSE and save clean P0 L3 checkpoints. Final validation
  MSEs are `0.00003675`, `0.00000855`, and `0.00001963`; all metadata reports
  `L3_online_gru`, `P0_human_view_no_wheel_no_oracle`, `ppo_used = false`, and
  `promoted = false`.
- M569 runs route-screen v2 with fresh seed `18560`. All three scaled BC seeds
  clear route-screen, match L2 success/collision (`0.671875` / `0.328125`), and
  beat L2 mean margin slightly. `BC5660` is selected with mean margin
  `0.950870`, ahead of L2 `0.936128`. No checkpoint is promoted.
- M570 evaluates selected `BC5660` on the four public frozen-source natural
  surfaces used by M543/M550/M565. It matches L2 success/collision
  (`0.866310` / `0.133690`), has slightly higher mean margin (`1.782199`
  versus L2 `1.777833`), and strongly repairs original M542 L3 (`+0.195633`
  paired success, `-0.190731` paired collision, `+0.797390` paired margin).
  This is public diagnostic evidence only; no checkpoint is promoted.
- M571 designs the next fresh route/generalization gate. M572 will evaluate
  `BC5660` versus L0/L2 on `256` fresh non-public route seeds
  `19560..19815`, excluding prior route-screen seeds `15560`, `16560`,
  `17560`, and `18560`. It must remain L0-safe and L2-competitive under
  pre-registered success/margin/collision tolerances, with no PPO, no public-row
  tuning, and no promotion.
- M572 runs that fresh route/generalization gate. `BC5660` passes: success
  `0.625000`, collision `0.375000`, and mean margin `1.064947`, slightly ahead
  of L2 (`0.621094`, `0.378906`, `1.049135`) and far ahead of L0
  (`0.050781`, `0.867188`, `-0.044399`). The run used `256` fresh seeds
  `19560..19815`, `uses_public_frozen_source_rows=false`, and performs no
  training or promotion.
- M573 designs the next moderate-OOD route layer. M574 should add eval-only
  config copies for L0/L2/L3 with shared wider speed, friction, obstacle, and
  hidden-vehicle randomization ranges while preserving each level's history
  contract. The later M575 OOD eval should use fresh seeds `20560..20815` and
  relaxed L2 competitiveness tolerances (`0.05` success/collision and `0.10`
  margin) because the distribution is deliberately shifted.
- M574 implements those eval-only configs:
  `configs/eval_m574_moderate_ood_l0.json`,
  `configs/eval_m574_moderate_ood_l2.json`, and
  `configs/eval_m574_moderate_ood_l3.json`. Focused tests verify exact parent
  PPO sections, approved OOD env deltas, shared distribution except
  `history_length`, and route-screen loader compatibility. No evaluation,
  training, or promotion is performed.
- M575 runs the moderate-OOD route gate on fresh seeds `20560..20815`.
  `BC5660` passes: success `0.628906`, collision `0.371094`, return
  `61.804108`, and mean margin `1.042773`, matching L2 success/collision and
  slightly improving L2 return/margin (`61.796892`, `1.036858`). This is a
  positive OOD diagnostic but still not promotion evidence by itself.
- M576 audits M570/M572/M575. BC5660 is L2-competitive on public natural
  surfaces, fresh route seeds, and moderate-OOD route seeds, but this is still a
  selected single-BC-seed result. Immediate promotion and PPO remain blocked;
  the next escalation is a BC seed-family repeat for seeds `5660`, `5661`, and
  `5662` on fresh same-distribution and moderate-OOD route blocks.
- M577 designs that repeat. M578 will evaluate `BC5660`, `BC5661`, and
  `BC5662` on fresh route seeds `21560..21815` using M541 configs. M579 will
  use fresh OOD seeds `22560..22815` and M574 configs only if M578 passes.
  Family pass requires BC5660 plus at least one other BC seed to remain L0-safe
  and L2-competitive; no promotion is allowed.
- M578 runs the BC seed-family fresh route repeat. All three BC seeds pass:
  `BC5660` success/collision/margin `0.675781` / `0.324219` / `0.992939`,
  `BC5661` `0.671875` / `0.328125` / `0.982097`, and `BC5662` `0.675781` /
  `0.324219` / `0.991177`, versus L2 `0.671875` / `0.328125` / `0.978128`.
  No checkpoint is promoted.
- M579 runs the BC seed-family moderate-OOD repeat. All three BC seeds pass:
  `BC5660` success/collision/margin `0.582031` / `0.417969` / `0.921253`,
  `BC5661` `0.574219` / `0.425781` / `0.914780`, and `BC5662` `0.582031` /
  `0.417969` / `0.920871`, versus L2 `0.574219` / `0.425781` / `0.913270`.
  This strengthens the scaled BC family but still does not prove recurrent
  dependence.
- M580 audits the BC family evidence. The route/OOD transfer claim is now
  strong, but recurrent self-ID is not yet proven. The next layer should use
  checkpoint ablations such as `reset_recurrent_state`,
  `zero_current_response`, and `zero_action_history` to test whether the L3
  online-GRU policy actually depends on recurrent command-response history.
- M581 designs that ablation layer. M582 will compare `BC5660` normal against
  `reset_recurrent_state`, `zero_current_response`, `zero_action_history`, and
  `zero_all_response` on fresh seeds `23560..23815`. Meaningful degradation is
  pre-registered as success drop `>= 0.02`, margin drop `>= 0.05`, or collision
  increase `>= 0.02`.
- M582 runs that fresh-route ablation. Normal `BC5660` scores success/collision/
  margin `0.691406` / `0.308594` / `1.068165`. `zero_action_history` reaches
  meaningful margin degradation (`0.052959`), while `zero_current_response` and
  `zero_all_response` reach strong margin degradation (`0.144810`) plus success
  drop and collision increase `0.027344`. `reset_recurrent_state` is only weak
  (`0.007812` success drop, `0.017594` margin drop), so the next step is the
  M583 moderate-OOD repeat rather than promotion or PPO.
- M583 repeats the ablation on moderate-OOD seeds `24560..24815`. Normal
  `BC5660` scores success/collision/margin `0.621094` / `0.378906` /
  `0.985368`. `zero_current_response` and `zero_all_response` again degrade
  behavior, with success drop and collision increase `0.035156` and margin drop
  `0.100321`. `reset_recurrent_state` and `zero_action_history` remain below
  meaningful thresholds on OOD. The next step is an audit to separate
  current-response dependence from accumulated hidden-state self-ID claims.
- M584 audits M582/M583. The supported claim is that BC5660 uses the current
  deployable ego/IMU-like response stream on both fresh route and moderate-OOD
  distributions. The unsupported claim is accumulated online-GRU hidden belief:
  reset-hidden remains weak in both runs. M584 blocks promotion/PPO and admits a
  sharper history-intervention design using delayed or wrong recurrent history.
- M585 designs that sharper gate. Existing tooling is sufficient: use
  `matched_current_response_ambiguity` to mine source-diverse pairs,
  `matched_history_intervention_gate` for action-level screening, and
  `persistent_wrong_history_intervention_gate` for outcome degradation. M586
  will mine BC5660 pair surfaces on fresh route seeds `25560..25563` and
  moderate-OOD seeds `25660..25663`.
- M586 mines those pair surfaces. Both pass the pre-registered source-diversity
  thresholds: fresh route yields `666` accepted pairs, `192` physical pairs,
  `15` left steps, and `14` obstacle buckets; moderate-OOD yields `403`
  accepted pairs, `152` physical pairs, `14` left steps, and `14` obstacle
  buckets. M587 action screening is admitted; no checkpoint is promoted.
- M587 runs action-level delayed/wrong-history screens on both M586 surfaces.
  The result is negative for hidden-history action sensitivity:
  `wrong_matched_history` and `delayed_history` have `0` above-threshold rows on
  both fresh and OOD surfaces. The screen is valid because positive controls are
  strong: `zero_current_response` is above threshold for all rows on both
  surfaces, and `zero_action_history` is often above threshold. Persistent
  outcome rollout is blocked until M588 audits the negative result.
- M588 audits that negative result. The screen is live, so the likely issue is
  not tool failure: BC5660 appears to transfer L2 behavior through current
  response, previous commands, and scene context without materially using
  accumulated hidden state. M588 blocks the persistent outcome gate and admits a
  BC hidden-use/objective audit before any repair training.

## Near-Term Rule

Do not treat reset-hidden diagnostics, M528 smoke return, route eval, or
M537-M570 public diagnostics as private generalization evidence. The L2-to-L3
distillation branch must keep L2 finite-window stacks training-only. Offline BC
may optimize teacher-action MSE only; any checkpoint still needs route-screen v2
before public frozen-source eval. M550 remains public diagnostic evidence and
cannot support a private generalization claim. Any later promotion requires
proof retention, generalization retention, behavior retention, no contract
violation, and clear lineage.

## Sensor Profile Policy

Keep raw wheel, `v_parallel`, steering torque, suspension, and similar channels
as separate profile experiments only. Do not promote them into the main actor
without passing the same frozen-recipe proof gates as P0.

Suggested future profile ladder:

| Profile | Inputs |
| --- | --- |
| P0 | current no-wheel human-view baseline |
| P1 | commands + actuator feedback + `ax/ay/yaw_rate` + scene |
| P2 | P1 + steering torque / EPS current |
| P3 | P2 + raw four-wheel `R omega` |
| P4 | P3 + roll/pitch/vertical acceleration |
| P5 | P4 + suspension / wheel travel |

Every profile must use the same gate sequence: probe, frozen PPO recipe,
matched-current wrong-history, reset/zero-current ablation, and outcome boundary
proof. Do not tune PPO separately for one profile and compare it directly.
