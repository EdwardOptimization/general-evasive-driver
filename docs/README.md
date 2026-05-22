# AutoDrift Research Notes

Last updated: 2026-05-22

This folder collects the initial literature package for the AutoDrift project.
The current focus is autonomous drifting with reinforcement learning, learned
vehicle/tire models, and NMPC-style constrained control.

## Contents

- `papers/`: PDFs supplied by the user or downloaded from open-access sources.
- `references.bib`: BibTeX entries for the primary papers and selected related work.
- `source-log.md`: source status, links, and short takeaways.
- `related-papers.md`: citation-snowball list grouped by project relevance.
- `drifting-rl-nmpc-reading-notes.md`: main reading note and project implications.
- `emergency-drift-avoidance-related-work.md`: focused notes for AEB-failure,
  AES, drift-based obstacle avoidance, and friction-adaptive control.
- `implementation-plan.md`: engineering roadmap and milestone definitions.
- `infrastructure.md`: current run-artifact contract and deferred infrastructure.
- `observation-contract.md`: deployable actor-input contract, removed oracle
  fields, and missing sensor/perception inputs.
- `m2-circular-drift-results.md`: current circular drift training and benchmark
  result.
- `m3-friction-adaptation-plan.md`: friction-step adaptation task definition
  and baseline result.
- `m4-general-path-tracking.md`: figure-eight transition tracking results and
  segment diagnostics.
- `m5-emergency-avoidance.md`: AEB-infeasible obstacle-avoidance task,
  baselines, and RL results.
- `m6-model-based-baselines.md`: fixed friction-envelope AES baseline and
  comparison against RL.
- `m7-universal-closed-loop-operator.md`: next-stage closed-loop RL operator
  direction for vehicle, tire, brake, actuator, and road generalization.
- `m7-related-papers.md`: related work for direct RL drift control, emergency
  avoidance, recurrent adaptation, asymmetric actor-critic, and sim-to-real
  domain randomization.
- `m7-validation-protocol.md`: benchmark, ablation, latent-probe, and behavior
  diagnostics needed to prove an M7 policy is effective.
- `m7-first-stage-results.md`: first M7 training, benchmark, ablation,
  latent-probe, negative results, and remaining validation gaps.
- `m7-gate-harness.md`: repeatable M7 gate and label-balanced scenario corpus
  commands.
- `m8-rl-professional-driver.md`: temporal-GRU driver baseline, stable-AES
  reward shaping, smoke result, and next validation steps.
- `m8-driver-gate-blocker-report.md`: best M8 gate result, failed ablations,
  negative attempts, and the remaining driver-v1 blocker.
- `m9-observation-degradation-gate.md`: response-feature ablations, negative
  result, and the next online recurrent validation requirement.
- `m10-clean-driver-results.md`: first full clean-contract temporal driver
  retrain, benchmark, ablations, latent probe, and negative conclusion.
- `m11-online-recurrent-plan.md`: online recurrent actor design, hidden-state
  reset ablation, queued training command, and validation plan.
- `m12-paired-perturbation-gate.md`: paired hidden-friction perturbation gate,
  M11 paired result, and next near-threshold gate direction.
- `m13-near-threshold-paired-gate.md`: near-threshold stress-corpus builder,
  paired hidden-response gate, M11 negative result, and M14 training direction.
- `m14-near-threshold-training-plan.md`: near-threshold recurrent training
  config, scenario-sampling filters, queued command, and validation gate.
- `m15-obstacle-aligned-perturbation-sampler.md`: strict obstacle-aligned
  friction-step sampler, M15 training config, and paired-gate validation plan.
- `m16-sequence-recurrent-ppo.md`: sequence recurrent PPO update for online GRU
  hidden dynamics and validation plan.
- `m17-response-prediction-aux.md`: deployable response-prediction auxiliary
  loss for online GRU hidden-state learning.
- `m18-actuator-response-critical-training.md`: paired actuator-response gate
  extension and behavior-critical recurrent training direction.
- `m19-response-retention-finetune.md`: same-contract M18 fine-tune direction
  for recovering aggregate success without erasing response dependence.
- `m20-periodic-response-retention.md`: periodic checkpointing and checkpoint
  selection plan for response-retention fine-tunes.
- `m21-response-critical-actor.md`: planned response-critical actor structure
  after M20 showed response masking still does not hurt the best checkpoint.
- `m22-hard-response-dependence-gate.md`: next gate direction for mining or
  constructing cases where response ablation must change the outcome.
- `m23-hard-corpus-training.md`: hard response seed oversampling path and first
  M23 training configuration.
- `m24-human-view-driver-contract.md`: 72-value human-view GRU observation
  contract and 3-channel steer/throttle/brake simulator action.
- `m25-human-view-gru-smoke.md`: GPU smoke result proving the human-view GRU
  contract trains end to end.
- `m26-human-view-gru-results.md`: first full human-view GRU training result,
  checkpoint sweep, ablations, and next hard-gate blocker.
- `m27-human-view-self-identification-gate.md`: proof standard and first
  harness plan for human-view hidden-response self-identification.
- `m28-hidden-swap-gate.md`: matched-current-observation hidden-swap gate,
  smoke validation, and negative M28 self-identification result.
- `m29-matched-response-corpus.md`: M28-derived matched hard seed corpus for
  follow-up response-critical training and gates.
- `m30-mixed-hard-corpus-training.md`: mixed hard-seed sampler, M30 training
  config, and smoke result.
- `m31-parallel-rollout-harness.md`: process-based vector env path for
  multi-core rollout collection and first speed smoke.
- `m32-rollout-throughput-profile.md`: rollout-only sync versus parallel
  throughput profile across worker counts.
- `m33-full-ppo-parallel-profile.md`: short full PPO sync versus parallel
  runtime profile and determinism check.
- `m34-response-aux-mixed-training.md`: response-prediction auxiliary loss
  added to the M30 mixed hard-corpus training path.
- `m35-m34-response-critical-corpus.md`: larger M34 hidden-swap mining run and
  response-change corpus for follow-up training.
- `m36-response-change-corpus-training.md`: planned fine-tune from M34_151 on
  the M35 response-change corpus.
- `m37-multistep-response-aux-plan.md`: next architecture direction after
  M36 showed one-step response auxiliary plus hard replay is insufficient.
- `m38-m37-response-critical-corpus.md`: M37_102 hidden-swap mining and
  response-critical corpus.
- `m39-m37-response-corpus-training.md`: planned M39 continuation from M37_102
  on the M38 corpus.
- `m40-response-aux-diagnostics-plan.md`: planned response auxiliary loss
  logging and offline evaluator after M39 weakened the ablation signal.
- `m41-behavior-sensitive-response-diagnostics.md`: per-seed response
  prediction diagnostics joined against outcome-change labels.
- `m42-hidden-contrast-objective.md`: intervention-aware auxiliary loss that
  contrasts normal recurrent hidden against per-step reset hidden.
- `m43-action-trajectory-intervention-diagnostics.md`: full-continuation action
  distance diagnostics for reset, zero-response, and hidden-swap interventions.
- `m44-action-contrast-objective.md`: deterministic action-mean contrast
  objective following the M43 action-collapse diagnosis.
- `m45-paired-hidden-snapshot-export.md`: export harness for matched
  nominal/perturbed observations and recurrent hidden states.
- `m46-paired-hidden-action-contrast-objective.md`: same-checkpoint
  paired-hidden action contrast objective using the M45 snapshot NPZ.
- `m47-seed-delta-audit.md`: seed-level M46 win/loss audit and next
  continuation-evidence direction.
- `m48-continuation-critical-snippets.md`: per-step snippets for M46 changed
  seeds and the clearance-margin gate direction.
- `m49-clearance-margin-gate.md`: obstacle collision-radius and
  clearance-margin metrics for evaluation, benchmark, and seed-delta audit.
- `m50-margin-critical-corpus.md`: margin-critical corpus mining across M38,
  broad, and fresh randomized obstacle sweeps.
- `m51-margin-retention-gate.md`: strict promotion gate and continuation
  training config for near-boundary margin retention.
- `m52-full-margin-retention-continuation.md`: full M51 continuation negative
  result and the deduplicated lower-mix direction for M53.
- `m53-dedup-low-mix-margin-retention.md`: deduplicated seed-level corpus,
  lower-mix training config, and M53 smoke gate result.
- `m54-full-dedup-low-mix-continuation.md`: full M53 continuation, strict
  margin-retention gate result, and the conservative M55 direction.
- `m55-conservative-margin-retention.md`: lower-learning-rate dense-checkpoint
  continuation result and the M56 clearance-margin reward direction.
- `m56-terminal-clearance-margin-reward.md`: config-gated terminal
  clearance-margin reward shaping and smoke validation.
- `m57-clearance-margin-reward-scale4.md`: stronger terminal margin reward
  result and the dense near-obstacle reward direction.
- `m58-dense-near-obstacle-clearance-reward.md`: dense near-obstacle
  clearance-margin reward setup and smoke validation.
- `m59-trust-region-checkpoint-interpolation.md`: M37_102 to M56_028
  checkpoint interpolation harness and strict gate result.
- `m60-constrained-baseline-anchor.md`: baseline-action anchor training
  constraint and M60 smoke validation.
- `m61-regression-seed-retention-replay.md`: M60 regression-seed replay corpus
  and stronger-retention smoke setup.
- `m62-positive-margin-checkpoint-interpolation.md`: first strict
  margin-retention pass and M62 current-best candidate.
- `m63-broader-driver-audit.md`: held-out audit showing M62 keeps aggregate
  success but still fails to prove response-history dependence.
- `m64-stronger-response-history-self-identification-gate.md`: paired
  perturbation and ablation audit showing M62 still lacks strong closed-loop
  self-identification evidence.
- `m65-response-necessity-corpus.md`: response-history necessity corpus miner,
  PPO continuation config, and smoke validation.
- `m66-full-response-necessity-continuation.md`: full M65 continuation negative
  result; no checkpoint passed margin retention or improved paired
  self-identification.
- `m67-belief-self-identification-roadmap.md`: captured 5.5pro recommendation
  and the adopted belief/self-ID roadmap after M66/M67-B.
- `m67a-privileged-upper-bound-harness.md`: privileged teacher upper-bound
  harness, full-dynamics teacher observation, and smoke validation.
- `m67b-full-privileged-upper-bound-training.md`: full privileged teacher
  negative upper-bound attempt and warm-started teacher next step.
- `m67c-input-profile-audit.md`: captured the observation-profile review,
  context motion-proxy risk, strict self-ID profile, enhanced OSI profile, and
  reward-cleanup risks.
- `m67d-strict-self-id-observation-profile.md`: config-gated strict context
  profile, smoke continuation, and M62 ablation diagnostic result.
- `m67e-warm-started-privileged-teacher.md`: M62-compatible 82-value
  privileged teacher architecture, training run, checkpoint sweep, and weak
  upper-bound result.
- `m67-self-id-decision-ledger.md`: compact index of the adopted M67
  self-identification decisions, their persisted artifacts, and the next
  matched action-divergent corpus task.
- `m68-matched-action-divergent-corpus.md`: matched visible-state action
  divergence miner, strict M65 smoke, and negative teacher-action diagnostic.
- `m69-broader-matched-hidden-dynamics-mining.md`: fresh-seed friction,
  weak-brake, and slow-actuator matched-action sweeps plus next continuation
  gate direction.
- `m70-wrong-history-continuation-gate.md`: continuation replay on M69
  wrong-history candidates, margin-aware hidden-swap summary, and negative
  outcome-causality result.
- `m71-outcome-sensitive-matched-scenario-constructor.md`: outcome-sensitive
  wrong-history corpus miner, obstacle-geometry overrides, and negative smoke
  results across weak-brake and low-friction contrasts.
- `m72-pre-emergency-warmup-history-harness.md`: warm-up history proof surface,
  obstacle perception reveal infrastructure, and negative warm-up reveal smoke.
- `m73-active-probing-warmup-harness.md`: active-probing warm-up extension,
  weak-brake/low-friction smoke runs, and near-miss diagnostic for the next
  outcome-bound sweep.
- `m74-active-probe-outcome-bound-scenario-sweep.md`: geometry sweep around M73
  active-probe near misses and negative result motivating snapshot-level
  obstacle relocation.
- `m75-snapshot-level-obstacle-relocation-sweep.md`: snapshot-preserving
  obstacle relocation harness, strict/relaxed sweeps, and negative strict gate
  result motivating snapshot-bank visible matching.
- `m76-snapshot-bank-visible-matcher.md`: active-probe snapshot-bank matcher,
  strict/relaxed relocation sweeps, and negative strict gate motivating
  boundary-aware relocation search.
- `m77-boundary-aware-snapshot-relocation.md`: dense obstacle-width relocation
  gate around M76 matched pairs and negative result motivating an
  outcome-weighted intervention objective.
- `m78-outcome-weighted-intervention-objective.md`: outcome-weighted
  hidden-intervention auxiliary loss, snippet NPZ export, human-view smoke
  training, and negative offline-loss check.
- `m79-outcome-objective-weight-tuning.md`: fixed-batch outcome-intervention
  evaluator, high-coefficient smoke, and negative objective tuning result.
- `m80-outcome-objective-only-sanity-check.md`: isolated outcome objective
  optimizer, fixed-batch before/after result, and short driving smoke.
- `external-review-5-5pro-mhtml.md`: consolidated 5.5pro MHTML review record
  covering project status, engineering backlog, research framing, input gaps,
  solve/verify split, warm-up/probing, and proof gates.
- `mhtml-input-sensor-contract-2026-05-21.md`: extracted MHTML input contract;
  actor inputs stay sensor-direct, slip ratios and controller diagnostics stay
  out, and the 2026-05-22 revision demotes `v_parallel_i` from required future
  actor input to optional low-level fusion comparison after driver-like minimal
  and raw-wheel profiles.
- `m143-driver-like-input-profile-audit.md`: latest input-profile audit plan:
  compare current baseline, driver-like minimal, driver-like minimal without
  steering feel, raw wheel speed, and optional `v_parallel_i` under the same
  probe and frozen RL recipe.
- `m81-wheel-response-input-roadmap.md`: MHTML review decision capturing
  wheel/tire response as the next major self-identification input branch,
  including the Stage 1 front/rear wheel-response implementation.
- `m82-outcome-objective-ppo-reintroduction.md`: guarded PPO reintroduction of
  the outcome objective with frozen `log_std`, fixed-batch guard, and negative
  smoke conclusion.
- `m83-wheel-response-driver-training-gate.md`: 32k-step wheel-response driver
  training gate and negative ablation result motivating M62-to-wheel
  warm-start.
- `m84-m62-to-wheel-partial-init.md`: behavior-preserving partial
  initialization from M62 into the 85-value wheel-response actor, with positive
  retention but no wheel self-ID pass.
- `m85-warmstarted-wheel-response-aux.md`: full 25-value response auxiliary
  continuation from M62 warm-start, retaining success but still failing
  zero-wheel dependence.
- `m86-wheel-response-relevance-audit.md`: body-only vs body+wheel linear probe
  audit showing narrow friction-bucket wheel information but no broad
  hidden-dynamics gain.
- `m87-wheel-informed-friction-envelope-objective.md`: training-time friction
  bucket auxiliary objective; retains behavior but is solved by body response
  rather than wheel response.
- `m88-wheel-masked-friction-auxiliary.md`: wheel-only masked friction
  auxiliary path; preserves most behavior but still fails zero-wheel
  dependence.
- `m89-objective-only-wheel-masked-friction-sanity.md`: objective-only
  optimization of the wheel-masked friction target, positive isolated movement,
  and small first zero-wheel behavior drop.
- `m91i-learned-history-sensor-ablation.md`: learned-history sensor ablation
  showing that the current raw front/rear wheel branch should not become the
  primary driver input.
- `m92-local-wheel-ground-speed-input-plan.md`: historical wheel input
  correction: use `Romega_i` and local `v_parallel_i`, not `slip_ratio` or
  wheel-speed averages. The latest M143 plan now treats `v_parallel_i` as an
  optional comparison profile rather than the default actor contract.
- `m92-local-wheel-ground-speed-observability-audit.md`: M92 audit result;
  single-track local ground-speed wheel profiles do not beat the no-wheel
  human-view baseline.
- `m93-m62-hidden-envelope-probe.md`: checkpoint diagnostic showing M62's
  carried recurrent hidden does not yet beat reset hidden on braking/yaw
  future-envelope prediction.
- `m94-hidden-envelope-objective-only.md`: objective-only no-wheel hidden
  envelope sanity check; yaw and lateral hidden belief improve but braking is
  not stable enough for PPO admission.
- `m95-braking-weighted-hidden-envelope-objective.md`: per-target contrast and
  braking-weighted objective; braking stabilizes but lateral/yaw tradeoffs still
  block PPO admission.
- `m96-per-target-hidden-envelope-objective.md`: equal per-target contrast
  objective; braking and yaw become stable, but one lateral seed still blocks
  PPO admission.
- `m97-minlift-hidden-envelope-objective.md`: mild lateral-overweight objective;
  negative result showing target-weight tuning should not replace the M96
  recipe.
- `m98-larger-batch-per-target-objective.md`: larger-batch repeat of the M96
  equal per-target objective; first strict objective-only hidden-envelope pass,
  still awaiting behavior retention.
- `m99-m98-behavior-retention-gate.md`: behavior gate for M98; behavior
  retention passes, but reset/zero-response ablations do not yet show
  driver-level self-identification.
- `m100-m98-actor-coupling-continuation.md`: first guarded PPO actor-coupling
  smoke from M98; retains behavior but still fails reset/zero-response
  dependence.
- `m101-objective-only-actor-coupling.md`: fixed-batch actor-coupling result
  from M98; first clear reset/zero-response behavior-dependence signal, but
  hidden-envelope retention still fails.
- `m102-retention-aware-actor-coupling.md`: stronger-anchor actor-coupling
  repeat; hidden-envelope retention returns, but behavior dependence disappears.
- `m103-outcome-aware-actor-coupling.md`: outcome-sensitive snippet mining and
  actor-coupling repeat; objective and behavior retention pass, but reset-hidden
  dependence and braking/lateral hidden-envelope retention still fail.
- `m104-minimum-observable-input-contract.md`: latest MHTML-derived input
  contract; actor sees sensor-direct command/actuator/wheel/body/scene signals,
  while slip ratios, controller flags, and oracle labels stay out of actor
  inputs.
- `m105-retention-constrained-outcome-coupling.md`: action-anchor constrained
  outcome actor coupling; first M101-M105 qualified positive where normal
  behavior retention, reset/zero-response degradation, and hidden-envelope lift
  are positive on the smoke gate, pending formal repeats.
- `m106-formal-retention-constrained-repeat-gates.md`: formal M105 repeat gate;
  behavior dependence repeats, but strict margin retention is borderline and
  hidden-envelope lift fails fresh probe seeds.
- `m107-multiseed-hidden-envelope-gate.md`: multi-seed hidden-envelope gate
  harness and M105 aggregate result; M105 hidden belief fails aggregate
  admission across probe seeds.
- `m108-baseline-multiseed-hidden-envelope-audit.md`: M62/M98/M102/M105
  baseline audit under the same aggregate gate; all fail, so the proof surface
  needs diagnosis before another objective.
- `m109-hidden-envelope-probe-reliability-audit.md`: hidden-envelope probe
  reliability audit; target means are stable at larger sample counts, but
  carried response hidden still loses to reset/current-response baselines.
- `m110-current-response-anchored-hidden-envelope-objective.md`: objective-only
  hidden-envelope tuning with an explicit current-response baseline; internal
  objective-batch gains fail external repeated split/multi-seed reliability.
- `m111-matched-current-response-ambiguity-audit.md`: matched-current-response
  ambiguity audit; finds 702 future-envelope ambiguous pairs but current hidden
  states do not systematically solve the ambiguity.
- `m112-matched-history-intervention-gate.md`: action-level intervention gate
  on M111 pairs; reset/wrong/delayed/zeroed histories change first actions, but
  rollout outcome is still untested.
- `m113-matched-history-outcome-gate.md`: continuation outcome gate for M112
  interventions; action changes do not produce success drops and only small
  clearance-margin gaps on M111 pairs.
- `m114-near-boundary-matched-history-outcome-surface.md`: near-boundary mining
  over M113 outcomes; finds reset/zero-current margin-loss rows but no
  wrong-history outcome-critical rows.
- `m115-wrong-history-boundary-relocation-surface.md`: boundary-tightened
  relocation gate; finds 12 wrong-history success-drop rows after obstacle
  half-width tightening, but the surface is narrow and needs M116 robustness
  checks before objective training.
- `m116-boundary-wrong-history-surface-robustness-gate.md`: robustness gate for
  M115; rejects direct objective training because accepted rows collapse to 3
  physical source pairs and 1 normal-margin bucket.
- `m117-source-diverse-wrong-history-boundary-mining.md`: source/geometry
  expansion after M116; all-candidate, relative lateral, and relative
  longitudinal sweeps still collapse to the same 3 physical pairs, so a fresh
  matched corpus is needed.
- `m118-fresh-source-diverse-matched-current-corpus.md`: fresh matched-current
  corpus with source-diversity selection; finds 471 matched rows across 155
  physical pairs and preserves action-level wrong-history sensitivity.
- `m119-fresh-corpus-outcome-boundary-gates.md`: M113/M115/M116-style outcome
  and boundary gates on the M118 corpus; rejects it as a training surface
  because outcome-critical wrong-history rows still collapse to 3 physical
  pairs and 1 margin bucket.
- `m120-outcome-critical-source-diverse-miner.md`: direct snapshot-bank
  outcome-critical mining with source-diverse selection and clean snippet
  export; strict context yields zero accepted rows, while relaxed context finds
  a small non-admissible margin-gap signal.
- `m121-context-aligned-outcome-critical-miner.md`: context-distance audit for
  the M120 blocker; identifies obstacle relative velocity as the context proxy,
  then tests a zero-relvel strict profile that restores accepted rows but still
  fails the source-diversity gate.
- `m122-zero-relvel-source-diverse-outcome-surface.md`: 60-episode repeat of
  the strict zero-relvel miner; admits the M105 corpus for objective-sanity
  only after reaching source diversity while the M62 control remains clean.
- `m123-m122-zero-relvel-objective-sanity.md`: retention-anchored objective
  sanity on the M122 snippets; fixed-batch loss and behavior retention pass, but
  yaw hidden-envelope regression blocks driver/PPO admission.
- `m124-retention-calibrated-zero-relvel-objective.md`: lower-strength M122
  objective sweep; admits a calibrated candidate for formal repeat because it
  keeps behavior and zero-response gap while avoiding the M123 yaw collapse.
- `m125-formal-m124-repeat-gate.md`: fresh-seed repeat gate for M124; behavior
  retention and zero-response gap repeat, but yaw/lateral hidden-envelope lift
  fails fresh probes, so PPO admission is rejected.
- `m126-zero-relvel-belief-proof-surface-audit.md`: reliability audit after
  M125; rejects hidden-envelope R2 as the primary gate and points toward
  strict outcome-critical wrong-history proof surfaces.
- `m127-outcome-centric-self-id-proof-gate.md`: formal repeat gate for the
  strict zero-relvel wrong-history outcome surface; admits the proof surface
  for corpus building while recording that all snippets are perturbed-source.
- `m128-combined-outcome-snippet-corpus.md`: combines accepted-only M127/M126
  outcome snippets into a deduplicated corpus with source-run provenance before
  the next objective-sanity experiment.
- `m129-combined-outcome-objective-sanity.md`: retention-anchored objective
  sanity on the M128 corpus; admits M129 only for formal repeat, not PPO.
- `m130-combined-outcome-formal-repeat-gate.md`: formal repeat gate for M129;
  rejects PPO readiness because fresh strict outcome-surface diversity is too
  weak despite behavior retention and clean M62 controls.
- `m131-proof-surface-retention-repair.md`: diagnosis of why M129 loses fresh
  proof-surface diversity; fixed logprob improvement increased one-step action
  distance but shrank rollout margin gaps.
- `m132-rollout-margin-retention-repair.md`: conservative s60/anchor20 repair
  that modestly improves M128 loss while recovering fresh proof-surface
  diversity versus M129; admitted only to formal repeat.
- `m133-s60-rollout-margin-formal-repeat-gate.md`: formal repeat gate for the
  M132 s60 repair; admits guarded PPO readiness after fresh behavior retention
  and strict proof-surface diversity repeat while recording no-action neutrality
  and perturbed-only source coverage.
- `m134-guarded-ppo-continuation-from-s60.md`: guarded PPO smoke from the M132
  s60 checkpoint; behavior retention passes, but strict proof-surface diversity
  regresses below M133, so longer PPO is rejected.
- `m135-ppo-step-anchor-sensitivity-gate.md`: PPO step-count and anchor-strength
  sensitivity gate; smaller steps reduce proof-surface regression but still
  fail M133 selected-seed diversity.
- `m136-m133-proof-surface-retention-corpus.md`: combines M133 strict
  proof-surface snippets into an explicit retention corpus and audits which
  keys M134/M135 lose.
- `m137-m133-retention-objective-sanity.md`: objective-only update on the M136
  retention corpus; fixed losses and behavior improve/pass, but strict rollout
  proof-surface diversity collapses, proving loss misalignment.
- `m138-retention-loss-rollout-misalignment-audit.md`: key-level audit showing
  M137 can lower retained-row penalties while losing strict rollout keys, so
  direct logprob retention is not rollout-safe.
- `research-process-enforcement.md`: local validator, manifest schema,
  scoreboard, and pre-commit integration that enforce the M90+ research
  workflow.
- `research-log.md`: long-running research queue status, current best model,
  per-cycle notes, and next hypotheses.
- `mvp-status.md`: engineering MVP completion audit.

## Local Hooks

Install the lightweight local pre-commit hook with `make hooks-install`. It
checks staged whitespace and runs the small harness test subset; it deliberately
does not run training or the full M7 gate.

## Scope Rule

The notes distinguish three roles:

- model-based control and NMPC for online constraint handling;
- learned tire, thermal, residual, or diffusion models for improving prediction;
- RL policies as the primary closed-loop operator for AEB-infeasible emergency
  avoidance and drift control;
- model-based control and NMPC as baselines, safety monitors, or fallback
  layers, rather than mandatory online control layers.

Full extracted paper text is not stored in this repository. Temporary extraction was
used only for reading and summarization.
