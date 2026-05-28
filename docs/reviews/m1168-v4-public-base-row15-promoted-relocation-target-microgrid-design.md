# m1168-v4-public-base-row15-promoted-relocation-target-microgrid-design Research Review

## Summary

- Generated at UTC: 20260528T013634Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M1168 is design-only. It can design a future target-margin microgrid diagnostic but cannot run relocation replay, rerun mining, rerun outcome gate, train actor weights, run PPO, promote, use private holdout, change actor inputs, weaken thresholds, convert a surface, or claim broad surface pass.

## Hypothesis

A fine target-margin microgrid can test whether M1166 undercounted wrong-history rows because it omitted very fine near-boundary target margins, while still keeping the diagnostic small enough to avoid M1164 resource failure.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit.md, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/summary.json, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/boundary_relocation_rows.csv
- parent_config: experiments/manifests/m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit.json
- parent_objective: design a small target-margin microgrid diagnostic to separate target-grid false negative from broader wrong-history scarcity
- derived_from: m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit
- blocked_by: M1167 finds both a target-margin grid artifact and broader wrong-history scarcity
- supersedes: None
- invalidates: large same-shape relocation expansion before microgrid check, conversion from M1166 pilot rows, PPO before refreshed wrong-history surface evidence

## Success Criteria

- design artifact exists
- future command reuses existing M1161 outcome CSV
- future command restores fine target margins including 0.0005
- future command keeps wrong_matched_history as the only report variant
- future command avoids body-offset expansion or uses only the original body offset
- comparison with M1161 and M1166 is pre-registered
- no relocation replay, mining, outcome rerun, actor training, PPO, promotion, private holdout, conversion, threshold weakening, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- future command is too large for staged diagnostic use
- comparison to M1161 and M1166 is ambiguous
- relocation replay, mining, outcome rerun, actor training, PPO, promotion, private holdout, conversion, threshold weakening, or actor-input change starts

## Evidence Gates

- M1168 is design-only
- M1168 must not run relocation replay
- M1168 must not rerun mining
- M1168 must not rerun outcome gate
- M1168 must not train actor weights
- M1168 must not run PPO
- M1168 must not promote
- M1168 must not use private holdout
- M1168 must preserve actor inputs
- M1168 must not convert a surface

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run relocation replay
- do not rerun mining
- do not rerun outcome gate
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert a surface
- do not claim broad surface pass from the future microgrid diagnostic

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1168-v4-public-base-row15-promoted-relocation-target-microgrid-design
