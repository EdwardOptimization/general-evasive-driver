# m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot Research Review

## Summary

- Generated at UTC: 20260528T011926Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M1166 may only run the small staged relocation pilot and compare it to M1161. It cannot rerun mining or outcome gates, train actor weights, run PPO, promote, use private holdout, change actor inputs, convert the pilot surface, or claim full surface pass.

## Hypothesis

A small wrong-history-only body-offset relocation pilot can complete quickly and indicate whether body-offset expansion improves accepted wrong-history surface quality over M1161.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1165-v4-public-base-row15-promoted-staged-relocation-expansion-design.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
- parent_config: experiments/manifests/m1165-v4-public-base-row15-promoted-staged-relocation-expansion-design.json
- parent_objective: run a small relocation-expansion pilot over existing M1161 outcomes
- derived_from: m1165-v4-public-base-row15-promoted-staged-relocation-expansion-design
- blocked_by: M1165 designs the resource-bounded staged pilot
- supersedes: None
- invalidates: conversion from pilot result, PPO from pilot result, full expansion before pilot result

## Success Criteria

- summary artifact exists
- pilot runtime completes
- accepted_wrong_history_rows is reported
- accepted_wrong_physical_pairs is reported
- accepted_wrong_normal_margin_buckets is reported
- accepted_wrong_normal_margin_max is reported
- comparison to M1161 is explicit
- no actor training, PPO, promotion, private holdout, mining rerun, outcome rerun, conversion, or actor-input change occurs

## Failure Criteria

- summary artifact is missing
- pilot exceeds resource budget and must be interrupted
- comparison to M1161 remains ambiguous
- actor training, PPO, promotion, private holdout, mining rerun, outcome rerun, conversion, or actor-input change starts

## Evidence Gates

- M1166 may run only the M1165 pilot command
- M1166 must reuse the existing M1161 outcome CSV
- M1166 must not rerun mining
- M1166 must not rerun outcome gate
- M1166 must not train actor weights
- M1166 must not run PPO
- M1166 must not promote
- M1166 must not use private holdout
- M1166 must preserve actor inputs
- M1166 must not convert the pilot surface

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun mining
- do not rerun outcome gate
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert the pilot surface
- do not claim full surface pass from pilot diagnostic

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot
