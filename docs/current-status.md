# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log; this page should stay short and current.

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

Status: M400 promotes M399 alpha `0.05` as the current public-gate base after
six public replay surfaces and behavior seeds pass. This remains the latest
public-gate base; M487-M525 did not train or promote a checkpoint.

Current blocker:

```text
m526-history-value-event-audit
```

Recent progress: M486-M492 is now closed as an artificial tail-forcing
mechanism branch. It showed that wrong hidden is not ignored, natural
`wrong_tail_once` corrects quickly, hidden-hold can create diagnostic events,
and observer-hidden action replay does not reproduce those events. This is
mechanism evidence, not deployable self-ID proof.

M493 redirects the research path toward natural belief decision windows: tasks
where command-response history forms belief before obstacle reveal, and the
first few post-reveal actions matter before current-response correction can wash
out the history effect.

M494 implements two P0-compatible natural belief configs. Both pass 384-reset
sampling stress with hidden obstacles at reset, late reveal, label diversity,
and friction-step-before-reveal coverage. Short-reveal is harder
(`m399` success `0.515625`), while warm-up capability is easier but still
nontrivial (`m399` success `0.843750`).

M495 passes that source-diversity gate. The combined natural belief
matched-current surface has `5580` accepted pairs across `6` probe seeds,
`3` labels, `3` targets, and `2` configs, with single-seed share `0.175` and
single-label share `0.480`.

M496 passes targeted triage. It exports `294` pairs across `6` probe seeds,
`3` labels, `3` targets, and `2` configs, with single-seed share `0.238`,
single-label share `0.544`, and single-config share `0.605`.

M497 rejects wrong-history event proof on the natural decision-window surface.
Wrong-history has `15` margin-only proof rows and `0` event rows, while
reset/zero-current controls have `472` proof rows and `17` event rows.

M498 finds the blocker: one-shot wrong-history produces a weak closed-loop
trajectory signal. Its trajectory distance mean is `0.055405`, only `5.5%` of
reset-hidden and `12.3%` of zero-current-response. The first action can move,
but the trajectory corrects quickly.

M499 designs that selector: first screen the full M495 surface by
wrong-history first-action distance, then run a short-horizon trajectory probe,
then select a source-diverse target set only if trajectory distance is
materially above the M498 weak baseline.

M500 implements and runs that selector. It finds stronger wrong-history action
trajectory rows (`targeted_trajectory_mean = 0.228203` versus M498 baseline
`0.055405`), but rejects outcome-gate admission: the selected surface has only
`171` rows, single-config share `0.725146`, and high normal margins
(`targeted_normal_margin_min = 0.932188`). This means action sensitivity alone
is not enough; the next surface must also be terminal-boundary sensitive.

M501 redesigns the natural proof path and rejects direct selector repair. In
the M500 candidate table,
`normal_margin <= 0.25` has `325` boundary rows but `0` trajectory-pass rows;
`normal_margin <= 1.0` has only `6` trajectory-pass rows from `1` seed and
`short_reveal` only. The current natural configs do not contain enough rows
that are both action-sensitive and terminal-boundary-sensitive.

M502 implements and sampling-validates two boundary-pressured natural belief
configs. Both pass `384/384` reset sampling with `3` labels and hidden
obstacles at reset. Threshold-score means are `0.229615` and `0.191020`, at or
below the M494 natural configs. Behavior smokes remain non-saturated:
short-reveal `m399` success is `0.78125`; warmup `m399` success is `0.875`.
M399 beats heuristic and random on both configs.

M503 mines matched-current ambiguity surfaces on both M502 configs. After the
initial `12400`-`12600` seed blocks produce only `3` probe seeds, M503 adds
fresh source-diversity blocks `12700`-`12900` without retuning mining
parameters. The combined surface has `5727` accepted pairs across `6` probe
seeds, `3` labels, `3` targets, and `2` configs, with single-seed share
`0.185088`, single-label share `0.479483`, and single-config share `0.507421`.

M504 runs the action-sensitive selector on the M503 surface. It finds a stronger
trajectory signal (`targeted_trajectory_mean = 0.224056`) and acceptable source
shares, but rejects outcome-gate admission: only `195` targeted rows are found,
only `4` have normal margin `<= 0.50`, and only `6` have normal margin
`<= 1.00`.

M505 audits the full M504 candidate table and finds that low-margin rows are
source-diverse, but their wrong-history action perturbations are smaller than
the M500 thresholds. With softer action thresholds, there are `65` rows at
normal margin `<= 0.50`, `216` at `<= 1.00`, and `494` at `<= 2.00`.

M506 implements that terminal-boundary-aware selector. It improves low-margin
coverage versus M504 (`35` rows at margin `<= 0.50`, `76` at `<= 1.00`) and
keeps nonzero trajectory signal (`mean 0.084141`, p90 `0.138282`), but rejects
outcome-gate admission because the source-capped targeted surface has only
`101` rows and label share `0.732673`.

M507 designs the next path: mine low-clearance normal-history anchors first,
then search source-diverse one-shot wrong histories around those anchors. If
natural anchor mining fails, the fallback is obstacle-boundary projection with
strict geometry-change limits and an explicit projection-proof label.

M508 implements and runs that anchor-first miner. It finds many natural
low-margin anchors (`3246`) and real one-shot wrong-history action signal
(`targeted_trajectory_mean = 0.092899`, p90 `0.130059`), but rejects outcome
admission because the source-capped targeted surface has only `104` rows and
single-label share `0.826923`. The audit shows eligible rows collapse into only
`5` obstacle geometry buckets, mostly `unavoidable`.

M509 designs the fallback branch: bounded obstacle-boundary projection from
M508 natural anchors. The branch must preserve natural ego/history state,
relocate only obstacle geometry, report projection magnitudes, and label the
surface as projection proof rather than raw natural-scenario proof.

M510 implements that projection miner. Projection magnitude is small
(`projection_l2_p50 = 1.0`, p90 `1.118034`) and wrong-history action signal is
still present (`targeted_trajectory_mean = 0.089577`), but all selected rows are
classified `unavoidable`, so projected-label diversity fails.

M511 designs the next branch: label-targeted projection mining. The miner may
use projected scenario labels as offline mining/gate metadata, but projected
labels remain forbidden actor inputs. Admission should require at least two
projected labels plus projection magnitude and half-width change limits.

M512 implements label-targeted projection mining. It finds `drift_required` and
`aeb_feasible` projected labels in the scored table, but those labels only
appear at high normal margins (`>= 7.45`). All low-margin rows remain
`unavoidable`, so projected-label diversity and terminal-boundary proof do not
overlap in the current projection family.

M513 designs the next audit: test whether low-margin non-`unavoidable`
projected rows exist under a broader diagnostic grid. If not, the workflow
should pre-register a split between mechanism proof gates and broad
scenario-label distribution gates instead of relaxing M512 after the fact.

M514 implements and runs that audit. The broader grid scores `78490` projected
candidates and finds all `4` projected labels (`unavoidable`, `drift_required`,
`aeb_feasible`, `aes_feasible`), but the labels still do not overlap the
terminal boundary. Rows with normal margin `<= 4.0` are all `unavoidable`; the
lowest non-`unavoidable` margin is `6.505553`.

M515 pre-registers the resulting gate split. Mechanism proof should use
terminal-boundary margin sensitivity plus source/config/target/geometry
diversity. Scenario-label diversity remains important, but it moves to a
separate broad scenario-distribution gate and cannot be used to tune mechanism
rows.

M516 implements the mechanism selector and passes the gate. It selects `292`
terminal-boundary projected rows across `6` probe seeds, `3` targets, `2`
configs, `12` projected obstacle buckets, and `46` projection buckets. The
selected rows keep strong wrong-history action signal (`trajectory mean =
0.080304`, p90 `0.124239`) and enough terminal-boundary rows (`236` at margin
`<= 0.50`, `275` at `<= 1.00`). Scenario labels remain all `unavoidable`, which
is reported but not used as a mechanism-gate veto after M514/M515.

M517 designs the required projection-aware outcome gate. The existing
tail-aligned gate cannot be reused unchanged because it would reconstruct
original obstacle geometry rather than replay M516's relocated obstacle
geometry. M518 must preserve projection geometry during normal/wrong/reset/zero
replays and classify positive proof, margin-only signal, control-only
sensitivity, fast correction no-effect, or invalid projection replay.

M518 implements and runs that projection-aware gate. It preserves relocated
obstacle geometry and produces valid replay rows, but the formal run is
classified `invalid_projection_replay`: `tail_offset=8` is invalid for every
one of the `239` input pairs, and all `318` invalid rows are
`missing_left_tail`. Wrong-history has only `1` source-narrow margin candidate
and `0` event rows; reset/zero controls have `10` proof candidates and `0`
event rows. This is an offset validity failure, not controller failure.

M519 redesigns the rerun. M520 should keep the M517 projection-aware semantics
but use valid offsets `0,2,4`, continue reporting invalid-tail counts, and
classify whether the result is positive wrong-history outcome proof,
margin-only signal, control-only sensitivity, fast correction, no-effect, or
still invalid replay.

M520 runs that valid-offset gate. It preserves relocated obstacle geometry and
is no longer invalid: `239` input pairs produce `638` valid tail pairs and
`79` invalid tail pairs. The classification is
`margin_only_projected_history_signal`. Wrong-history has only `1`
source-narrow margin candidate and `0` event rows; reset/zero controls have
`10` proof candidates and `0` event rows. This confirms offset `8` was the M518
validity problem, but it still does not establish positive source-diverse
wrong-history outcome proof.

M521 redirects the next evidence line. Rather than force more one-shot
wrong-history event rows, it designs an L0/L1/L2/L3 history-value ablation:
L0 current-only diagnostic, L1 one-step feedback, L2 finite command-response
window, and L3 online GRU recurrent belief.

M522 implements the first diagnostic runner over M520 projected outcomes. It
maps `normal_projected` to `L3_online_gru` and `reset_projected` to
`L0_reset_hidden_each_step`. The result is
`margin_only_history_value_signal`: L0 has `8` margin candidates and `0` event
rows across `2` probe seeds, `2` configs, and `2` targets. This proves the
runner works, but it is still source-narrow and projected-surface only.

M523 designs the next upgrade: configurable level-to-variant mappings and
multisurface projected/natural provenance. The next runner should evaluate M520
projected rows plus recent natural outcome surfaces such as M497 and M487.

M524 implements that upgrade. The M520 projected surface remains
`margin_only_history_value_signal` with `8` L0 candidates and `0` event rows.
The natural M497/M487 surfaces produce `event_history_value_signal`: `480` L0
candidates and `18` event rows across `12` probe seeds, `2` configs, and `3`
targets. These are obstacle-completion drops, not success or collision drops.

M525 designs the required audit before stronger claims: export the M524 event
rows, check source diversity and duplicates, verify event semantics, and keep
projected rows out of the natural event claim.

Next step: M526 should run the history-value event audit. It should not train
or promote.

## Current Evidence

- M177: action-level self-ID signal exists. Wrong-history, reset-hidden, and
  zero-current-response interventions change actions.
- M178: raw matched-current continuation outcome is neutral. Wrong-history does
  not create success drops on the raw surface.
- M179: boundary relocation creates local wrong-history success drops, but the
  surface is lateral-only and duplicate-dominated.
- M180: lateral and longitudinal obstacle offsets do not fix duplicate
  domination.
- M181: lowering the base action-distance threshold does not fix duplicate
  domination; the M178 candidate pool is exhausted for the current boundary
  relocation recipe.
- M182: remaking the matched-current corpus with physical-pair, left-step, and
  obstacle-bucket diversity produces a robustness-passing boundary wrong-history
  proof surface: `78` accepted success-drop rows across `15` physical pairs,
  `8` left steps, `3` targets, and `2` checkpoints.
- M183: deduplicated M182 boundary-outcome corpora pass objective sanity for
  both M168 and M170, and replay sanity reproduces normal-history success plus
  wrong-history failure on every corpus row.
- M184: a 20-step anchored actor-coupling update from M168 improves the M183
  fixed objective with tiny anchor drift, preserves behavior on seeds `9503`
  and `9504`, passes the protected key, and retains all M168/M170 boundary
  replay success drops.
- M185: a 1024-step guarded PPO smoke from M184 improves the fixed M183
  objective slightly, preserves behavior on seeds `9503` and `9504`, passes the
  protected key, and retains all M168/M170 boundary replay success drops.
- M186: independent repeats of the M185 recipe on seeds `5186` and `5187`
  preserve behavior, protected key, and M168/M170 boundary replay drops. Fixed
  objective improvement is mixed, so M185 seed `5185` remains the best retained
  fixed-loss checkpoint.
- M187: a short stage2 PPO extension from M185 seed `5185` improves fixed M183
  loss to `0.171351` and preserves behavior, protected key, and both M183
  replay surfaces.
- M188: stage2 repeats on seeds `5191` and `5192` preserve behavior, protected
  key, and both M183 replay surfaces; seed `5191` improves fixed M183 loss to
  `0.171306`.
- M189: a short stage3 continuation from M188 seed `5191` improves fixed M183
  loss to `0.171221` and preserves behavior, protected key, and both M183
  replay surfaces.
- M190: stage3 repeats preserve behavior, protected key, and both M183 replay
  surfaces, but fixed M183 loss plateaus near `0.171232`; M189 remains the
  current best fixed-loss checkpoint.
- M191: broader current-best evaluation validates M189 on fresh behavior seeds
  `9505` and `9506`, preserves the protected key, and keeps the M168/M170 M183
  replay success-drop counts at `16/16` and `17/17`. The result is positive as
  retention, but not enough to continue PPO because the proof surface is still
  inherited from M183.
- M192: a fresh current-family proof-surface refresh with seeds
  `9520`-`9523` finds `2817` matched-current pairs and passes robustness with
  `131` wrong-history success drops across `11` physical pairs, `6` left
  steps, `3` checkpoints, and `2` target groups. This refreshes evidence beyond
  M183 but still requires replay-aligned objective sanity before actor/PPO work.
- M193: converts M192 accepted rows into M184/M188/M189 boundary-outcome
  objective corpora. All three pass 3-seed objective sanity and replay gates.
  The current-best M189 corpus has `14` rows across `11` physical pairs and
  `2` targets, with `14/14` replayed success drops retained.
- M194: a single-seed tiny actor-coupling update from M189 improves the M193
  fixed objective by `0.001639` on independent eval, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M195: fresh actor-update repeats from M189 on seeds `9851` and `9852` both
  improve the fixed M193 objective versus M189 and preserve behavior,
  protected key, old M183 replay, and refreshed M193 replay. M194 remains the
  best fixed-objective actor-update checkpoint.
- M196: a 1024-step guarded PPO smoke from M194 preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
  Fixed M193 loss remains better than M189 (`0.159017` vs `0.160647`) but does
  not beat M194 (`0.159008`), so the result is retention only.
- M197: fresh PPO smoke repeats from M194 on seeds `5197` and `5198` both
  improve fixed M193 loss versus M194 (`0.158919` and `0.158976` vs
  `0.159008`) and preserve behavior seeds `9505` and `9506`, protected key,
  old M183 replay drops `16/16` and `17/17`, and refreshed M193 replay drops
  `14/14`. Seed `5197` is the current best retained fixed-loss repeat.
- M198: a short stage2 from M197 seed `5197` improves fixed M193 loss to
  `0.158892`, preserves behavior seeds `9505` and `9506`, passes the protected
  key, retains old M183 replay drops `16/16` and `17/17`, and retains
  refreshed M193 replay drops `14/14`.
- M199: stage2 repeats from M197 seed `5197` on seeds `5201` and `5202` both
  improve fixed M193 loss versus M198 (`0.158850` and `0.158857` vs
  `0.158892`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. Seed `5201`
  is the current best retained fixed-loss repeat.
- M200: a short stage3 from M199 seed `5201` improves fixed M193 loss to
  `0.158756`, preserves behavior seeds `9505` and `9506`, passes the protected
  key, retains old M183 replay drops `16/16` and `17/17`, and retains
  refreshed M193 replay drops `14/14`. Its smoke eval termination rate is
  elevated at `0.40`, so repeat evidence is required before further
  continuation.
- M201: stage3 repeats from M199 seed `5201` on seeds `5204` and `5205` both
  improve fixed M193 loss versus M199 (`0.158730` and `0.158755` vs
  `0.158850`), do not repeat M200's elevated smoke eval termination, and
  preserve behavior, protected key, old M183 replay drops `16/16` and `17/17`,
  and refreshed M193 replay drops `14/14`. Seed `5204` is the current best
  retained fixed-loss repeat.
- M202: a short stage4 from M201 seed `5204` improves fixed M193 loss to
  `0.158585`, keeps smoke eval termination at `0.20`, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M203: stage4 repeats from M201 seed `5204` on seeds `5207` and `5208` both
  improve fixed M193 loss versus M201 (`0.158642` and `0.158616` vs
  `0.158730`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. They do not
  beat M202 (`0.158585`), so M202 remains the best fixed-loss stage4. Seed
  `5207` has elevated smoke eval termination `0.40`, so only one short
  guarded stage5 is admitted.
- M204: a short stage5 from M202 seed `5206` improves fixed M193 loss to
  `0.158475`, keeps smoke eval termination at `0.20`, preserves behavior seeds
  `9505` and `9506`, passes the protected key, retains old M183 replay drops
  `16/16` and `17/17`, and retains refreshed M193 replay drops `14/14`.
- M205: stage5 repeats from M202 seed `5206` on seeds `5210` and `5211` both
  improve fixed M193 loss versus M202 (`0.158520` and `0.158503` vs
  `0.158585`) and preserve behavior, protected key, old M183 replay drops
  `16/16` and `17/17`, and refreshed M193 replay drops `14/14`. They do not
  beat M204 (`0.158475`), so M204 remains the best fixed-loss stage5.
- M206: a short stage6 from M204 seed `5209` improves fixed M193 loss to
  `0.158420`, has smoke eval termination `0.00`, and preserves behavior plus
  old/refreshed replay gates, but fails protected key
  `9944|perturbed|28|28` with `0/1` accepted cases. M206 is rejected; do not
  continue PPO until the protected-key failure is audited.
- M207: audits M206's protected-key failure. The selected key keeps normal
  success and large margin gap, but its normal margin moves to `0.207450`,
  above the reference `max_normal_margin = 0.2` boundary window. M204 remains
  the current best; one fresh-seed stage6 retry from M204 is pre-registered.
- M208: runs the one allowed fresh-seed stage6 retry from M204 seed `5209`.
  The retry improves fixed M193 loss to `0.158354`, keeps behavior success
  `0.8625` on seeds `9505` and `9506`, preserves old M183 replay drops
  `16/16` and `17/17`, and preserves refreshed M193 replay drops `14/14`.
  It fails the same protected key with normal margin `0.208742`, above the
  reference `max_normal_margin = 0.2`, so M208 is rejected and same-recipe
  stage6 PPO is stopped.
- M209: designs the protected-key-aware response. The repeated M206/M208
  failure is treated as single-key proof fragility: normal-history clearance
  improved out of the near-boundary window while wrong-history margin gap stayed
  large. Do not train the driver to lower clearance for the old key. Refresh a
  current-best-family multi-key protected surface before any further PPO.
- M210: fresh current-family protected-surface refresh with seeds
  `10020`-`10023` finds `1837` matched-current pairs across `209` physical
  pairs, but boundary relocation finds `0` accepted wrong-history rows. Reset
  and zero-current interventions still produce `680` and `261` accepted rows,
  so the negative result is specific to fresh wrong-history near-boundary
  evidence.
- M211: repeats the current-family refresh on the M192 probe seeds
  `9520`-`9523` and recovers `171` accepted wrong-history rows across
  `13` physical pairs, `8` left steps, `3` checkpoints, `2` targets, and
  `2` margin buckets. Robustness passes, so M210 was seed/corpus-specific
  rather than proof that current-family wrong-history evidence is gone.
- M212: converts the M211 accepted rows into M204/M202/M199 objective corpora.
  The current-best M204 corpus has `17` rows across `13` physical pairs,
  passes 3-seed objective sanity, and replays against M202 with `17/17`
  success drops retained. The M199 cross-family replay is mixed (`13/15`), so
  the next actor update should use only the M204 current-best corpus.
- M213: runs one tiny anchored actor update from M204 using the M212 M204
  corpus. Fixed M212 loss improves from `0.205221` to `0.201354`, behavior
  success remains `0.8625`, reset and zero-all ablations remain `0.85` and
  `0.80`, old M183 replay, refreshed M193 replay, new M212 replay, and
  protected key all pass.
- M214: repeats the M213 recipe from M204 on seeds `10051` and `10052`.
  Both improve fixed M212 objective, but both fail old and new replay gates by
  losing normal-history success on near-boundary rows. Broad behavior and the
  single protected key still pass, so the failure is specific to the proof
  replay surfaces rather than a global behavior collapse. M214 is rejected;
  M204 remains the retained base and the actor-update recipe needs audit before
  any more updates.
- M215: audits M214. The failure mechanism is now classified as preferred
  boundary-action drift under a relative contrast objective: fixed loss improves
  because rejected-history logprob is reduced, but preferred/normal action
  fidelity is not explicitly protected on the near-boundary snippets. M216 is
  pre-registered as a smaller update with preferred-only snippet action anchor.
- M216: runs the smaller preferred-only snippet-anchored actor-update recipe on
  the known M214 failure seeds `10051` and `10052`. Both improve fixed M212
  loss modestly, pass old M183 replay, refreshed M193 replay, current M212
  replay, behavior seeds `9505`/`9506`, and protected key `9944`. Because these
  were known failure seeds selected after M214, M217 must repeat the same recipe
  on fresh seeds before PPO.
- M217: repeats the exact M216 recipe on fresh seeds `10053` and `10054`. Both
  improve fixed M212 loss versus M204, pass old M183 replay, refreshed M193
  replay, current M212 replay, behavior seeds `9505`/`9506`, and protected key
  `9944`. Seed `10054` is the best fresh-repeat candidate and admits one tiny
  guarded PPO smoke only.
- M218: runs one tiny guarded PPO smoke from M217 seed `10054`. Fixed M212 loss
  improves slightly to `0.204267`, all old/current replay gates pass, behavior
  seeds `9505`/`9506` stay at success `0.8625`, and protected key `9944`
  passes. M219 must repeat the same smoke from M217 seed `10054` on fresh PPO
  seeds before any longer continuation.
- M219: repeats the M218 guarded PPO smoke from the same M217 seed `10054`
  source on fresh PPO seeds `5215` and `5216`. Both repeats keep fixed M212
  loss improved versus M204, preserve old M183 replay, refreshed M193 replay,
  current M212 replay, and broad behavior. Seed `5215` fails the protected key
  by moving normal margin to `0.200679`, just above the old `0.2` boundary
  window. Seed `5216` has the best fixed M212 loss `0.204240` and passes the
  protected key with normal margin `0.199571`, so only seed `5216` is promotable.
- M220: runs one short guarded stage2 from M219 seed `5216`. Fixed M212 loss
  improves to `0.204179`, all old/current replay gates pass, and behavior seeds
  `9505`/`9506` stay at success `0.8625`, but protected key `9944` fails with
  normal margin `0.214602` above the old `0.2` near-boundary window. M220 is
  rejected; current best remains M219 seed `5216`.
- M221: audits the M220 failure. M220 preserves normal success and
  wrong-history gap on the old key but leaves the near-boundary normal-margin
  window, matching the M206/M208 and M219 seed `5215` failure class. Do not
  repeat M220, loosen the old key, or train lower clearance on that one row.
  Refresh a source-diverse M217/M218/M219-family protected surface before any
  more PPO.
- M222: refreshes the protected surface for the M217/M218/M219 family on probe
  seeds `9520`-`9523`. It recovers `180` accepted wrong-history boundary rows
  across `13` physical pairs, `8` left steps, `3` checkpoints, `2` targets, and
  `2` margin buckets. Robustness passes, so the current family still has
  source-diverse history-dependent near-boundary evidence.
- M223: converts the M222 accepted rows into replay-aligned M219/M218/M217
  boundary-outcome corpora. Each corpus has `17` rows across `13` physical
  groups and passes 3-seed objective sanity. The M219 corpus replay sanity
  preserves `17/17` wrong-history success drops, so a small guarded actor-update
  design is admitted.
- M224: runs one small M216-style preferred-only snippet-anchored actor update
  from M219 seed `5216` using the M223 M219 corpus. Fixed M223 loss improves
  from `0.210903` to `0.209824`; old M183, refreshed M193, current M212, and
  new M223 replay gates pass; behavior remains `0.8625`; protected key `9944`
  passes with normal margin `0.186385`.
- M225: repeats the M224 actor-update recipe from the same M219 source on fresh
  seeds `10064` and `10065`. Both improve fixed M223 versus M219 and preserve
  old/current/new replay, broad behavior, and protected key. They do not beat
  M224 fixed loss, so M224 remains the best actor-update checkpoint and admits
  one guarded PPO smoke.
- M226: runs one tiny guarded PPO smoke from M224 using the M223 corpus and M224
  action anchor. Broad behavior remains `0.8625`, but fixed M223 does not beat
  M224, M183 M170 replay drops to `16/17`, and protected key `9944` fails with
  normal margin `0.203847`. M226 is rejected; current best remains M224.
- M227-M265: repairs the PPO retention path with snippet anchors, protected-key
  snippets, trajectory anchors, exact source-aware objectives, and
  trajectory-anchored post-PPO projection. The current public-gate base advances
  to `m264_a001`, but the old protected key becomes saturated: normal-margin
  slack shrinks to `0.000029` while wrong-history margin gap remains large.
- M266: refreshes the M261/M263/M264 protected surface without PPO. Robustness
  passes with `180` accepted wrong-history boundary rows across `13` physical
  pairs, `8` left steps, `3` checkpoints, `2` targets, and `2` margin buckets.
  The refreshed rows have mean normal margin `0.005947` and max normal margin
  `0.010194`, so the old key remains a diagnostic but should not be the sole
  protected-surface veto.
- M267: converts the M266 surface into replay-aligned boundary-outcome corpora
  for `m264_a001`, `m263_a005`, and `m261_a001`. Each corpus has `17` rows
  across `13` physical pairs and passes 3-seed objective sanity; replay sanity
  preserves normal success `1.0` and `17/17` wrong-history success drops.
- M268: runs one small actor update from `m264_a001` using the M267 corpus.
  Fixed M267 loss improves under sampled and exact eval, but M183/M168,
  M183/M170, and M193/M189 replay gates fail. M268 is rejected as
  `proof_washout` / `objective_overfit`.
- M269: audits M268 and finds the failure is normal-history collision on old
  surfaces, not wrong-history sensitivity loss. M193 fully overlaps M267
  physical keys and still fails, so the issue is old hidden/action geometry not
  protected by an M267-only corpus.
- M270: builds a `99`-row source-balanced combined anchor corpus covering
  M183/M168, M183/M170, M193/M189, M212/M204, M223/M219, M267/M264, and
  protected key `9944`. Loader validation passes.
- M271: runs one small actor update with the M270 corpus. The combined objective
  improves, but M183/M193/M212/M223 replay gates fail before behavior or
  protected-key gates. M271 is rejected; the next step is no-training
  interpolation from M264 toward M271.

Historical M271 blocker:

```text
m272-m271-interpolation-retention-probe
```

## Near-Term Rule

Do not run PPO or promote a checkpoint while the current blocker is M487
critical-window tail-aligned outcome gate. M486 selected `312` targeted pairs
from the M485 matched-current surface, covering `6` probe seeds, `3` labels, and
`3` targets, with near-threshold / late-high-energy split `157/155`. This is
still only a targeted test surface. M487 must split by config and run
tail-aligned wrong-history gates; only `wrong_tail_once` rows can count toward
natural wrong-history proof. M478 remains positive diagnostic evidence that
wrong belief can be outcome-critical if clamped, but clamped rows and
single-source tail events must stay separate from natural wrong-history proof.

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
