# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Actor Contract

Mainline actor:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deployable inputs:

- ego kinematics / IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road / free-space / obstacle geometry in ego frame;
- recurrent state from past command-response history.

Not allowed in the deployable actor:

- `mu`, mass, CG, tire stiffness, brake scale, actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode or rule branch;
- `speed_ref`, `beta_target`, path error, heading error, path curvature;
- TTC, required clearance, oracle stopping distance, reference trajectory;
- collision/success/progress labels or any precomputed answer.

## Current Checkpoints

Latest public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Status: M400 promoted M399 alpha `0.05` as the current public-gate base after
six public replay surfaces and behavior seeds passed. M487-M529 did not promote
a new driver checkpoint.

Latest infrastructure smoke checkpoint:

```text
runs/m528_l0_current_observation_smoke/checkpoint.pt
```

Status: M528 smoke-only L0 current-observation checkpoint. It validates
baseline route and metadata, not driver performance.

## Current Blocker

```text
m559-targeted-collision-margin-config-family
```

M559 should implement the M558-approved collision/clearance-margin reward config
family and tests. This is config/test infrastructure only; no training or public
frozen-source diagnostics.

## Recent Evidence Line

- M520 valid-offset projected replay produced only a margin-only projected
  history signal: `1` source-narrow wrong-history proof candidate and `0` event
  rows.
- M524 found stronger natural history-value diagnostics: `480` L0 diagnostic
  candidates and `18` obstacle-completion event rows across natural M497/M487
  surfaces.
- M526 audited those event rows as source-diverse diagnostic evidence:
  `18` obstacle-completion drops across `2` surfaces, `5` probe seeds, and
  `2` targets, with projected event rows excluded.
- M527 defined the matched baseline family: L0 feedforward/current observation,
  L1 one-step command-response annotation, L2 finite command-response window,
  and L3 online GRU recurrent belief.
- M528 implemented explicit baseline metadata and an L0 smoke path while
  preserving the P0 no-wheel/no-oracle actor contract.
- M529 pre-registered the staged matched-baseline evaluation ladder so later
  L0/L2/L3 comparisons use shared budgets, seeds, configs, artifacts, and
  holdout discipline.
- M530 repeated the L0 current-observation smoke on seeds `3530` and `3531`.
  Both completed and wrote stable `L0_current_observation` plus
  `P0_human_view_no_wheel_no_oracle` metadata. The smoke returns are not
  interpreted as baseline evidence.
- M531 added machine-checkable L0/L2/L3 short-train configs with shared PPO
  budget, seed, task distribution, and P0 contract checks. L2 is the only config
  with `history_length = 4`; L0 and L3 use `history_length = 1`.
- M532 ran all three short-train configs on seed `3530`. L0 and L2 terminated
  in all eval episodes, while L3 had lower termination rate (`0.6`) and higher
  return on this one seed. This is route/artifact evidence only; repeat seeds
  and natural history-value surface evals are still required.
- M533 repeated the frozen configs on seeds `3531` and `3532`. Across seeds
  `3530`-`3532`, L3 has the best average return/termination (`45.7765`/`0.6`),
  L2 is second (`39.9082`/`0.6667`), and L0 is third (`27.3016`/`0.8667`).
  This is preliminary route evidence only; natural history-value surface eval is
  the next evidence layer.
- M534 designed that next layer. Existing recurrent-only tail gates are not
  enough for matched L0/L2/L3 evaluation, so the next tool must reconstruct
  natural source states with M399, replay L0/L2/L3 from the same frozen
  state/history, keep M526 rows as public diagnostics, and exclude projected
  surfaces from natural claims.
- M535 implemented that evaluator. It supports L0 current-frame replay, L2
  current-first stacked history replay, and L3 hidden construction from source
  observation prefixes. Focused tests pass, and a real 2-pair short-reveal smoke
  produced `6` outcome rows with `0` invalid rows.
- M536 scaled the evaluator to all nine matched short-train checkpoints on
  small short-reveal and warmup natural subsets. It produced `279` valid outcome
  rows total with one diagnosed short-reveal source-tail miss. L0/L2/L3 tied on
  success/completion/collision, while L3 had the best mean clearance margin.
  This is still route evidence only.
- M537 ran the full public frozen-source natural-surface matrix across M497
  short/warmup and M487 near/late splits. It produced `20196` valid outcome rows
  and no metadata or actor-contract failures. L3 leads aggregate success
  (`0.851901`), collision rate (`0.148099`), and mean clearance margin
  (`1.654668`) versus both L0 and L2, and is best on every per-surface success
  and margin table. The public M526 event overlay also favors L3, but this is
  still public diagnostic evidence rather than private generalization or
  checkpoint promotion.
- M538 converted the M537 result into exact paired source-key deltas. The join
  is complete (`6732` triplets, `0` incomplete). L3-L0 is robust across all
  surfaces and all three training seeds, with paired success delta `+0.020351`
  and margin delta `+0.144301`. L3-L2 is aggregate-positive and positive on all
  surfaces, but not seed-uniform: seed `3531` favors L2 with success delta
  `-0.013815` and margin delta `-0.143703`.
- M539 diagnoses the seed `3531` L2-over-L3 counterexample. It is broad rather
  than an event artifact: all four surfaces, all target groups, and all
  tail-offset groups have negative mean L3-L2 margin deltas. The `31` success
  regressions are all `L2 obstacle_completed -> L3 collision`, and non-event
  rows carry the success/collision regression. L3 seed `3531` has a systematic
  first-action shift relative to L2, so the next step should address matched
  training variance rather than promote L3 from public diagnostics.
- M540 designs the matched training-variance escalation. It keeps L2 as a real
  finite-window baseline, defines a staged ladder starting with 4096-step
  matched configs, separates L3-vs-L0 from L3-vs-L2 pass rules, and requires
  public paired diagnostics before any fresh-holdout claim. It also corrects the
  current lineage config paths to `configs/ppo_m531_matched_*_short_train.json`.
- M541 implements the matched 4096-step variance config family:
  `configs/ppo_m541_matched_l0_variance_4096.json`,
  `configs/ppo_m541_matched_l2_variance_4096.json`, and
  `configs/ppo_m541_matched_l3_variance_4096.json`. Tests verify valid P0
  history-baseline metadata, shared task distribution, and that the new configs
  differ from M531 only in `total_steps` and default seed. No training or
  promotion was performed.
- M542 runs the seed-3540 4096-step route pilot for all three levels. All runs
  complete and write valid P0 history-baseline metadata. Route eval strongly
  favors L2 (`return_mean = 77.992665`, `termination_rate = 0.2`) over L0
  (`20.334296`, `1.0`) and L3 (`21.645978`, `1.0`), but this is route evidence
  only and not a stable ranking or promotion claim.
- M543 evaluates those M542 checkpoints on the public M497/M487 frozen-source
  natural surfaces. L2 dominates aggregate success/margin (`0.866310`/`1.777833`)
  while L3 regresses below L0 (`0.670677`/`0.984809`). Paired L3-L2 deltas are
  strongly negative: success `-0.195633`, collision `+0.190731`, margin
  `-0.793024`. L3 is worst on every public surface, so the current recurrent
  recipe should be audited before expanding seeds.
- M544 audits that L3 regression. There is no P0 contract violation: config and
  metadata differences are the intended finite-window versus online-GRU fields.
  The issue is training behavior: L3 peaks early (`best_return = 52.598733` at
  step `1792`) but collapses late (`last4_return_mean = 23.259713`, final return
  `15.771149`), while L2 improves late. M543 failures include `423` L2-completed
  to L3-collision pairs and a large L3-L2 action shift. The next step is L3
  recurrent recipe repair design, not more runs of the same L3 setup.
- M545 designs that repair path. It keeps P0 inputs and L2 as a serious
  finite-window baseline, allows only L3 optimization/checkpoint-selection
  controls, pre-registers interval-checkpoint selection from route artifacts
  before public eval, and admits three M546 diagnostic configs: `fast_select`,
  `lr1e4`, and `lr5e5`. This is design-only and does not promote a checkpoint.
- M546 implements those L3-only repair configs and tests. `fast_select` adds
  `checkpoint_interval_steps = 512` while keeping `learning_rate = 0.0003`;
  `lr1e4` and `lr5e5` lower recurrent update aggressiveness and set
  `max_grad_norm = 0.25`. Tests verify all three keep the M541 L3 environment
  exactly and differ only by approved optimization/checkpoint-selection fields.
- M547 runs the three M546 repair configs and evaluates all saved interval/final
  checkpoints under the route-only selection rule. The result is negative:
  `0/27` saved checkpoints pass route health, and the best saved checkpoint
  (`fast_select` step `1024`) has return `22.941196` with termination `1.0`.
  The useful diagnostic is that all three variants peak in training at step
  `1792`, but that step is unsaved by the 512-step checkpoint cadence.
- M548 adds update-aligned `checkpoint_interval_steps = 256` configs for the
  same three L3 repair variants. Tests verify the only PPO difference from each
  M546 parent is checkpoint cadence, so every PPO update step can be saved and
  evaluated in the next route pilot.
- M549 runs that update-aligned route pilot. The previously missed step `1792`
  is now saved but fails deterministic route health for all variants. One saved
  checkpoint passes the M545 route-health gate: `fast_select_ckpt256` step
  `2816`, with route return `27.858686`, termination `0.8`, and mean clearance
  margin `0.594595`. Public frozen-source diagnostics are now admitted for that
  selected checkpoint, but no checkpoint is promoted.
- M550 runs those public diagnostics. M549 selected L3 improves over original
  M542 L3 (`success +0.053922`, margin `+0.164015`), but it still regresses
  against L0 (`success -0.076203`, margin `-0.235235`) and L2 (`success
  -0.141711`, margin `-0.629009`) on the same public surfaces. The next step is
  to redesign route-health screening, not to promote or matched-repeat this
  checkpoint.
- M551 redesigns the route-health screen. Route-screen v2 must use at least
  `64` public-neutral route episodes, include L0/L2/original-L3 references, and
  rank checkpoints by obstacle success, clearance margin, collision rate, then
  return. A candidate below L0 on route-screen v2 is blocked from public
  frozen-source eval.
- M552 retrospectively validates route-screen v2. It uses level-matched env
  configs so L2 keeps `history_length = 4`, evaluates 64 public-neutral route
  episodes, and rejects M549 selected L3 before public eval: M549 success
  `0.046875` is below L0 `0.062500` and far below L2 `0.609375`.
- M553 implements route-screen v2 as reusable harness infrastructure:
  `autodrift.route_screen_v2` supports named checkpoint policies, per-policy
  level-matched env configs, required L0/L2 references, candidate selection,
  `episodes.csv`, `policy_summary.csv`, `summary.json`, and explicit
  `uses_public_frozen_source_rows = false` provenance. The runner reproduces
  the M552 rejection of M549 selected L3.
- M554 designs the next L3 recurrent repair branch under route-screen v2. It
  freezes P0/env/task boundaries, restricts repair v2 to PPO stability controls,
  and admits exactly three small L3-only variants for M555:
  `epoch1_clip01`, `longseq_epoch1`, and `lowentropy_epoch1`.
- M555 implements those three L3-only configs and tests. All preserve the M548
  L3 env/task distribution, P0 actor contract, and update-aligned
  `checkpoint_interval_steps = 256`; differences are limited to M554-approved
  PPO stability controls.
- M556 trains those configs and evaluates `43` L3 interval/final candidates
  with route-screen v2. No checkpoint is admitted. `35/43` candidates pass L0
  binary success, but `0/43` pass L0 clearance margin and `0/43` pass collision
  tolerance. Public frozen-source diagnostics are blocked.
- M557 classifies that failure as collision-dominated after a small binary
  success gain. The best candidate converts `5` L0 collisions to completions,
  but also converts `7` L0 non-collision terminations and `3` L0 completions to
  collisions. Versus L2, `38` L2 completions become L3 collisions.
- M558 designs a targeted repair branch using existing obstacle collision and
  clearance-margin reward terms. It keeps P0 inputs, rotates the next
  route-screen v2 selection seed to `16560`, and admits exactly three M559
  reward variants.

## Near-Term Rule

Do not treat reset-hidden diagnostics, M528 smoke return, route eval, or
M537-M543 public diagnostics as private generalization evidence. The next branch
must use route-screen v2 before any public frozen-source eval. M550 remains
public diagnostic evidence and cannot support a private generalization claim.
Any later promotion requires proof retention, generalization retention, behavior
retention, no contract violation, and clear lineage.

## Sensor Profile Policy

Keep raw wheel, `v_parallel`, steering torque, suspension, and similar channels
as separate profile experiments only. Do not promote them into the main actor
without passing the same frozen-recipe proof gates as P0.

Suggested future profile ladder:

| Profile | Inputs |
| --- | --- |
| P0 | current no-wheel human-view baseline |
| P1 | commands + actuator feedback + `ax/ay/yaw_rate` + scene |
| P2 | P1 + steering torque / EPS current |
| P3 | P2 + raw four-wheel `R omega` |
| P4 | P3 + roll/pitch/vertical acceleration |
| P5 | P4 + suspension / wheel travel |

Every profile must use the same gate sequence: probe, frozen PPO recipe,
matched-current wrong-history, reset/zero-current ablation, and outcome boundary
proof. Do not tune PPO separately for one profile and compare it directly.
