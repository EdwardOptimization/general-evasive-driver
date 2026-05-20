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
