# M361 Micro-Alpha Utility Audit

M361 audits whether the M360-promoted micro-alpha checkpoint is meaningful
enough to chain another PPO continuation from. It does not run PPO, actor
updates, or actor-input changes.

## Inputs

Previous public-gate base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

M360 public-gate base:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

The M360 candidate came from bounding the M356 best-feasible exact repair
candidate back toward the M352 public base.

## Evidence

| Signal | Value | Interpretation |
| --- | ---: | --- |
| Accepted alpha | 0.00025 | Nonzero but extremely small movement |
| First failing old-key alpha | 0.0005 | The direction is clipped after one more grid step |
| Exact M297 delta vs M352 | -0.000000119 | Numerically positive, but negligible |
| Exact M270 delta vs M352 | -0.000000060 | Numerically positive, but negligible |
| Full replay gates | 6 / 6 | Proof retained |
| Source-diverse gates | 5 / 5 | Source-diverse proof retained |
| Behavior success mean | 0.8625 | Equal to public behavior baseline |
| Behavior termination mean | 0.1375 | Equal to public behavior baseline |

M357 already showed that the direct M356 best-step candidate is not acceptable:
it passes exact M297/M270 but fails source-diverse old-key neighborhood proof
and M267/M264 first replay retention. M358 then showed that the same direction
only survives the old-key neighborhood gate at a micro alpha.

## Utility Judgment

M360 is useful as a conservative public-gate bookkeeping step. It keeps a
monotonic exact-objective lineage alive and proves that the M354/M356 direction
contains at least a tiny proof-safe component.

It is not useful evidence of meaningful driver improvement:

- the exact-objective improvement is around `1e-7`;
- behavior success, termination, and clearance are effectively unchanged;
- accepted movement is only `0.00025` of the M352-to-M356 direction;
- the first tested larger alpha already fails the old-key neighborhood gate.

Therefore, chaining longer PPO from the M360 checkpoint would be premature. The
current blocker is not "need more PPO"; it is that the exact M297/M270 repair
objective can still produce directions that pass exact objectives while pointing
almost immediately into old-key neighborhood proof failure.

## Decision

Classify M360 as:

```text
proof_safe_micro_step
```

Use it as the current public-gate base for lineage consistency, but do not treat
it as meaningful driver progress and do not start longer PPO from it as the next
research move.

Admit:

```text
m362-old-key-aware-exact-repair-design
```

The next design should make old-key neighborhood proof a first-class repair
residual or constraint, before another PPO proposal is accepted or lengthened.

## Requirements For M362

M362 should design, but not yet train, an old-key-aware exact repair/projection
stack that can address the M357/M358 failure mode:

- exact M297/M270 remain lexicographic no-regression objectives;
- old-key neighborhood accepted-case success and margin windows become
  first-class repair constraints or residuals;
- source-diverse protected gates remain promotion gates, not optional reports;
- line search must reject directions that only survive at negligible alpha;
- actor inputs remain the P0 human-view 72-dim online-GRU contract.

The intended outcome is a repair objective that can use PPO proposals without
collapsing into `alpha=0.00025` retention-only movement.
