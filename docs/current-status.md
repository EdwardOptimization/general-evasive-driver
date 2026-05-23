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
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

Status: M370 promotes M369 alpha `0.4` as the current public-gate base. It
passes old-key replay, source-diverse protected gates `5/5`, all six public
replay surfaces, and behavior seeds `9505`/`9506`. This remains a proof-safe
incremental step rather than a large driver-performance improvement; alpha
`0.6` from the same hard-row weighted repair direction is the first tested
old-key compact gap-p10 failure.

Current blocker:

```text
m374-gap-tail-weighted-repair-probe
```

M337 classified the bottleneck as singleton old-key gap-floor saturation, not
broad source-diverse proof washout. M341 mined a source-diverse old-key
neighborhood corpus with `179` broad rows and `40` compact rows. M342-M345
implemented and validated reusable static and replayable old-key neighborhood
gates. M347 then found `m335_a010` is the largest M335 interpolation alpha
passing that distributional old-key gate, with `alpha=0.02` the first failing
alpha.

M348 checks `m335_a010` beyond old-key replay. It passes exact M297/M270
no-regression versus the previous M336 base, source-diverse protected gates
`5/5`, and first replay gates M183/M170 plus M267/M264. M349 then promotes it
after all six public replay gates and behavior seeds pass. M350 registers the
next short PPO escalation design from this new base without running training.
M351 runs the proposal-only PPO step: the repaired endpoint improves exact
objectives but fails source/old-key proof, while bounded `alpha=0.0075` passes
exact, source-diverse, old-key neighborhood, and first replay gates. M352
promotes the bounded candidate after all six public replay gates and behavior
seeds pass. M353 registers a fresh-seed repeat before any longer PPO. M354 is
the fresh-seed proposal-only PPO repeat: raw PPO runs, but exact repair improves
M297 while regressing M270, so downstream gates are skipped. M355 audits that
failure and finds a feasible 39-step repair state; the saved 40-step endpoint
failed because the repair tool logs pre-update metrics but saves the final
post-update state. M356 implements post-update metrics and lexicographic
best-feasible checkpoint selection; the corrected M354 repair probe saves step
`25` and passes exact M297/M270. M357 then rejects direct acceptance: the
candidate passes M183/M170 but fails source-diverse protected gates `3/5`, old
key neighborhood `25/40` accepted, and M267/M264 first replay `15/17`. M358
then bounds the M356 direction by interpolation: `alpha=0.00025` is the largest
tested nonzero old-key-neighborhood-passing step, while `alpha=0.0005` is the
first failing step. M359 verifies `alpha=0.00025` passes source-diverse
protected gates `5/5` and M183/M170 plus M267/M264 first replay gates `17/17`.
M360 promotes `alpha=0.00025` after all six replay surfaces and behavior seeds
pass. This is a proof-safe micro-step, not meaningful driver improvement. M361
classifies it as retention-only progress. M362 designs old-key-aware exact
repair, where old-key neighborhood proof becomes a first-class repair surrogate
before more PPO. M363 implements the old-key preference corpus and optional
exact-repair surrogate, exports a 40-row old-key corpus, and verifies the repair
integration path with a no-update smoke. M364 runs the no-PPO proof probe:
direct old-key-aware repair still fails old-key replay by one accepted
regression, but interpolation alpha `0.1` passes old-key, source-diverse, and
first replay gates. M365 promotes alpha `0.1` after the full public gate passes.
M366 audits the alpha `0.2` failure and finds a single wrong-history
terminal-margin sign crossing, not normal-branch regression. M367 designs a
hard-row overlay and branch-weight feedback path for old-key repair. M368
implements that path, exports a 40-row weighted old-key corpus with one hard
row, and verifies no-update exact repair integration without changing actor
inputs. M369 runs the no-PPO proof probe: the direct repaired endpoint fails
old-key replay, but interpolation alpha `0.4` passes old-key, source-diverse,
and first replay proof gates. M370 promotes alpha `0.4` after the full public
gate passes. M371 should audit the alpha `0.6` old-key compact gap-p10 failure
before any more repair or PPO. M371 classifies alpha `0.6` as old-key
gap-distribution erosion without accepted regressions; M372 should design
gap-tail retention feedback rather than lower thresholds or run PPO. M372
completes that design and admits M373 implementation of the gap-tail overlay
path. M373 implements the overlay path, exports a 40-row hard-row plus gap-tail
weighted old-key corpus, and verifies no-update exact repair integration. M374
should now test the weighted corpus in a no-PPO repair probe, with closed-loop
old-key replay still authoritative.

| Role | Checkpoint | Status |
| --- | --- | --- |
| strict anchor | `runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt` | strict full-replay anchor |
| split-aware candidate | `runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt` | preserves robust rows but loses knife-edge row 67 |
| guarded actor-update candidate | `runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt` | passes M183 objective, behavior, protected key, and M168/M170 boundary replay |
| guarded PPO smoke candidate | `runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt` | positive single-seed PPO smoke; requires repeat before longer PPO |
| repeated PPO smoke candidates | `runs/ppo_m186_guarded_from_m184_seed5186/checkpoint.pt`, `runs/ppo_m186_guarded_from_m184_seed5187/checkpoint.pt` | preserve gates; fixed objective mixed, so M185 remains best fixed-loss candidate |
| guarded stage2 candidate | `runs/ppo_m187_stage2_from_m185_seed5190/checkpoint.pt` | positive single-seed stage2; requires repeat before longer PPO |
| repeated stage2 candidates | `runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt`, `runs/ppo_m188_stage2_from_m185_seed5192/checkpoint.pt` | preserve gates; seed 5191 has current best fixed M183 loss |
| guarded stage3 candidate | `runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt` | positive single-seed stage3; requires repeat before longer PPO |
| repeated stage3 candidates | `runs/ppo_m190_stage3_from_m188_seed5194/checkpoint.pt`, `runs/ppo_m190_stage3_from_m188_seed5195/checkpoint.pt` | preserve gates but do not beat M189 fixed loss |
| current-best actor-update candidate | `runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt` | best refreshed M193 fixed-objective actor update; seed-repeat stable |
| current-best guarded PPO smoke | `runs/ppo_m196_guarded_from_m194_seed5196/checkpoint.pt` | positive retention smoke from M194; requires repeat before longer PPO |
| current-best guarded PPO repeat | `runs/ppo_m197_guarded_from_m194_seed5197/checkpoint.pt` | best fixed-loss M197 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage2 | `runs/ppo_m198_stage2_from_m197_seed5200/checkpoint.pt` | positive single-seed stage2; requires repeat before further continuation |
| current-best guarded stage2 repeat | `runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt` | best fixed-loss M199 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage3 | `runs/ppo_m200_stage3_from_m199_seed5203/checkpoint.pt` | positive single-seed stage3; smoke eval termination elevated; requires repeat before further continuation |
| current-best guarded stage3 repeat | `runs/ppo_m201_stage3_from_m199_seed5204/checkpoint.pt` | best fixed-loss M201 repeat; preserves behavior, protected key, old replay, and refreshed replay |
| current-best guarded stage4 | `runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt` | positive single-seed stage4; requires repeat before further continuation |
| current-best guarded stage4 repeat evidence | `runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt` | M203 repeats preserve gates, but M202 remains best fixed-loss stage4 |
| current-best guarded stage5 | `runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt` | positive single-seed stage5; requires repeat before further continuation |
| current-best guarded stage5 repeat evidence | `runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt` | M205 repeats preserve gates, but M204 remains best fixed-loss stage5 |
| current-best snippet-anchored actor update | `runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt` | M217 fresh repeat preserves old/current replay, behavior, and protected key |
| current-best guarded PPO smoke repeat | `runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt` | best retained M219 repeat; seed5215 fails protected-key margin window |
| rejected guarded stage2 from M219 | `runs/ppo_m220_stage2_from_m219_seed5217/checkpoint.pt` | improves fixed M212 and preserves replay/behavior, but fails protected key |
| previous public-gate base | `runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt` | M299 promoted after exact M297/M270 improvement and full public-gate pass |
| rejected PPO proposal | `runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt` | M302 regresses exact M297/M270 and is not promotable |
| exact repair infrastructure | `src/autodrift/exact_post_ppo_repair.py` | M305 implemented deterministic exact M297/M270 repair summaries and line-search starts |
| previous public-gate base | `runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt` | M307 promoted after exact objectives full replay protected-key and behavior gates pass |
| repair repeat diagnostic | `runs/m308_exact_repair_from_raw_s40_seed10094/candidate_checkpoint.pt` | M308 repeats M306 exact deltas and first replay gates; not separately promoted |
| next PPO proposal config | `configs/ppo_m310_exact_repaired_proposal_smoke.json` | M309 registered smoke PPO from M307 plus mandatory exact repair before replay |
| rejected full-gate candidate | `runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt` | M311 rejects after protected-key failure despite exact and replay success |
| previous public-gate base | `runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt` | M314 promoted after exact objectives full replay protected-key and behavior gates pass |
| next protected-key-aware PPO config | `configs/ppo_m316_protected_key_aware_proposal_smoke.json` | M315 registered smoke PPO from M314 plus exact repair and protected-key-bounded acceptance before replay |
| current public-gate base | `runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt` | M317 promoted after exact objectives full replay protected-key and behavior gates pass; protected-key slack is about `4.8e-6` |
| refreshed protected surface | `runs/m319_m317_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv` | M319 found source-diverse accepted wrong-history rows away from the saturated old key |
| refreshed protected corpora | `runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv` | M320 converted the M319 surface into compact replay-aligned corpora; all replay sanity gates pass |
| protected gate design | `docs/m321-source-diverse-protected-gate-design.md` | M321 defines M320 corpora as first-class protected acceptance bundle and keeps `9944` diagnostic |
| protected gate wrapper | `src/autodrift/source_diverse_protected_gate.py` | M322 implements aggregate replay-gate wrapper and M320 sanity reproduction |
| endpoint diagnostic | `runs/m323_source_diverse_gate_repaired_endpoint_probe/summary.json` | M323 shows M316 repaired passes source-diverse gates but old `9944` remains a singleton-window conflict |
| protected-key policy | `docs/m324-single-key-window-override-policy-design.md` | M324 allows singleton-window saturation to advance to full public gate only after exact and source-diverse proof pass; `9944` remains diagnostic |
| previous source-diverse public base | `runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt` | M325 promotes the repaired endpoint after exact objectives, source-diverse proof, six replay gates, old-key audit, and behavior seeds pass |
| next PPO config | `configs/ppo_m327_source_diverse_protected_proposal_smoke.json` | M326 registers smoke PPO from M325 with exact repair, source-diverse protected gates, old-key diagnostic, and first replay gates |
| current source-diverse public base | `runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt` | M328 promotes the M327 exact-repaired PPO proposal after exact, source-diverse, replay, old-key audit, and behavior gates pass |
| fresh-seed repeat config | `configs/ppo_m330_source_diverse_protected_repeat_smoke.json` | M329 registers PPO seed 5237 from M328 base with exact repair and source-diverse proof gates |
| rejected fresh-seed repeat | `runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt` | M330 exact/source-diverse pass but old-key margin gap floor fails, so first replay is not run |
| old-key gap audit | `runs/m331_m330_old_key_gap_floor_audit/summary.json` | M331 classifies M330 as old-key local gap erosion and admits gap-bounded interpolation |
| gap-bounded interpolation candidate | `runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt` | M332 selects alpha 0.45 after exact/source-diverse/old-key floor and first replay gates pass |
| current source-diverse public base | `runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt` | M333 promotes alpha 0.45 after exact, source-diverse, replay, old-key gap floor, and behavior gates pass |
| short PPO escalation config | `configs/ppo_m335_short_source_diverse_escalation.json` | M334 registers 4096-step PPO from M333 base with exact repair and bounded proof gates; no PPO run yet |
| bounded short-PPO candidate | `runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt` | M335 exact repair improves objectives but old-key floor clips accepted movement to alpha 0.0075; first replay gates pass |
| previous source-diverse public base | `runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt` | M336 promotes alpha 0.0075 after exact, source-diverse, replay, old-key gap floor, and behavior gates pass |
| old-key bottleneck audit | `runs/m337_old_key_gap_floor_bottleneck_audit/summary.json` | M337 shows M335 endpoint passes source-diverse gates but old-key gap collapses to 0.065360; next step is distributional gap-gate design |
| old-key gap distribution design | `docs/m338-old-key-gap-distribution-refresh-design.md` | M338 keeps 9944 as diagnostic but designs source-diverse gap distribution to avoid singleton veto dominance |
| old-key gap corpus refresh | `runs/m339_old_key_gap_distribution_refresh/summary.json` | M339 broad pool has 195 rows, but compact severity draft is source dominated, so it cannot replace singleton 9944 floor |
| old-key neighborhood design | `docs/m340-old-key-neighborhood-mining-design.md` | M340 designs five no-PPO seed blocks plus explicit broad and compact diversity targets |
| old-key neighborhood corpus | `runs/m341_old_key_neighborhood_mining/summary.json` | M341 produces a valid 40-row compact corpus across 5 seed blocks; selected alpha passes and repaired endpoint fails |
| old-key neighborhood gate | `src/autodrift/old_key_neighborhood_gate.py` | M342 implements the reusable static gate and M343 confirms selected alpha passes while repaired endpoint is repair-needed |
| old-key gate policy | `docs/m344-old-key-neighborhood-policy-integration-design.md` | M344 defines the neighborhood gate as the first-class old-key proof gate while keeping `9944` diagnostic visible |
| old-key replay adapter | `src/autodrift/old_key_neighborhood_replay_gate.py` | M345 converts compact old-key replay guard results into candidate-level pass/fail metrics; M335 alpha passes and repaired endpoint fails |
| old-key alpha sweep design | `docs/m346-old-key-neighborhood-alpha-sweep-design.md` | M346 pre-registers a no-PPO alpha sweep over the M335 interpolation family using replayable old-key gate metrics |
| old-key alpha sweep | `runs/m347_old_key_alpha_sweep/summary.json` | M347 finds `alpha=0.01` is the largest old-key-neighborhood-passing M335 interpolation alpha and `alpha=0.02` is the first failing alpha |
| exact/source-diverse probe | `runs/m348_m335_a010_probe/summary.json` | M348 passes exact M297/M270, source-diverse protected gates, old-key neighborhood, and first replay gates for `m335_a010` |
| current public-gate base | `runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt` | M349 promotes alpha 0.01 after exact, source-diverse, old-key neighborhood, six replay, and behavior gates pass |
| next PPO config | `configs/ppo_m351_old_key_neighborhood_escalation.json` | M350 registers a short proposal-only PPO continuation from M349 base with exact/source-diverse/old-key-neighborhood gates |
| bounded PPO candidate | `runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt` | M351 selects alpha 0.0075 after repaired endpoint fails source/old-key proof but bounded alpha passes exact/source-diverse/old-key/first replay gates |
| current public-gate base | `runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt` | M352 promotes alpha 0.0075 after exact, source-diverse, old-key neighborhood, six replay, and behavior gates pass |
| fresh-seed repeat config | `configs/ppo_m354_old_key_neighborhood_repeat.json` | M353 registers seed 5240 short PPO repeat from M352 base before any longer PPO |
| rejected fresh-seed repeat | `runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt` | M354 exact repair improves M297 but regresses M270, so downstream gates are skipped |
| exact repair endpoint audit | `runs/m355_m354_repair_step39_diagnostic/summary.json` | M355 shows M354 had a feasible 39-step exact repair state; final-step selection crossed the M270 boundary |
| exact repair best-step candidate | `runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt` | M356 fixes endpoint selection and selects step 25 with exact M297/M270 no-regression |
| rejected proof-gate candidate | `runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt` | M357 rejects direct acceptance because source-diverse old-key and M267/M264 proof gates fail |
| bounded micro-alpha candidate | `runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt` | M358 finds alpha 0.00025 passes exact and old-key; alpha 0.0005 first fails old-key |
| proof-gate-passing micro-alpha | `runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt` | M359 passes source-diverse protected and first replay proof gates |
| current public-gate base | `runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt` | M360 promotes alpha 0.00025 after full public gate pass; movement is extremely small |
| current blocker | `experiments/manifests/m374-gap-tail-weighted-repair-probe.json` | M374 must probe the gap-tail weighted old-key repair path without PPO before any further continuation |

Do not replace M168 with M170 solely because M170 has better fixed objective or
slightly stronger action-level sensitivity.

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

Do not run more PPO until M339 exports and validates the source-diverse
old-key/gap corpus. Do not lower the `0.09` singleton floor ad hoc and do not
remove `9944` from diagnostics; replace singleton veto dominance with a
pre-registered distributional gate. Do not change actor inputs.

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
