# M221 Stage2 Protected-Key Failure Audit

M221 audits why M220 is rejected after passing fixed objective, replay, and broad
behavior gates. No PPO, actor update, or actor input change is run here.

## Evidence

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted | Normal success | Normal margin | Wrong-history margin | Margin gap | Fixed M212 loss |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| m204_5209 | true | true | 0.189607 | 0.094102 | 0.095505 | 0.205221 |
| m217_10054 | true | true | 0.176641 | 0.083504 | 0.093137 | 0.204291 |
| m218_5214 | true | true | 0.199560 | 0.100863 | 0.098696 | 0.204267 |
| m219_5215 | false | true | 0.200679 | 0.102143 | 0.098536 | 0.204423 |
| m219_5216 | true | true | 0.199571 | 0.100774 | 0.098797 | 0.204240 |
| m220_5217 | false | true | 0.214602 | 0.119100 | 0.095502 | 0.204179 |
| m206_stage6 | false | true | 0.207450 | 0.109548 | 0.097903 | 0.158420 |
| m208_retry | false | true | 0.208742 | 0.111262 | 0.097479 | 0.158354 |

The old protected-key acceptance window is:

```text
min_normal_margin = 0.0
max_normal_margin = 0.2
min_margin_gap = 0.02
```

M220 does not lose normal success and does not collapse the wrong-history margin
gap. It fails because normal margin moves to `0.214602`, outside the old
near-boundary window.

## Interpretation

M220 is rejected by the pre-registered gate, but the failure is a proof-surface
window failure rather than a broad driving failure:

- fixed M212 objective improves;
- old M183, refreshed M193, and current M212 replay gates all pass;
- behavior seeds `9505` and `9506` retain success `0.8625`;
- reset-hidden and zero-all-response ablations still degrade success;
- the protected key remains outcome-sensitive in gap terms but is no longer
  close enough to the boundary under normal history.

This is the same failure class as M206/M208 and M219 seed `5215`. It shows that
ordinary PPO continuation tends to move the single historical key out of its
diagnostic margin window.

## Decision Table

| Option | Decision | Reason |
| --- | --- | --- |
| Promote M220 anyway | Reject | It failed the pre-registered protected key. Fixed objective and behavior are not sufficient. |
| Repeat M220 | Reject | The first stage2 already failed the protected key; repeating the same recipe would chase noise. |
| Loosen `max_normal_margin` after seeing M220 | Reject | That would invalidate the pre-registered protected-key gate. |
| Train lower clearance on the old key | Reject | It would optimize an evidence artifact against the actual driver objective. |
| Lower LR or increase generic anchor immediately | Defer | It might keep the old single key inside the window but would not fix single-key proof fragility. |
| Refresh current-family protected surface | Select | A multi-key current-family surface can distinguish true proof retention from one row becoming safer. |

## Selected Plan

M222 will refresh the protected surface for the current M217/M218/M219 retained
family:

```text
m217_10054  runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
m218_5214   runs/ppo_m218_guarded_from_m217_seed5214/checkpoint.pt
m219_5216   runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt
```

M219 seed `5216` remains the current best checkpoint until a new candidate
passes all gates.

The refresh will:

- reuse the same P0 zero-obstacle-relvel actor input profile;
- mine matched-current pairs on the previously productive M192 probe seeds
  `9520`-`9523`;
- run direct outcome continuation;
- relocate obstacle geometry into near-boundary conditions;
- require wrong-history success drops with diversity across physical pairs,
  source steps, checkpoints, targets, and margin buckets;
- keep the historical key in reports, but avoid making one old row the only
  protected proof.

## Decision

Decision:

```text
admit_m219_family_protected_surface_refresh
```

Next step:

```text
m222-m219-family-protected-surface-refresh
```

M222 may run mining and robustness gates only. PPO remains blocked until the
refreshed protected surface is documented and converted into objective/replay
gates.
