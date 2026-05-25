# M887 V4 Enriched Pair-Delta Objective-Only Probe Audit

## Purpose

M887 audits the M886 no-PPO objective-only probe before any replay/proof gate.

The audit question is:

```text
Is M886's exact-admissible objective-only result clean enough to justify
closed-loop replay/proof evaluation of one candidate checkpoint?
```

M887 is audit-only:

```text
no training
no PPO
no checkpoint promotion
no actor input change
```

## Source Artifacts

Primary run:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe
```

Primary candidate family:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_001.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_0025.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_005.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_01.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_02.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_05.pt
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
```

## Contract Checks

M886 passed the audit-only contract checks:

```text
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
exact_losses_finite: true
training_nonfinite: false
actor_input_contract_changed: false
residual_head_changed: false
ppo_used: false
promoted: false
```

The raw actor checksum changed, as expected for an objective-only actor update,
but the residual checksum stayed unchanged:

```text
residual_checksum_before == residual_checksum_after
```

## Exact Objective Result

Raw candidate:

```text
train_weighted_loss_delta: -0.0008391377425962521
objective_eval_regression: -0.00040940263054589643
source_holdout_regression: -0.0007514722493229264
new_signature_holdout_regression: -0.0003465016682941968
```

The raw candidate improves exact train and holdout losses, but it is not
directly admissible because M885 required interpolation before acceptance.

Interpolation grid:

```text
alpha    train_delta          max_holdout_regression   exact_admissible
0.001    -0.0000008488855054  -0.0000003576278687      true
0.0025   -0.0000021385569726  -0.0000007947285969      true
0.005    -0.0000041934751696  -0.0000016291936238      true
0.01     -0.0000084258856312  -0.0000033775965373      true
0.02     -0.0000167767847739  -0.0000068744023640      true
0.05     -0.0000419909915617  -0.0000173250834148      true
0.10     -0.0000838603704207  -0.0000345706939697      true
```

All seven nonzero interpolation candidates improved the exact train objective
and did not regress the registered exact public holdouts.

## Action Drift

M886 reports small action drift on the M883/M880 exact rows:

```text
raw_candidate all action_l2_mean: 0.0011987320806356033
alpha_0_1 all action_l2_mean: 0.00011984185470731906
```

This is small enough for a replay/proof gate probe. It is not enough for
promotion, because exact one-step objective metrics do not establish closed-loop
behavior retention.

## Candidate Selection

M887 selects the following checkpoint for the next replay/proof gate:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
```

Reason:

- it is the largest tested interpolation that remains exact-admissible;
- it gives the best exact train improvement among nonzero alphas;
- exact holdout deltas are nonpositive;
- action drift remains tiny relative to the raw candidate and typical action
  scale.

Fallback candidate if replay/proof gates fail due a boundary cliff:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_05.pt
```

## Caveats

M887 does not reduce the main caveats from M884-M886:

- exact objective rows are public workflow artifacts;
- source-holdout is not a new source holdout;
- eval and new-signature holdouts are degradation-only;
- 78055 is still absent from new accepted pair-delta rows;
- no closed-loop replay, behavior seed, protected-row, or generalization gate
  has run for the M886 candidates.

## Decision

Decision:

```text
v4_enriched_pair_delta_objective_only_probe_audit_admit_replay_gate
```

Next:

```text
m888-v4-enriched-pair-delta-replay-proof-gate-design
```

M888 should design the smallest closed-loop replay/proof gate stack for
`alpha_0_1.pt`, with `alpha_0_05.pt` as fallback. It must keep PPO and
promotion blocked until proof retention is evaluated.
