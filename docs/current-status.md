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
m905-v4-pair-delta-public-base-integration-readiness-design
```

M904 closed the objective effect-size branch and opened public-base integration
readiness. M905 must design compatibility and objective-only transfer gates
while keeping M568 diagnostic base separate from the current public-gate base.

## Recent Evidence Line

- M904 synthesizes M895-M903. Raw objective-only movement is repeatable,
  proof-safe versus M568, and margin-positive on public proof, m121-style fresh,
  and robust challenge-family diagnostics without success/termination
  regression. Unsupported claims remain success improvement, PPO, direct
  promotion, and public-base integration. Next branch: public-base integration
  readiness.
- M903 passes robust challenge-family benchmarks. Near-threshold robust keeps
  raw success `0.843750` and termination `0.156250`, with clearance deltas
  about `+0.00370`. Late high-energy robust keeps raw success `0.781250` and
  termination `0.218750`, with clearance deltas about `+0.00337`. Seed-delta
  audit shows no success flips. This is a second margin-only public
  generalization positive, not PPO or promotion.
- M902 designs M903 challenge-family benchmark on
  `m451_challenge_near_threshold_robust_zero_relvel` and
  `m451_challenge_late_high_energy_robust_zero_relvel`, `128` episodes each.
  Raw candidates must retain success/termination within `0.01` on each family,
  keep nonnegative clearance on each family, and achieve combined clearance
  delta at least `+0.001`. No PPO or promotion.
- M901 audits M900 as margin-only fresh evidence. Raw candidates retained
  success/termination and exceeded the fresh clearance threshold, but seed-delta
  audit showed no success flips. The next route is a second scenario-family
  design using robust near-threshold and late high-energy challenge configs,
  not public-base integration or PPO.
- M900 runs the no-training fresh benchmark on seeds `9705`/`9706`, `256`
  episodes each. Raw candidates retain success `0.761719` and termination
  `0.238281` versus M568 and pass the clearance threshold: `m886_raw`
  `+0.003236`, `m891_raw` `+0.003250`. Alpha `0.1` movement is about
  `+0.000425`. Seed-delta audit shows no success flips, so this is a
  margin-only fresh public diagnostic pass, not promotion or PPO admission.
- M899 designs M900 fresh/generalization benchmark: seeds `9705`/`9706`,
  `256` episodes each, `configs/m121_human_view_zero_obstacle_relvel.json`,
  and seed-delta audit. Raw candidates must retain success within `-0.005`,
  termination within `+0.005`, and clearance delta at least `+0.002` versus
  M568 to count as useful fresh-distribution movement. No PPO or promotion.
- M898 audits M897 as proof-safe raw scaling evidence and routes to fresh
  generalization design. Supported: raw candidates preserve exact/replay/
  behavior-retention gates while producing about `10x` the alpha `0.1`
  clearance movement. Unsupported: success improvement, broad generalization,
  public-base integration, and PPO safety.
- M897 passes the controlled raw-candidate scaling gate. Both raw candidates
  reconstruct `247/247` exact rows, first replay gates pass `4/4`, full replay
  gates pass `12/12`, and behavior seeds `9505`/`9506` retain success `0.8125`
  and termination `0.1875`. Raw candidates increase clearance by about
  `+0.00488` versus M568, roughly `10x` alpha `0.1`, but still do not improve
  success and slightly reduce return. PPO and promotion remain blocked.
- M896 designs controlled raw-candidate scaling gates. M897 must first run
  exact objective recheck for both raw candidates, then the sensitive replay
  gates `M183/M170` and `M267/M264`, then all six replay/proof surfaces only if
  first gates pass. Behavior seeds `9505`/`9506` are allowed only after full
  replay passes. PPO and promotion remain blocked.
- M895 audits effect size from existing M886/M891/M889/M893 artifacts. Accepted
  alpha `0.1` is repeatable and proof-safe but too small for performance claims:
  action L2 mean is about `1.2e-4`, success and termination are retention ties,
  and behavior clearance movement is about `+0.00049`. Raw candidates are about
  `10x` larger in action movement and keep negative exact holdout deltas, but
  they have no replay evidence and require controlled scaling gates first.
- M894 synthesizes M885-M893 and opens `v4_pair_delta_objective_effect_size`.
  The supported claim is narrow: the no-PPO enriched pair-delta objective-only
  update repeats across two optimizer/minibatch seeds, selects alpha `0.1` both
  times, and preserves exact/replay/behavior proof gates versus M568 for both
  candidates. PPO, promotion, generalization claims, and meaningful driver
  improvement remain blocked because the movement is tiny and all gates are
  public workflow artifacts.
- M893 passes exact recheck, six replay/proof surfaces, and behavior seeds
  `9505`/`9506` for M891 `alpha_0_1` versus M568. Exact recheck reconstructs
  `247/247` rows; all six replay surfaces pass with zero candidate success-drop
  regression. Behavior retention stays at success `0.8125` and termination
  `0.1875`, with aggregate clearance delta `+0.0004909103515290392`. Together
  with M889, this supports two-seed proof retention for the no-PPO
  objective-only recipe, not promotion or PPO safety.
- M892 audits M891 as a clean fresh-seed repeat of the M886 no-PPO
  objective-only result. Both seeds reconstruct `247/247` rows, find `7`
  nonzero exact-admissible interpolation candidates, and select alpha `0.1` as
  the best exact-admissible candidate. This supports objective-level
  repeatability only; replay retention for the M891 repeat is routed to M893.
- M891 repeats the M886 objective-only recipe with seed `10887` and otherwise
  identical settings. It reconstructs `247/247` rows, keeps actor input and M761
  residual head unchanged, and again finds `7` nonzero exact-admissible alphas.
  Best alpha is `0.1` with train weighted-loss delta
  `-0.00008399784564971924`. This supports objective seed repeatability but not
  replay retention for the repeat yet.
- M890 audits M889 as clean but single-seed proof evidence. The supported claim
  is limited to M886 seed-10886 `alpha_0_1` preserving M568-relative exact,
  replay, and behavior-retention gates. Unsupported claims include repeat
  stability, meaningful driver improvement, generalization, PPO safety, and
  public-base promotion. Next is an identical no-PPO objective-only repeat with
  seed `10887`.
- M889 passes the exact/replay/behavior proof-gate stack for M886
  `alpha_0_1.pt` versus M568. Exact recheck reconstructs `247/247` rows and
  keeps exact deltas nonpositive. All six replay/proof surfaces pass with zero
  candidate success-drop regression. Behavior seeds `9505` and `9506` retain
  success `0.8125` and termination `0.1875`; aggregate clearance margin delta
  is `+0.0004892324201435372`. This is proof retention from the M568 diagnostic
  branch, not public-base promotion.
- M888 designs the M889 replay/proof gate stack for
  `runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt`
  versus M568. The order is exact objective recheck, first replay gates
  `M183/M170` and `M267/M264`, all six public replay surfaces, then behavior
  seeds `9505` and `9506` only if replay passes. `alpha_0_05.pt` is the
  fallback. PPO and promotion remain blocked.
- M887 audits the M886 objective-only result as clean exact-objective evidence
  and admits replay/proof gate design. It selects
  `runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt`
  because it is the largest exact-admissible interpolation, has the best train
  objective delta, and keeps exact holdout deltas nonpositive. `alpha_0_05.pt`
  is the fallback. This is still not replay success, PPO admission, or
  promotion.
- M886 implements the first no-PPO enriched pair-delta objective-only probe. It
  reconstructs all `247/247` actor-state tensor rows with `0` missing rows,
  keeps M761 residual-head parameters unchanged, trains only actor-coupling
  parameters for `32` Adam steps, and finds `7` nonzero exact-admissible
  interpolation candidates. The best exact-admissible alpha is `0.1` with train
  weighted-loss delta `-0.00008386037042074079`; raw train delta is
  `-0.0008391377425962521`, but raw is not accepted directly. This is exact
  objective evidence only, not closed-loop replay evidence or promotion.
- M885 designs the first no-PPO objective-only probe. It limits the update to a
  narrow actor-coupling scope, requires exact M883 objective metrics before and
  after update, uses interpolation from base to raw candidate, rejects exact
  holdout regression, and explicitly forbids PPO or promotion.
- M884 synthesizes M875-M883 and promotes to the next branch:
  `v4_pair_delta_objective_probe`. The previous branch successfully transformed
  raw M873 pair-delta rows into deduped splits, enriched action targets, and
  exact no-update objective sanity with full tensor reconstruction. Remaining
  caveats are public-gate overfit risk, no new source holdout, degradation-only
  eval/new-signature splits, and 78055 still absent from new accepted rows.
- M883 implements exact no-update enriched pair-delta objective sanity and
  passes. It reconstructs all `247` expected actor-state rows with `0` missing
  tensors and `0` snapshot rejections, computes finite improvement/degradation
  preference losses, and leaves actor parameters unchanged. This is still not an
  update result, so the next step is M884 branch synthesis before objective-only
  probe work.
- M882 designs exact no-update pair-delta objective sanity. Improvement rows
  should prefer the override action over the normal action under the same
  normal observation/hidden state; degradation rows should prefer the normal
  action over the harmful override. The design requires deterministic actor
  observation and recurrent-hidden reconstruction before logprob losses can be
  computed. No update or PPO is admitted.
- M881 audits M880 enriched corpus as complete enough for design-only objective
  work. The action target blocker is resolved, but the next design must define
  how implementation will recover actor observations and recurrent hidden
  states for exact log-probability objectives. New source holdout remains
  unavailable and the 78055 caveat remains, so actor update, PPO, promotion,
  and learned self-ID claims are still blocked.
- M880 implements no-training target-action enrichment and passes. It enriches
  `247` dedup rows plus all four split files, with `494/494` identity-unique
  joins, zero missing joins, zero ambiguous joins, preserved split labels,
  preserved duplicate metadata, and restored target action fields. The result
  is corpus infrastructure only: new source holdout is still unavailable and
  the 78055 caveat remains, so objective training, actor update, PPO, and
  promotion remain blocked pending M881 audit.
- M879 designs the no-training target-action enrichment route. The important
  correction is that M877's `existing_m867_or_m870` rows recover action targets
  from M867 sequence rows, while `new_m873` rows recover action targets from
  M873 sequence rows. A live identity-key check gives `247/247` unique sequence
  matches, but this is still corpus infrastructure only. Objective training,
  actor update, PPO, and promotion remain blocked until M880 implements and
  audits the enriched artifacts.
- M878 audits M877 transformed corpus as structurally cleaner but not ready for
  loss design. M877 fixed duplicate-axis pressure and split coverage, but
  deduplicated accepted rows do not carry the action target fields needed for a
  future objective, such as normal first action, right first action, and first
  override action. Those fields exist in M873 sequence rows, so the next step is
  no-training target enrichment by joining M877 dedup signatures back to M873
  sequence rows. Objective training, PPO, and promotion remain blocked.
- M877 implements the no-training dedup/resplit transformation. It reduces the
  corpus from `273` raw accepted rows to `247` deduplicated rows and collapses
  new M873 evidence from `39` rows to `13` closed-loop signatures, reducing new
  duplicate factor from `3.0` to `1.0`. The transformed objective train split
  has `124` rows including `8` new rows, eval has `22` rows including `2` new
  rows, source holdout has `98` existing-only rows, and new-signature holdout
  has `3` rows. The `78055` caveat remains and new source holdout is
  unavailable, so objective training, PPO, and promotion remain blocked pending
  audit.
- M876 designs a no-training corpus transformation before objective design. The
  plan deduplicates by closed-loop signature, explicitly excludes retarget-axis
  labels from the dedup key, preserves duplicate metadata, separates existing
  M867/M870 evidence from new M873 evidence, and writes purpose-specific
  objective train/eval/source-holdout plus new-signature holdout splits. The
  design keeps the `78055` caveat visible and makes objective training, PPO,
  and promotion remain blocked until the transformed corpus is implemented and
  audited.
- M875 audits M873 corpus objective readiness and rejects direct objective
  design from the raw split. M873 remains a positive corpus result, but the
  `39` new accepted rows compress to `13` unique closed-loop signatures, all
  have `retarget_delta = 0.0`, and axis labels create a `3.0x` duplication
  factor. The current split is not objective-ready: train has `28` rows and
  `0` new M873 rows, eval has `16` rows all from new M873 rows, and holdout has
  `12` rows and `0` new M873 rows. The `78055` caveat remains. Objective
  training, PPO, and promotion stay blocked.
- M874 synthesizes M864-M873 and closes the
  `v4_pair_delta_boundary_expansion` branch. The branch supports that
  no-training generated boundary data can be converted into real pair-delta
  outcome evidence, and that M873's boundary-preserving normal-window search
  materially improves coverage to `56` balanced rows across `4` left seeds. It
  does not support learned self-ID or promotion, and the `78055` caveat remains.
  Public-gate overfit risk is moderate because all evidence is still corpus
  construction on public surfaces. Objective training, PPO, and promotion
  remain blocked until the new objective-readiness branch audits duplicate
  pressure, source split quality, and caveats.
- M873 implements the no-training boundary-preserving refresh and passes the
  registered coverage gates. Normal-boundary search produces `48`
  accepted-window candidates across all `3` missing seeds and all `3` retarget
  axes. Pair-delta replay over `48` candidates produces `864` sequence rows and
  `39` new accepted pair-delta rows. Combined with existing accepted rows, the
  balanced corpus reaches `56` rows across `4` left seeds, `11` source groups,
  `8` fault families, `27` fault pairs, `2` directions, and `2` axis pairs;
  seed/direction/axis dominance gates pass. Caveat: new accepted rows cover
  `78048` and `78057` but not `78055`, so this is not a complete missing-seed
  solution and not a promotion claim. Actor and M761 checksums are unchanged;
  no training, PPO, or promotion occurs. M874 must synthesize before more work.
- M872 designs a no-training two-stage refresh for missing seeds. Stage A must
  run normal-only boundary search, include the original target point, classify
  wide-safe vs collision/negative vs accepted-window rows, and refine adjacent
  brackets until normal branch satisfies `normal_success == true`,
  `normal_collision == false`, and `0.0 <= normal_margin <= 0.03`. Stage B may
  run pair-delta sequence replay only on accepted normal-window candidates.
  Thresholds remain unchanged, component controls stay diagnostic-only, and
  objective training, PPO, actor mutation, M761 mutation, and promotion remain
  blocked. M873 is admitted as the final targeted implementation before branch
  synthesis.
- M871 audits M870 as clean but not objective-ready. Construction worked and
  targeted all missing seeds, but accepted-row failure is explained by normal
  branch window miss: `0/1728` retarget replay rows satisfy the accepted normal
  branch condition, while `1152` rows are already colliding and `576` rows are
  too safe (`normal_margin > 0.03`). The largest missing-seed margin deltas are
  real diagnostics but occur on non-primary rows, so they cannot become
  objective data. Objective training, PPO, and promotion remain blocked. M872
  should design boundary-preserving missing-seed refresh.
- M870 implements the no-training accepted pair-delta coverage expansion.
  Construction gates pass with `24` target weak-seed rows across missing seeds
  `78048`, `78055`, and `78057`, `96` retarget candidates, and `1728`
  pair-delta sequence replay rows. Actor and M761 checksums are unchanged; no
  training, PPO, or promotion occurs. The result remains source-limited:
  `new_accepted_pair_delta_rows` is `0`, accepted coverage remains the
  original `234` rows, and the balanced corpus has `40` rows but only `2` left
  seeds. Existing accepted rows rebalance better on direction and axis
  dominance (`0.525` each), but missing-seed retargets mostly produce high
  margin deltas only after the normal branch is already colliding, so they
  cannot count as accepted primary pair-delta evidence. M871 should audit
  before more implementation.
- M869 designs a no-training accepted pair-delta coverage expansion route. The
  next implementation should first compute a stronger direction/axis-aware
  rebalance diagnostic over existing M867 accepted rows, then target missing
  accepted seeds `78048`, `78055`, and `78057` by selecting their strongest
  weak pair-delta rows and applying bounded obstacle retargeting plus extended
  pair-delta replay (`hold_steps` `6,8,10`, epsilon L2 `0.075,0.10,0.125`).
  Primary gates require at least `60` accepted rows, `36` balanced rows, at
  least `3` left seeds, at least `2` directions and axis pairs, and dominance
  limits on seed, direction, and axis-pair. Component controls remain
  diagnostic-only; objective training, PPO, and promotion stay blocked.
- M868 audits M867 as real pair-delta outcome evidence but not objective-ready.
  Candidate selection passed, so pair construction is not the active blocker.
  The blocker is accepted outcome sensitivity concentration: accepted rows
  appear only for left seeds `78058` and `78050`; seeds `78048`, `78055`, and
  `78057` have no flips and max absolute margin deltas below `0.003`. The
  balanced corpus has `32` rows but only `2` left seeds, direction dominance
  `0.75`, and axis-pair dominance `0.96875`. M869 should design targeted
  accepted-coverage expansion; objective training, PPO, and promotion remain
  blocked.
- M867 implements the no-training generated-boundary pair-delta refresh.
  Candidate selection passes design gates with `1332` raw pair candidates,
  `118` selected replay pairs, `27` left source groups, `5` left seeds, and
  `9` left fault families. Actual pair-delta replay produces real outcome
  signal: `1416` pair-delta sequence rows, `234` accepted pair-delta rows, and
  `97` success/collision flips. The result is still source-limited because
  the balanced corpus has only `32` rows across `2` left seeds, with direction
  dominance `0.75` and axis-pair dominance `0.96875`. Actor and M761 checksums
  are unchanged; no training, PPO, or promotion occurs. M868 must audit before
  objective design.
- M866 designs the source-aware no-training pair-delta refresh over M864
  combined generated-boundary rows. M867 should convert pairability projection
  into actual sequence outcome evidence by replaying only pair-delta directions
  first, then selecting a balanced pair-delta corpus. Component controls cannot
  satisfy primary gates. Objective training, PPO, actor mutation, M761 mutation,
  and promotion remain blocked.
- M865 audits M864 as clean sparse-useful generated-boundary coverage. Strong
  gates still fail and the surface is axis-concentrated, but sparse gates pass
  with `59` combined boundary-new-to-M844 rows, `27` source groups, `5` seeds,
  `9` fault families, and `365` primary pairability projections. The next route
  is a limited pair-delta refresh design that converts pairability projections
  into actual sequence outcome evidence. PPO, objective training, actor
  mutation, M761 mutation, and promotion remain blocked.
- M864 implements no-training generated-boundary refinement from M860 brackets.
  It selects `25` bracket seeds, including `13` no-M860-boundary brackets,
  reconstructs all `25` snapshots, and produces `42` accepted refined rows.
  Combined M860+M864 coverage reaches `59` boundary-new-to-M844 rows across
  `27` source groups, `5` seeds, and `9` fault families; primary pairability
  projection rises to `365`. This passes sparse generated-boundary gate but not
  strong gate because rows/source groups/seeds remain below strong thresholds.
  Pair-delta replay and PPO remain blocked until audit.
- M863 synthesizes the M853-M862 branch and continues it into one
  generated-boundary refinement implementation. Supported claims are limited to
  no-training data construction: source targeting and snapshot reconstruction
  work, trace diagnostics identify all-safe-wide blocker, closer obstacle
  generation opens `17` new boundary rows, and M860 contains `13`
  refinement-ready wide/negative bracket groups. Unsupported claims remain
  pair-delta outcome evidence, objective-ready self-ID corpus, PPO admission,
  learned policy improvement, or promotion.
- M862 designs the no-training generated-boundary refinement route. The next
  implementation should select M860 same-source same-axis generated
  wide/negative brackets, prioritize groups with no M860 accepted boundary row,
  reconstruct the original M825 temporal snapshot, and replay bounded
  bisection/refinement between endpoint parameters. It must report both
  refined-only accepted rows and combined M860+refined coverage. Pairability
  remains a cheap projection only; pair-delta replay, objective training, PPO,
  actor mutation, M761 mutation, and promotion remain blocked. However, the
  branch has reached the 10-milestone synthesis cadence, so M863 must synthesize
  M853-M862 before another implementation.
- M861 audits M860 as source-limited but refinement-ready. Sparse gates still
  fail (`17 < 32` accepted generated boundary rows, `38 < 40` primary
  pairability rows, `4 < 5` seeds), so pair-delta replay is still blocked. But
  M860 generated replay contains `13` same-source same-axis groups with
  wide/negative brackets and no accepted boundary row, plus `17` groups with
  accepted rows. The next route is therefore no-training generated-boundary
  refinement, not direct pair-delta replay or broad source generation.
- M860 implements the no-training closer obstacle/source generation runner. It
  generates `660` candidate plans from M857 traces across `44` primary source
  groups, `8` seeds, and `9` fault families, reconstructs all requested
  snapshots, and preserves actor/M761 checksums. The run opens `17` accepted
  boundary-new-to-M844 rows and `38` primary pairability projection rows. This
  improves over M857's zero generated boundary rows but remains below sparse
  gate (`32` accepted rows and `40` pairability rows). Accepted rows come only
  from `all_safe_closer_obstacle`; `all_collision_safer_side` and
  half-width-only generation contribute zero accepted rows. M860 is
  `v4_closer_obstacle_source_generation_source_limited`, not pair-delta
  outcome evidence and not PPO admission.
- M859 designs the closer obstacle/source generation route. All-safe-wide
  source axes should generate bounded closer-obstacle extrapolations from their
  closest wide-safe trace rows, with combined tightening for very wide margins.
  All-collision axes should use safer-side candidates and source-step
  neighborhood shifts. M860 may only run normal closed-loop generated candidate
  replay and must not run pair-delta sequence replay.
- M858 audits M857 as valid no-training trace evidence and confirms the primary
  blocker is scenario sampling: boundary-new-to-M844 rows are mostly too
  safe/wide under the tested grids. Recovered controls validate the trace
  runner but cannot count as new-source evidence. The next route is closer
  obstacle/source generation, not wider same-axis replay, objective training, or
  PPO.
- M857 implements the no-training trace diagnostic. It traces `44` primary
  boundary-new-to-M844 sources and `8` recovered controls, reconstructs all
  `52` snapshots, writes `1924` bracket trace rows, and classifies `132`
  primary source-axis rows. The primary cause is `all_safe_wide`:
  `114/132 = 0.863636`; `18/132 = 0.136364` are
  `all_collision_or_negative`; accepted extended boundary axes are `0`. This
  rules out simple same-source axis widening as the best next route and points
  toward closer obstacle/source generation after audit.
- M856 designs a full parameter/outcome trace diagnostic for
  boundary-new-to-M844 source axes. The next implementation must preserve every
  initial and extended grid evaluation over obstacle lateral offset, timing, and
  half-width, then classify no-bracket causes such as all-safe wide margins,
  all-collision traces, extended bracket discovery, mixed/no-adjacent brackets,
  ambiguous/non-finite results, or reconstruction errors. The result is allowed
  to choose a no-training next route only; it is not pair-delta outcome
  evidence and does not admit PPO or promotion.
- M855 audits M854 as a clean source-limited boundary expansion rather than a
  contract failure. Target selection and snapshot reconstruction work, and M854
  expands beyond the M850 active pair-delta source groups. But accepted
  boundary rows are still all from existing M844 boundary sources, while
  boundary-new-to-M844 targets produce only `no_collision_safe_bracket`
  failures. Because M854 did not persist full initial/expansion evaluation
  traces for rejected axes, the next step is trace-first no-bracket diagnosis
  rather than pair-delta replay or PPO.
- M854 implements the no-training pair-delta boundary expansion. Target
  selection is broad: `61` source groups, `12` seeds, and `9` fault families,
  with all `61` requested snapshots reconstructed. Actor and M761 residual-head
  checksums are unchanged and no training, PPO, promotion, or pair-delta
  sequence replay occurs. Boundary bracketing remains source-limited:
  `73` expanded rows produce only `32` accepted successful non-collision
  low-margin rows, covering `17` source groups, `4` seeds, `7` fault families,
  and all `3` boundary axes. Pairability projection is close to sparse-useful
  but below gate with `77` primary rows. The key blocker is that all accepted
  rows are `existing_boundary_recovered`; the `boundary_new_to_m844` targets
  produced only `no_collision_safe_bracket` failures.
- M853 designs the first step of the `v4_pair_delta_boundary_expansion` branch.
  It targets the M850 coverage gap by selecting sources absent from the M850
  balanced pair-delta left side, prioritizing absent seeds and missing fault
  families such as brake/drive authority drops, front/rear lateral authority
  drops, steering fault, and combined fault. M853 explicitly blocks PPO,
  promotion, actor/residual training, and pair-delta sequence replay until
  boundary coverage is audited.
- M806 designs the next no-training boundary-axis expansion. It preserves the
  M804 closed-loop replay discipline but adds obstacle lateral offset,
  source-step neighborhood replay, fault activation micro-sweeps, fault
  severity micro-sweeps, and bracketed distance/width bisection. M806 also adds
  axis-balance gates: at least `3` retarget axes, max axis dominance `0.60`,
  and at least `10` accepted rows from at least `3` axes, while keeping the
  primary `0.0 <= margin <= 0.00005`, alpha `0.2`, source-dominance, checksum,
  no-training, no-PPO, and no-promotion constraints unchanged.
- M805 audits M804 as a clean geometry-only diagnostic. M804 proves the primary
  low-margin window is reachable by closed-loop public geometry retargeting and
  preserves intervention sensitivity, but it is not source-diverse or
  axis-diverse enough for the active-steer guard corpus. M805 rejects
  calibration, PPO, promotion, and threshold weakening, and routes next to
  source-diverse boundary-axis expansion design.
- M804 implements and runs the no-training boundary-window retarget tool.
  Closed-loop retargeting creates `252` accepted primary-window rows with
  margins from `0.000004953` to `0.000046264`, no reconstruction failures, and
  unchanged actor/residual checksums. However every accepted row comes from
  `obstacle_half_width` retargeting; obstacle-distance retargeting produces
  `0` accepted rows. Accepted rows cover only `3` seeds, have max seed
  dominance `0.428571`, and max fault-pair dominance `0.714286`, so M804 is
  classified as `v4_low_margin_boundary_window_geometry_only_diagnostic`, not a
  source-diverse guard pass. Intervention branches on accepted rows still all
  collide, so the local proof mechanism is present but too source/axis
  concentrated for calibration.
- M803 designs the next no-training boundary-window retarget step. It fixes the
  target anchors from M801: `60` collision rows at alpha `0.2` with margins from
  `-0.000572` to `-0.000173` across `2` seeds and `5` source indices, plus the
  nearest `24` successful non-collision diagnostic rows with margins from
  `0.005243` to `0.005768` from `1` seed and `4` source indices. M803 requires
  M804 to rerun closed-loop candidates under public retarget axes such as
  obstacle width, obstacle timing, fault activation step, fault severity, and
  neighboring source step. It keeps alpha `0.2`, the primary
  `0.0 <= margin <= 0.00005` gate, source-diversity requirements, checksum
  invariants, and no-training/no-PPO/no-promotion constraints unchanged.
- M802 audits M801 as a clean no-training diagnostic-band-only result. M801 is
  a broad coverage positive but not a primary low-margin corpus pass: positives
  increased to `4825` across `108` seeds and `18` fault-family pairs, while the
  primary successful non-collision low-margin band `<= 0.00005` remains empty
  and all rows through `<= 0.001` are collisions. M802 classifies the blocker
  as a boundary-window miss and rejects both threshold relaxation and another
  generic broad wave. M803 should design targeted collision/success boundary
  retargeting.
- M801 implements the low-margin refresh config and selector, then runs the
  no-training data pipeline. The source wave expands to `49152` matched pairs
  and `3552` reset-only rows. Sequence intervention exports `4825`
  outcome-critical positives across `108` seeds and `18` fault-family pairs
  with sentinel false positives `0`. Reference residual replay reconstructs
  `4805/4825` rows with actor checksum unchanged and no training/PPO, but raw
  residual alpha `0.2` has normal success `0.987513` and collision `0.012487`.
  The low-margin selector finds `76` collision-free successful diagnostic rows
  at margin `<= 0.2`, but `0` rows in the primary `<= 0.00005` band and `0`
  through `<= 0.001`; all rows at margin `<= 0.001` are collisions. Result
  class is `v4_low_margin_guard_refresh_diagnostic_band_only`. M802 audit is
  required before retargeting or calibration.
- M800 designs the required low-margin corpus refresh after M799 accepted the
  M798 source-diversity blocker. A direct M795 parent replay margin-distribution
  check shows alpha `0.2` normal rows have only `12` rows at margin
  `<= 0.00005`, still `12` at `<= 0.00010`, and only `36` through
  `<= 0.10000`, all from one seed, before the next distinct rows jump to about
  `0.201 m`. M800 therefore rejects a threshold-only fix and requires M801 to
  run a no-training boundary-retargeted source wave, reference residual replay,
  and strict low-margin guard export with at least `80` accepted rows, `8`
  seeds, `8` source indices, `4` fault-family pairs, max seed dominance
  `0.25`, no actor/residual mutation, no PPO, and no promotion.
- M799 audits M798 as a valid process-positive blocker. The low-margin guard
  corpus has only `12` rows and all are variants of one public active source:
  `seed 77025`, `source_index 12`, `step 24`, one fault-family pair, with
  normal margin `+0.000003618`. Diversity is `1` unique seed, `1` unique source
  index, `1` unique fault-family pair, and max seed dominance `1.0`, versus
  required `8`, `8`, `4`, and `0.25`. The audit rejects weakening the
  diversity thresholds or tuning only that active source. It routes next to
  `m800-v4-low-margin-source-diverse-corpus-refresh-design`; residual
  calibration, PPO, and promotion remain blocked.
- M798 extends `v4_normal_margin_residual_calibration.py` with
  `--objective-mode active_steer_guard`, source-diverse low-margin guard row
  selection, low-margin guard artifacts, separability artifacts, and focused
  tests. The run stops before training because the M795 parent replay contains
  only `12` low-margin guard rows, all from the same public active source
  (`seed 77025`, `source_index 12`, `step 24`, one fault-family pair).
  Diversity is `1` unique seed, `1` unique source index, `1` unique
  fault-family pair, and max seed dominance `1.0`, versus required `8`, `8`,
  `4`, and `0.25`. No optimizer, closed-loop replay, PPO, or promotion occurs;
  actor and residual checksums remain unchanged. Result class is
  `v4_active_steer_guard_low_margin_corpus_blocked`.
- M797 designs a no-PPO active steer guard calibration after M795's near miss.
  The design keeps the M568 actor and M761 residual head frozen, keeps the M795
  steer/brake gate with fixed-zero throttle, and adds a stronger workflow:
  source-diverse low-margin guard-row selection, supervised gate separability
  probe, active-steer feasibility projection, then gap retention under the
  guard. It requires exact alpha `0.2` closed-loop gates, M786/M780 references,
  active/source-diverse low-margin steering safety, and steer selectivity
  before any candidate claim. It also adds explicit stop conditions for
  low-margin corpus block and deployable feature separation failure. M798 is
  admitted as implementation diagnostic only; PPO and promotion remain blocked.
- M796 audits M795 as a clean near-miss negative. M795 is not a candidate and
  does not justify PPO because active-source margin and steer selectivity fail.
  However, alpha `0.2` is collision-free and reaches the strong gap reference,
  so the branch is not exhausted. The audit concludes that the next design must
  make active/source-diverse low-margin steering safety lexicographic before
  gap optimization, rather than simply tuning the same objective coefficients.
  M797 is admitted as design-only; PPO and promotion remain blocked.
- M795 extends `v4_normal_margin_residual_calibration.py` with
  `--objective-mode steer_attributed_gate`, a 2146-parameter
  `SteerAttributedResidualGate` that learns steer/brake gates and fixes
  throttle residual to zero, plus focused tests and component gate artifacts.
  The no-PPO run reconstructs `2640/2652` rows, writes `21120` replay rows and
  `10560` objective rows, and confirms M568 actor and M761 residual-head
  checksums unchanged. Result class is
  `v4_steer_attributed_calibration_component_collapse`: alpha `0.2` passes
  strict normal retention and reaches gap mean `0.044080`, slightly above the
  M780 alpha `0.125` gap reference, but active-source margin is only
  `+0.000003618`, below the M786 alpha `0.15` active-margin reference
  `+0.000028246`. Gate evidence explains the miss: active normal steer gate is
  `0.668225`, active intervention steer gate is `0.665187`, so active steer
  contrast is negative instead of selective. M795 is a clean negative and
  admits M796 audit only.
- M794 designs the next no-PPO residual calibration probe around M792's
  component attribution. The design keeps the M568 actor and M761 residual head
  frozen and adds only a deployable-feature
  `SteerAttributedResidualGate(feature) -> [g_steer, g_brake]`, with throttle
  fixed to zero in the primary mode because M792 found no throttle role. The
  objective makes high residual retention the default, applies
  steering-specific suppression to low-normal-margin normal rows and the active
  source, retains steering on intervention-sensitive rows, retains brake as a
  useful-only component, and adds a steer contrast term between low-margin
  normal and intervention rows. Candidate rules keep the M786 alpha `0.15`
  active-margin and gap references plus the M780 alpha `0.125` strong-gap
  reference, and require component selectivity to avoid another scalar/vector
  collapse. M795 is admitted as implementation diagnostic only; PPO and
  promotion remain blocked.
- M793 audits M792 as a clean attribution-only result, not an actionable mask
  or promotion result. M792 preserves no-training invariants, reconstructs
  `2640/2652` rows, and reports no actor or residual-head mutation. The audit
  accepts the main component finding: steering residual is both useful and
  harmful, because it carries intervention gap but also drives the active-source
  alpha `0.2` normal collision; brake is useful-only and throttle is inactive
  on this diagnostic. M793 blocks generic vector-gate continuation, PPO, and
  promotion. It selects a new design-only blocker: steer-attributed
  normal-boundary residual calibration that can suppress harmful steering
  residual on low-normal-margin branches while retaining steering and brake
  contribution where intervention separation is needed.
- M792 adds `src/autodrift/v4_residual_component_sensitivity.py` and focused
  tests, then runs the no-training fixed-mask component sensitivity probe over
  the M773 broader source-holdout corpus. It reconstructs `2640/2652` rows with
  `0` metadata misses and the same `12` unsupported `command_shift_obs`
  rejects, writes `168960` replay rows, `84480` objective rows, `384`
  active-source rows, and confirms the M568 actor and M761 residual-head
  checksums unchanged. No optimizer, PPO, or promotion is used. Result class is
  `v4_residual_component_sensitivity_attribution_found`: no fixed mask is
  actionable, but component roles are identifiable. Steer is both useful and
  harmful: at alpha `0.2`, `steer_only` reaches gap mean `0.044286` but
  collides on the active source with margin `-0.000049`, while
  `throttle_brake` / no-steer stays safe with margin `+0.000112` but gap mean
  only `0.042545`. Brake is useful-only with lower gap, and throttle has no
  meaningful role. M792 therefore blocks PPO/promotion and admits M793 audit
  before any steer-specific objective.
- M791 designs a no-training fixed-mask component sensitivity probe for the
  frozen M761 residual head. The design keeps the M568 actor frozen, keeps the
  M761 residual head frozen, and evaluates masks over steer/throttle/brake
  residual components: none, all, single components, no-component ablations,
  and two-component combinations. It uses alpha ladder `0.0`, `0.125`, `0.15`,
  `0.2`, with alpha `0.2` as the primary diagnostic because it has strong
  intervention gap but active-source normal collision. Required outputs include
  per-mask aggregate metrics, active-source metrics, component replay rows, and
  checksums. Actionable evidence requires strict normal retention plus
  better-than-M786 alpha `0.15` gap and active-source margin; attribution
  evidence can also identify harmful/useful components without producing a
  candidate. M792 is admitted as a no-training implementation only; training,
  PPO, and promotion remain blocked.
- M790 audits M789 as a clean negative. The vector-gate implementation
  preserved actor and residual checksums, trained only the 2179-parameter
  calibrator, and wrote complete artifacts, so the negative is not a tooling
  artifact. The audit confirms that M789 did not beat M786 alpha `0.15`: gap
  mean improved by only about `5e-6`, while active-source margin dropped
  slightly from `+0.000028246` to `+0.000027881`; alpha `0.2` still collides on
  the same active source. The decisive failure is component collapse: final
  normal gates are `0.671292/0.671167/0.671190`, final intervention gates are
  `0.684914/0.684800/0.684820`, and `gate_component_std_mean` is only
  `0.000066`. M790 classifies the primary issue as `objective_overfit`: without
  component attribution, the vector gate found another scalar-like moderate
  scaling solution. It blocks PPO/promotion and selects a no-training residual
  component sensitivity design before another vector objective.
- M789 extends the residual calibration tool with `objective_mode=vector_gate`,
  a 3-output steer/throttle/brake gate, component gate metrics, and vector
  candidate classification, then runs the registered no-PPO probe. It
  reconstructs `2640/2652` rows with `0` metadata misses and the same `12`
  unsupported `command_shift_obs` rejects, writes `21120` replay rows and
  `10560` objective rows, and confirms base actor and M761 residual-head
  checksums unchanged. Only the 2179-parameter vector calibrator is trained.
  Result class is `v4_vector_residual_calibration_component_collapse`:
  candidate count is `0`, strong candidate count is `0`, and limited candidate
  count is `0`. Alpha `0.15` passes strict normal retention and has gap mean
  `0.043403`, but active-source margin `+0.000027881` is slightly below M786
  alpha `0.15`'s `+0.000028246`, so it is not a Pareto improvement. Alpha
  `0.2` has gap mean `0.044438` but still collides on the active source with
  margin `-0.000005`. Final component gates are nearly identical (`normal
  0.671292/0.671167/0.671190`, `intervention
  0.684914/0.684800/0.684820`), with `gate_component_std_mean 0.000066`, so
  the vector gate collapsed to scalar-like behavior. M790 must audit before
  further vector objective, PPO, or promotion.
- M788 designs the next no-PPO residual calibration probe after M787 found
  scalar gating too close to alpha scaling. The design keeps the M568 actor
  frozen, keeps the M761 residual head frozen, and replaces scalar `g(feature)`
  with a per-action-dimension vector gate `g(feature) in [0,1]^3` over
  steer/throttle/brake residual components. It preserves the human-view
  deployable input contract and uses terminal margins/source labels only as
  training-time weights and audit metadata. The primary target is alpha `0.2`:
  a strong candidate must pass strict normal retention, keep active-source
  margin at least M786 alpha `0.15`'s `+0.000028`, and reach intervention gap
  mean at least M780 alpha `0.125`'s `0.044047`. A limited candidate must
  Pareto-improve M786 alpha `0.15`; merely reproducing scalar-gate behavior
  does not count. M789 is admitted as implementation diagnostic only, with PPO
  and promotion blocked.
- M787 audits M786 alpha `0.15` as a valid limited diagnostic positive, not a
  promotion-ready scalar-gate breakthrough. M786 is clean and produces one
  candidate: alpha `0.15` passes strict normal retention and the registered gap
  gate with intervention gap mean `0.043397` and active-source margin
  `+0.000028`. However, alpha `0.2` still fails on the same active source
  (`seed 77025`, `source_index 12`) with margin `-0.000005`, and M786 does not
  outperform M780 alpha `0.125` on intervention gap or margin gap. Gate means
  move from M783's near-half `0.499727/0.499986` to `0.670088/0.683384`, which
  is an improvement but still far from the intended high-default `0.85`
  asymmetric behavior. M787 therefore blocks PPO and promotion and pivots from
  scalar gate tuning to vector residual calibration design.
- M786 extends the frozen-actor frozen-residual calibrator with a high-default
  asymmetric scalar-gate objective and runs the registered no-PPO probe. It
  reconstructs `2640/2652` rows with `0` metadata misses and the same `12`
  unsupported `command_shift_obs` rejects, writes `21120` replay rows and
  `10560` objective rows, and confirms base actor and M761 residual-head
  checksums unchanged. Only the 2113-parameter calibrator is trained. Result
  class is `v4_normal_margin_calibration_candidate` with one candidate alpha:
  `0.15`. Alpha `0.15` keeps normal success `1.0`, collision `0.0`, improves
  intervention action gap mean/p10 to `0.043397/0.026649` versus base
  `0.040348/0.025782`, and keeps active source margin `+0.000028` versus M780
  alpha `0.125` reference `+0.000009`. Alpha `0.2` still fails strict normal
  retention with normal success `0.995455`, collision `0.004545`, and the same
  active source margin crossing to `-0.000005`. Final gate means are
  `0.670088` normal and `0.683384` intervention, so M786 partially escapes
  M783's global half-gate but does not achieve the intended high-default
  asymmetric behavior. M787 must audit before repair, PPO, or promotion.
- M785 designs the second scalar-gate calibration probe. It keeps the M568
  actor and M761 residual head frozen, keeps deploy-time inputs clean, and
  changes the objective so high gate is the default rather than a value the
  optimizer must discover from a `0.5` start. The proposed M786 gate initializes
  at about `0.85`, applies strong suppression only to low-margin normal rows
  and the active boundary source, adds high-default priors for non-low-margin
  normal and intervention rows, requires active/outcome intervention gate
  retention, adds a low-margin gate contrast term, and keeps the original
  intervention gap threshold instead of weakening the M783 near miss. M786
  should evaluate alphas `0.0`, `0.125`, `0.15`, `0.2` and explicitly report
  whether the gate escaped global half-scaling.
- M784 audits M783 as a clean negative. The first calibrator successfully fixed
  normal retention, including active source alpha `0.2` margin `+0.000033`,
  while preserving actor and residual-head checksums. It failed because the
  objective found an almost global half-gate solution (`gate_normal_mean
  0.499727`, `gate_intervention_mean 0.499986`) that under-shot intervention
  signal: alpha `0.2` gap lift is `0.002950`, just below the required `+0.003`,
  and candidate count remains `0`. M784 classifies the issue as
  `objective_overfit` / objective misalignment rather than contract or metric
  artifact, and admits only a high-default asymmetric residual gate design. PPO
  and promotion remain blocked.
- M783 adds `src/autodrift/v4_normal_margin_residual_calibration.py` and focused
  tests, then runs the no-PPO calibrator probe. It reconstructs `2640/2652`
  rows with `0` metadata misses and the same `12` unsupported
  `command_shift_obs` rejects, writes `21120` replay rows and `10560` objective
  rows, and confirms base actor and M761 residual-head checksums unchanged.
  Only the 2113-parameter calibrator is trained. Result class is
  `v4_normal_margin_calibration_no_gap_lift`: the calibrator fixes the active
  normal boundary, with alpha `0.2` normal success `1.0`, collision `0.0`, and
  active source margin `+0.000033`, but no alpha passes the intervention gap
  candidate threshold. Final gates are almost global half-scale
  (`gate_normal_mean 0.499727`, `gate_intervention_mean 0.499986`), so alpha
  `0.2` gap mean improves only to `0.043298` versus base `0.040348`, just below
  the required `+0.003` lift. This is a clean negative for the first gate-only
  objective; no PPO or promotion occurred.
- M782 designs a no-PPO normal-margin-aware residual calibration branch. The
  design keeps the M568 actor frozen, keeps the M761 residual head frozen for
  the first probe, and adds a small deployable-feature gate
  `g(feature) in [0, 1]` so executed residual action becomes
  `base_action + alpha * g(feature) * delta_m761`. Terminal margins, source
  labels, and fault metadata may be used only as training-time weights and
  audit metadata, not deploy-time inputs. The objective combines low-margin
  normal suppression, an explicit `seed 77025/source_index 12` boundary guard,
  intervention gap retention, an intervention gate floor, optional
  hard-negative calibration, and parameter regularization. M783 should evaluate
  alpha `0.0`, `0.125`, `0.15`, `0.2`, verify base actor and M761 residual
  checksums remain unchanged, train only calibrator parameters, and keep
  PPO/promotion blocked.
- M781 audits M780 as a limited lower-alpha feasibility positive. Alpha
  `0.125` preserves strict normal retention and improves intervention
  action-gap and margin-gap metrics on M773, showing that M777's alpha `0.2`
  failure was a narrow residual-scale boundary rather than broad normal
  collapse. The audit blocks promotion and PPO because the active normal source
  margin at alpha `0.125` is only about `9e-6`, and alpha `0.15` already
  crosses into collision on the same source. M781 concludes that more dense
  alpha sweeps would only refine the crossing point; the next scientific
  blocker is how to preserve intervention-sensitive residual corrections while
  explicitly protecting low-margin normal branches.
- M780 runs the pre-registered no-training alpha ladder `0.0`, `0.05`, `0.1`,
  `0.125`, `0.15`, `0.175`, `0.2` on the broader M773 corpus. It reconstructs
  `2640/2652` rows with `0` metadata misses and `12` rejected
  `unsupported_variant:command_shift_obs` rows, writes `36960` replay rows and
  `18480` objective rows, and keeps actor checksum unchanged. Alpha `0.125` is
  the best script-level candidate and the only tested alpha that both passes
  strict normal retention and script closed-loop candidate criteria: normal
  success `1.0`, normal collision `0.0`, intervention action gap mean/p10
  `0.044047/0.026886` versus base `0.040348/0.025782`, margin gap mean
  `0.032352` versus base `0.029796`, and outcome sensitivity retention `1.0`.
  Alphas `0.15`, `0.175`, and `0.2` all collide on the same `seed 77025`,
  `source_index 12` source; the source margin crosses from `+0.000009` at
  alpha `0.125` to `-0.000014` at alpha `0.15`. This supports a narrow
  alpha-boundary interpretation, but alpha `0.125` remains a tiny-margin
  diagnostic candidate, not a promotion result. M781 must audit before repair,
  PPO, or promotion.
- M779 designs the pre-registered no-training alpha-boundary probe admitted by
  M778. It fixes inputs to the M568 diagnostic actor, M761 residual head, M773
  positive/contrast rows, and broader scenario config, and registers alpha
  ladder `0.0`, `0.05`, `0.1`, `0.125`, `0.15`, `0.175`, `0.2`. Alpha `0.2`
  remains the failed reference; lower alphas are not a retroactive pass. M780
  must require strict normal retention (`normal_success_rate == 1.0`,
  `normal_collision_rate == 0.0`), intervention action-gap and margin-gap
  improvement over base, outcome sensitivity retention `1.0`, no metadata
  misses, and no actor/training/PPO/promotion mutation. It must stratify `seed
  77025`, `source_index 12`, `step 24` to decide whether M777 is a narrow
  alpha-boundary issue or requires explicit normal-margin retention/objective
  repair.
- M778 audits M777 as mechanism-positive but strict-normal-retention-failed.
  Alpha `0.2` improves intervention action gap mean/p10 from base
  `0.040348/0.025782` to `0.046317/0.027627`, improves margin gap mean from
  `0.029796` to `0.033918`, and keeps outcome sensitivity retention at `1.0`;
  reconstruction is `2640/2652` with `0` metadata misses and no
  actor/training/PPO/promotion mutation. The stricter M775 gate still fails
  because normal success drops to `0.995455` and normal collision rate becomes
  `0.004545`. All 12 normal collision rows come from one unique source (`seed
  77025`, `source_index 12`, `step 24`, `halfshaft_torque_loss_proxy`,
  `drive_authority_drop->rear_lateral_authority_drop`) duplicated across three
  intervention variants and four horizons. The source has only `+0.000124`
  base margin, so alpha `0.2`'s small first-action drift `0.000380` flips it
  to `-0.000062`. M778 classifies this as `behavior_regression` with
  `scenario_sampling_failure` risk, not a metric artifact or contract
  violation, and admits only a pre-registered lower-alpha normal-boundary probe
  design. PPO and promotion remain blocked.
- M777 runs no-PPO residual replay on the broader M773 corpus. It reconstructs
  `2640/2652` rows with `0` metadata misses and `12` rejected
  `unsupported_variant:command_shift_obs` rows, writes `21120` replay rows and
  `10560` objective rows, and keeps actor checksum unchanged. Script-level
  result_class is `v4_residual_closed_loop_replay_candidate` with candidate
  alphas `0.2`, `0.5`, and `1.0`. Alpha `0.2` improves intervention action gap
  mean from base `0.040348` to `0.046317` and margin gap mean from `0.029796`
  to `0.033918`, with outcome sensitivity retention `1.0`. However, M775's
  stricter normal-retention gate fails: alpha `0.2` normal success is
  `0.995455` and normal collision rate is `0.004545`, caused by one unique
  concentrated normal collision source (`seed 77025`, `source_index 12`,
  `halfshaft_torque_loss_proxy`,
  `drive_authority_drop->rear_lateral_authority_drop`). This is
  mechanism-positive but strict-normal-retention-failed; no training, PPO, or
  promotion occurred. M778 must audit before repair, alpha retuning, PPO, or
  promotion.
- M776 performs the required workflow synthesis for the
  `v4_residual_source_holdout_replay` branch after validation blocked direct
  implementation. The synthesis records that M761-M775 support limited
  continuation: the residual mechanism survived public closed-loop replay and
  sparse fresh-holdout replay, and broader M773 source mining materially
  expanded positives from `995` to `2652` while reducing concentration.
  Unresolved risks remain: M773 misses strict broad gates on fault-family-pair
  count (`17 < 18`) and seed dominance (`0.171569 > 0.15`), hard negatives are
  sparse, and current faults remain `current_model_or_proxy` rather than true
  per-wheel physics. Synthesis decision is `continue`, but only to one limited
  no-PPO broader residual replay implementation. PPO, promotion, and broad
  generalization remain blocked.
- M775 designs a limited no-PPO residual replay on the broader M773 corpus. It
  fixes inputs to the M568 actor checkpoint, the M761 residual head, M773
  `2652` positive rows and contrast rows, and
  `configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json`.
  Alpha `0.2` is pre-registered as the primary conservative candidate, with
  `0.5` and `1.0` diagnostic. M776 must report reconstruction, normal
  retention, intervention action-gap and margin-gap changes, seed/fault-family
  pair/variant/horizon stratification, hard-negative sparsity, and
  `current_model_or_proxy` claim boundary. Alpha retuning, training, PPO,
  residual retraining, actor mutation, and promotion remain blocked. Research
  validation required workflow synthesis before another implementation
  milestone, so M775 now admits M776 synthesis rather than direct replay.
- M774 audits M773 as materially supporting the coverage-limited hypothesis.
  M773 is much broader than M767: `2652` positives versus `995`, `49` positive
  seeds versus `25`, `17` positive fault-family pairs versus `13`, and max seed
  dominance `0.171569` versus `0.247236`. Artifact gates are clean: no
  sentinel positives, no missing normal matches, no missing metadata, and no
  mutation/training/PPO flags. The audit preserves caveats: strict broad gates
  still miss by one fault-family pair (`17 < 18`) and seed dominance
  (`0.171569 > 0.15`), and hard negatives remain incomplete (`2134` hard
  negatives for `2652` positives, `872` positives without hard negatives).
  Because ordinary corpus validity is clean and the strict misses are small
  relative to the coverage improvement, M774 admits only limited no-PPO
  residual replay design on M773 with alpha `0.2` primary. PPO, training, and
  promotion remain blocked.
- M773 runs the broader disjoint-seed source wave from M772. Stage 1 reaches
  `24576` matched pairs and `1389` reset-only rows with result_class
  `cross_fault_reset_only`, compared with M767's `390` reset-only rows. Stage 2
  selects `1024` source rows across `63` seeds and `22` source fault-family
  pairs, finding `2652` sequence outcome-critical rows with `0` sentinel false
  positives and result_class `v4_reset_sequence_outcome_positive`. Stage 3
  exports `2652` clean positives, `2652` normal rows, and `2134` hard-negative
  rows with no sentinel positives, no missing normals, no missing metadata, and
  `current_model_or_proxy` claim boundary. This materially supports the
  coverage-limited hypothesis: M767 had `995` positives, `25` positive seeds,
  `13` positive fault-family pairs, and max seed dominance `0.247236`; M773
  has `2652`, `49`, `17`, and `0.171569`. The ordinary positive corpus gate
  passes, but the result is `v4_sequence_outcome_corpus_hard_negative_sparse`.
  Strict M772 broad gates still miss by one pair (`17 < 18`) and by seed
  dominance (`0.171569 > 0.15`). No residual replay, training, PPO, actor
  mutation, or promotion occurred. M774 must audit before choosing limited
  residual replay versus more source-balancing work.
- M772 designs a broader source-holdout wave to test whether sparse
  extreme-scenario coverage is limiting self-ID evidence. It adds
  `configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json`,
  preserves the v4 fault families and pairing rules, increases `max_pairs` from
  `12288` to `24576`, registers fresh seed range `77024..78047`, and sets M773
  `max_source_rows=1024`. The stricter broader gates are `positive_rows >=
  1500`, `unique_positive_seeds >= 40`,
  `unique_positive_fault_family_pairs >= 18`, `max_positive_seed_dominance <=
  0.15`, and `max_positive_fault_family_pair_dominance <= 0.22`. M772 also
  keeps the model-fidelity boundary explicit: wheel blowout, single-corner
  grip collapse, split-mu, stuck caliper, halfshaft, suspension, and per-wheel
  sensor faults are current-model proxies or future high-fidelity faults, not
  true per-wheel physics claims in the single-track model. It admits M773
  broader corpus generation only; residual replay, PPO, training, and promotion
  remain blocked until audit.
- M771 audits M770 as a limited source-holdout mechanism positive. It supports
  the coverage-mining hypothesis: v4 coverage produced source rows, sequence
  outcome rows, residual objective signal, public closed-loop replay, and now a
  limited disjoint-seed holdout replay where primary alpha `0.2` passes while
  normal branch success remains `995/995`. The audit also preserves caveats:
  the holdout corpus is sparse/source-concentrated and intervention collisions
  concentrate in a few seeds/fault pairs. It selects broader source-holdout
  coverage before stronger generalization, PPO, or promotion claims.
- M770 runs limited no-PPO residual replay on the sparse fresh M767 holdout
  corpus. It reconstructs `995/995` rows with `0` metadata misses and `0`
  rejected rows, writes `7960` replay rows and `3980` objective rows, and keeps
  the base actor checksum unchanged. Result class is
  `v4_residual_closed_loop_replay_candidate`: alpha `0.2`, `0.5`, and `1.0`
  pass. Normal branch success is `995/995` and normal collision rate is `0` for
  all alphas. Primary alpha `0.2` raises intervention action gap mean/p10 from
  base `0.043862/0.039491` to `0.050473/0.045717` and margin gap mean from
  `0.026641` to `0.030329`, with normal first-action drift mean/p95
  `0.000553/0.001208`. Base intervention branch already has `20/995`
  collisions; alpha `0.2` has `23/995`, alpha `1.0` has `31/995`, concentrated
  in a few seeds/fault pairs. No optimizer, training, PPO, promotion, or actor
  mutation occurred.
- M769 designs limited no-PPO residual replay on the sparse fresh M767 corpus.
  It fixes the replay inputs to the M761 residual head and M767
  positive/contrast rows, sets alpha `0.2` as the primary conservative holdout
  alpha, keeps `0.5` and `1.0` diagnostic, and requires M770 to preserve
  sparse-holdout caveats. Residual retraining, alpha tuning from holdout
  results, PPO, and checkpoint promotion remain blocked.
- M768 audits M767 as fresh, clean, but sparse. The corpus fails strict
  exporter gates, but passes M766 limited-holdout minimums: `995` positives,
  `25` seeds, `13` fault-family pairs, max seed dominance `0.247236 <= 0.25`,
  no sentinel positives, no missing normal matches, no metadata misses, and
  `current_model_or_proxy` claim boundary. The audit admits only limited
  residual holdout replay design with caveats; it does not admit broad
  generalization, PPO, or promotion.
- M767 runs the disjoint-seed source-holdout pipeline for seed range
  `76512..77023`. Stage 1 produces `390` reset-only rows with result_class
  `cross_fault_reset_only`. Stage 2 selects `441` source rows and finds `995`
  sequence outcome-critical rows with `0` sentinel false positives, but
  result_class is `v4_reset_source_balance_blocked`. Stage 3 exports `995`
  clean positives, `995` normal rows, and `1028` hard-negative rows with no
  missing metadata, no sentinel positives, and no missing normal matches. The
  fresh corpus gate fails as `v4_sequence_outcome_corpus_sparse`: positive rows
  `995 < 1000`, fault-family pairs `13 < 16`, and max seed dominance
  `0.247236 > 0.2`. No residual replay, training, PPO, promotion, or actor
  mutation occurred.
- M766 designs the fresh source-holdout path. Precheck shows existing artifacts
  are not enough for unbiased residual holdout: M752 has `1213` non-sentinel
  outcome positives, M755 exports all `1213`, and there are `0` extra positives
  not used by M761. Although M752 has `60` unused source rows, they are not
  clean positive holdout rows. The design therefore selects a disjoint seed
  range `76512..77023` and admits a no-training fresh v4 source wave,
  reset-source sequence intervention, and corpus export before any residual
  replay.
- M765 audits M764 as a clean public-corpus closed-loop mechanism positive. It
  supports alpha `0.2` as the conservative next candidate and treats alpha
  `1.0` as aggressive diagnostic because its `4/1213` intervention collisions
  are concentrated in seed `76030`, variant `zero_command_obs`, horizons `6/8`,
  and fault pair `front_lateral_authority_drop->combined_fault`. The audit
  records that M755's `assigned_split=heldout` is contaminated for residual
  evaluation because M761 trained on all M755 positives. The next branch must
  design fresh source-holdout replay or fresh source mining, not PPO or
  promotion.
- M764 implements and runs the no-PPO closed-loop residual replay evaluator.
  It reconstructs `1213/1213` source rows with `0` metadata misses and `0`
  rejected rows, writes `9704` replay rows and `4852` objective rows, and keeps
  the base actor checksum unchanged. Result class is
  `v4_residual_closed_loop_replay_candidate`: alpha `0.2`, `0.5`, and `1.0`
  pass closed-loop candidate gates. Normal success is `1213/1213` and normal
  collision rate is `0` for all alphas. Alpha `0.2` raises intervention action
  gap mean/p10 from base `0.041716/0.026395` to `0.047937/0.028594` with normal
  first-action drift mean/p95 `0.000480/0.000939`; alpha `1.0` raises gap to
  `0.074868/0.038011` but creates `4/1213` intervention-branch collisions. No
  optimizer, PPO, promotion, or actor mutation occurred.
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
