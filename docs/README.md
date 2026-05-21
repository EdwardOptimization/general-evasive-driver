# AutoDrift Research Notes

Last updated: 2026-05-21

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
