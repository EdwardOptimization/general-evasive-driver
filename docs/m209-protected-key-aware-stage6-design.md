# M209 Protected-Key-Aware Stage6 Design

M209 designs the next step after M206 and M208 both failed the same protected
key. No PPO, actor update, or actor input change is run in this milestone.

## Evidence Reviewed

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted | Normal success | Normal margin | Wrong-history margin | Margin gap | Fixed M193 loss |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| m204_stage5 | true | true | 0.189607 | 0.094102 | 0.095505 | 0.158474873 |
| m206_stage6 | false | true | 0.207450 | 0.109548 | 0.097903 | 0.158420356 |
| m208_retry | false | true | 0.208742 | 0.111262 | 0.097479 | 0.158354129 |

M206 and M208 both preserve broad evidence:

- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay drops remain `16/16` and `17/17`;
- refreshed M193 replay drops remain `14/14`;
- reset-hidden and zero-all-response degradation remains visible.

The repeated failure is narrower: both stage6 updates move the selected key
above the pre-registered near-boundary acceptance window.

```text
reference max_normal_margin = 0.2
M206 normal margin = 0.207450
M208 normal margin = 0.208742
```

The wrong-history margin gap does not collapse. It slightly increases relative
to M204.

## Interpretation

The protected key is failing as a proof artifact, not as a broad behavior
artifact. The policy is making the protected case safer under normal history,
which is good for driving, but bad for a single near-boundary diagnostic row.

Therefore the next step should not train the driver to reduce clearance just to
keep the old key inside `max_normal_margin = 0.2`.

## Candidate Directions

| Direction | Decision | Reason |
| --- | --- | --- |
| Protected boundary anchor | Defer | A loss that directly pulls normal margin back under `0.2` would optimize the evidence artifact against the driver objective. It may be useful only if it is framed as action/hidden retention, not lower-clearance retention. |
| Lower update magnitude | Defer | M196 already uses very small learning rate `1e-6` and a strong action anchor. Reducing updates may pass the old key, but it does not fix the single-key fragility. |
| Boundary window refresh | Select | A multi-key, source-diverse protected surface can distinguish real self-ID retention from one row becoming too safe. This preserves the proof standard without retroactively loosening M206/M208. |

## Selected Plan

M210 will refresh the protected surface around the current retained family:

```text
m199_5201  runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
m202_5206  runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
m204_5209  runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

M204 remains the current best checkpoint until a future candidate passes all
gates.

The refresh should:

- mine fresh matched-current pairs under the same P0 zero-obstacle-relvel actor
  input profile;
- include wrong-history, reset-hidden, zero-current-response, zero-action-history,
  and delayed-history interventions;
- relocate obstacle geometry to near-boundary conditions;
- require source diversity across physical pairs, source steps, checkpoints,
  targets, and margin buckets;
- build the next protected evidence from multiple rows, not one key.

## Future Gate Policy

The old key remains historical evidence and should keep being reported, but it
should not be the only protected proof row.

Future candidates should be judged by a refreshed protected set with two
separate notions:

- driver retention: normal-history success and broad behavior must not regress;
- proof retention: enough pre-registered near-boundary wrong-history rows must
  remain outcome-sensitive to support the self-ID claim.

A row that becomes safer under normal history can be logged as
`improved_out_of_boundary`, but the candidate still needs enough other
pre-registered rows inside the near-boundary window. This avoids weakening the
proof after seeing results while also avoiding a perverse incentive to reduce
clearance.

## Decision

Decision:

```text
admit_current_best_protected_surface_refresh
```

Next step:

```text
m210-current-best-protected-surface-refresh
```

M210 may run mining and robustness gates only. PPO remains blocked until the
refreshed protected surface is documented and converted into a runnable
objective/gate plan.
