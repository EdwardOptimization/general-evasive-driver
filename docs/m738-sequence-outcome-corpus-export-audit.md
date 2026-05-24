# M738 Sequence-Outcome Corpus Export Audit

## Purpose

M738 audits the M737 exported sequence-outcome corpus before any objective
design.

The question is:

```text
Should the project train on the M737 corpus now, repair the contrast corpus,
or first refresh broader extreme-fault scenario coverage?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M737 produced:

```text
result_class: sequence_outcome_corpus_hard_negative_sparse

positive_rows: 70
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
excluded_sentinel_rows: 3
duplicate_positive_keys: 0
missing_normal_matches: 0

unique_positive_seeds: 28
unique_positive_fault_family_pairs: 10
max_positive_seed_dominance: 0.085714

contrast_groups: 70
normal_rows: 70
positive_intervention_rows: 70
hard_negative_rows: 63
contrast_hard_negative_gate_pass: false

positive_corpus_gate_pass: true
training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

So the core positive corpus is clean:

```text
M734 non-sentinel outcome positives are preserved.
Every positive has a matched normal row.
No sentinel row is exported as a positive.
No duplicate positive key is exported.
```

But the same-source/same-horizon hard-negative contrast set is sparse:

```text
hard_negative_rows: 63
positive_rows: 70
```

This means M737 is not yet a complete contrast corpus for a
sequence-preference objective.

## Supported Claims

M738 supports:

```text
1. M737 successfully preserved M734's positive sequence-outcome evidence.

2. The sequence-outcome evidence is source-diverse enough to keep as a durable
   public corpus: 28 positive seeds, 10 positive fault-family pairs, and max
   seed dominance below 0.09.

3. Sentinel filtering worked: 3 sentinel positive candidates were excluded and
   0 sentinel rows entered the positive corpus.

4. A later objective can use the corpus as evidence, but only after deciding
   whether it needs complete hard negatives or a broader scenario refresh.
```

## Falsified Claims

M738 falsifies:

```text
1. M737 produced a complete same-source/same-horizon positive-vs-hard-negative
   contrast corpus.

2. The project should immediately run PPO or actor updates from M737.

3. The current public sequence-outcome rows are enough to close the user's
   broader extreme-fault coverage concern.
```

M738 does not falsify:

```text
1. The M734/M737 positive sequence-outcome evidence.

2. The command-response-history dependence hypothesis.

3. The possibility that richer extreme fault coverage will expose more
   outcome-critical self-ID cases.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The current M734/M737 source surface produces a clean positive corpus, but it
does not produce enough same-source/same-horizon action-only hard negatives for
every positive contrast group.
```

Not present:

```text
contract_violation: no actor input changed
proof_washout: no actor was trained
training_instability: no optimizer ran
promotion_gate_failure: no checkpoint was promoted
private_holdout_contamination: private holdout was not used
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate to high.

Reasons:

```text
1. M737's 70 positives all come from M734 public diagnostic rows.
2. The same sequence horizons and intervention variants are now known.
3. Repeated objective design on this fixed corpus could overfit the public rows.
4. The corpus is clean but not a private or fresh distribution.
```

Mitigation:

```text
Do not run PPO or promote from M737.
Do not design a large objective before refreshing scenario coverage or adding a
clear holdout/repair plan.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: extreme_fault_distribution_v3
```

Rationale:

```text
The positive corpus is worth preserving, but the hard-negative sparsity and the
user's coverage hypothesis point to the same blocker: the current source
surface is still too narrow for the next strong self-ID claim.
```

The next branch should answer:

```text
Are we failing to verify stronger self-identification because the scenario
distribution does not cover enough extreme and asymmetric vehicle failures?
```

M739 should be a design-only milestone for a broader data wave. It should not
train an actor or change the actor input contract.

## Required M739 Direction

M739 should design an extreme-fault v3 distribution with:

```text
current-model proxy faults:
  split-mu / side friction loss
  front/rear lateral authority drop
  brake fade and brake authority asymmetry
  drive authority loss
  steering lag, stuck, rate-limit, and saturation
  sensor delay, dropout, bias, and noise
  actuator deadzone and asymmetric lag
  mass, CG, payload, and yaw-inertia shifts
  fault onset during warm-up, pre-emergency, emergency, and recovery

four-wheel/high-fidelity-required faults:
  true single-wheel blowout
  true single-wheel brake failure
  true halfshaft or driveline break
  wheel-specific friction and normal-load effects
  wheel-speed, tire-temperature, and tire-pressure dynamics
```

The data wave should produce matched counterfactual cases:

```text
same visible geometry and ego state
different hidden fault condition
normal history vs reset / zero / delayed / wrong history
action and terminal margin divergence reported separately
```

M737 remains useful as a seed corpus and sanity check, but M739 should broaden
coverage before any objective or PPO branch.
