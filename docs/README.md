# AutoDrift Research Notes

Last updated: 2026-05-20

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

## Scope Rule

The notes distinguish three roles:

- model-based control and NMPC for online constraint handling;
- learned tire, thermal, residual, or diffusion models for improving prediction;
- RL policies for reference-free waypoint behavior, residual decisions, or high-level
  strategy, rather than as the first replacement for all solver logic.

Full extracted paper text is not stored in this repository. Temporary extraction was
used only for reading and summarization.
