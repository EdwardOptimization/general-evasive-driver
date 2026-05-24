# m643-source-balanced-bc-v2-objective-design Research Review

## Summary

- Generated at UTC: 20260524T123515Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_bc_v2_objective_design_admit_m644
- Decision reason: M643 designs a conservative BC-v2 ladder with exact evaluator before head-only smoke and rejects direct full-actor sequence imitation from initial-state sequence targets

## Hypothesis

The M641/M642 corpus can support a conservative BC-v2 objective design that uses source-balanced masked sequence losses and exact pre/post gates before any actor update.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv, runs/m642_sequence_corpus_exact_objective_sanity/summary.json, docs/m642-sequence-corpus-exact-objective-sanity.md
- parent_config: experiments/manifests/m642-sequence-corpus-exact-objective-sanity.json
- parent_objective: design a source-balanced BC-v2 objective using the M641 exact sequence target corpus
- derived_from: m642-sequence-corpus-exact-objective-sanity
- blocked_by: m642-sequence-corpus-exact-objective-sanity
- supersedes: None
- invalidates: None

## Success Criteria

- design document specifies trainable scope and frozen components
- design document specifies masked source-balanced objective terms
- design document specifies exact sanity and retention gates
- design document specifies source-heldout evaluation discipline
- no actor update is run
- research validation passes

## Failure Criteria

- design changes actor input contract
- design allows training without exact objective gates
- design uses source ids or target labels as actor inputs
- design omits source-heldout validation discipline
- design admits promotion from objective-only improvement

## Evidence Gates

- design objective terms before actor update
- keep P0 human-view actor input contract unchanged
- separate train source rows from source-heldout validation rows
- pre-register exact objective non-regression gates
- pre-register replay and behavior retention gates before any checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not add source ids target labels or split labels to actor observations
- do not tune on source-heldout validation and report it as unbiased promotion evidence
- do not collapse source-balanced weights into raw row-count weights

## Failure Taxonomy

- none

## Scoreboard

- milestone: m643-source-balanced-bc-v2-objective-design
- type: infrastructure
- checkpoint: docs/m643-source-balanced-bc-v2-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_bc_v2_objective_design_admit_m644
- reason: M643 designs a conservative BC-v2 ladder with exact evaluator before head-only smoke and rejects direct full-actor sequence imitation from initial-state sequence targets

## Next Blocker

m644-source-balanced-bc-v2-objective-implementation
