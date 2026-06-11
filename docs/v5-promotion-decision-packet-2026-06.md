# v5 晋升决定包（WP6.1，2026-06）

## 状态与声明边界

- kind：决定包（decision packet）。Phase-2 计划 WP6.1 交付物
  （`docs/research-plan-phase2-capability-boundary-tracking.md`）。
- 本文档**只陈述已测得的收益与负债并给出推荐，不执行晋升**。晋升与否的决定权在
  PI/用户。在决定作出之前，incumbent（v4）不变，v5 维持 candidate。
- 全部数字实查自下列已落盘工件；本文档不产生任何新测量，不做
  driver-performance / robustness / validation / ranking / high-fidelity
  verdict 声明。

## 对象

| 角色 | 模块 | DRIVER_ID |
|---|---|---|
| incumbent（部署中，未动） | `src/autodrift/active_safety_reflex_driver.py` | `active_safety_reflex_driver_m3105_incumbent_v4_no_regression` |
| candidate（待决定） | `src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py` | `active_safety_driver_v5_curvature_speed_governor_candidate`（`V5_POLICY_CONFIG` sha256 `2961746369567e5dafdcdbd5b41cb150c60a6fbb872dcf8f773ccca7523b2304`） |

v5 = 原样调用 v4 动作函数 + 两个 obs72-only 纯函数覆盖层（曲率可行性
grip-priority 调速器 + 防甩尾 ESC 修整）；覆盖层关闭时与 v4 逐位等价
（697 闭环步抽查 max |Δ| = 0.0）。

## 收益（实测）

数据源：`experiments/feasibility_audit/v5_panel_validation_summary.json` /
`v5_panel_validation_rows.csv`（4 面板 × 64 行 × 2 驱动 = 512 episode，
同进程同种子逐行配对；复跑字节级一致）、
`experiments/feasibility_audit/chrono_hf4_full_rows.csv`、
`experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv`。

1. **修复 2 行循迹出界**：feasible_only-0024（seed 602631）与
   fresh-0053（seed 501820）offtrack→success。面板效果：feasible_only
   60→61/64（aeb_feasible 55→56/57）；fresh 可行行 52/53→**53/53**。
2. **四面板 512 episode 零回退**：四个面板的 `rows_regressed_by_v5`
   全部为空——没有任何 v4-success 行被 v5 变为失败；old 面板（硬
   no-regression 面板）success 57/64、7 个失败行 outcome 逐行不变。
3. **holdout 消掉唯一可行行碰撞**：holdout 面板（种子基 701500，与已用
   192 种子不相交）v4 collision 1 → v5 **0**（holdout-0029，seed 707660：
   collision→offtrack，margin −0.046→+0.333；仍是失败行，不计修复）。
   v5 在全部 192 个可行标签行上 0 碰撞（v4 为 1）。
4. **Chrono::Vehicle 下无回归**：HF4 同场景双后端测量中 v5 在
   feasible-only 面板 **60/64**，与 current-sim 63/64 一致，0 个
   success→collision/offtrack 翻转
   （`docs/feasibility-route-hf4-full-discrepancy-2026-06.md`）。附注：v5
   设计针对的两行（fresh-0053、feasible_only-0024）在 Chrono 下本就不失败
   ——该失败模式部分是 current-sim 伪迹。
5. **+1 已到探测上限**：其余 3 个高速出界行（0010/0013/0029）经 84 个
   特权动作日程探测 0 通过（0013 差 ~8.4 m，高置信物理不可达），在反射类
   控制上限之外；feasible_only 只 +1 不是 v5 调参不足。

## 负债（实测）

数据源：`experiments/feasibility_audit/reflex_overshoot_recovery.json`
（6912 回合超调恢复网格，`docs/selfid-reflex-recovery-budget-2026-06.md`）、
`experiments/feasibility_audit/v5_panel_validation_summary.json`（old 面板
margin guard）。

1. **深超调域 v5 纯减分**：同 cell 同 seed 严格配对——无障 1152 对：
   both 809、**v4_only 26、v5_only 0**；有障 1152 对：**v4_only 28、
   v5_only 0**。即 v5 没有救回任何 v4 救不回的超调回合，反而丢掉
   26–28 个 v4 本可救回的回合；双双恢复时 v5 平均多花 1.94 步、多丢
   0.086 m。
2. **高速释刹方向在深滑移域是错的**：无障格 off_track 计数
   μ=0.6：4→14、μ=0.85：1→14（v4→v5；governor 在深滑移+高速下释放刹车，
   方向与救车需求相反）。
3. **old 面板 7 不可避行 margin guard（容差 1e-3）4/7 通过**：3 行恶化
   −0.021…−0.059 m。背景：该量低于这些速度下的单步离散量子
   （0.27–0.36 m/step）；0007 的撞击速度反而更低（17.23→16.48 m/s）；
   obstacle_yield 三组参数扫描证明这 3 行恶化与保留任何修复不可同时满足。
4. **原目标未全达**：feasible_only 60→61（+1 < 目标 +3，见收益第 5 条的
   上限证据）；ESC 层仅由 1 个低速甩尾行驱动设计，样本少。

## 权衡判定（实测结论的并列陈述）

v5 的 panel 收益（高速循迹出界 −2 行、可行行碰撞 1→0）与深超调救车损失
（−26…−28 回合、μ≥0.6 出界 4→14/1→14）是**真实测得的双向权衡**，不是噪声：
两者都来自确定性、逐 seed 配对的测量，且复跑一致。

## 推荐（本文档建议；决定权在用户）

**仅在加入「深滑移让位 v4 制动仲裁」条款后晋升**：当深滑移指征
（beta/yaw 盈余大，即超调恢复域）出现时，governor/ESC 让位给 v4 的制动
仲裁；否则保持 v4 为 incumbent、v5 维持 candidate。依据：
`docs/selfid-reflex-recovery-budget-2026-06.md` 推断第 4 条 +
计划 WP6.1。合并后的让位条款本身需先在 recovery 网格上验证
（验收方向：配对 v4_only 26/28 → ~0，且 panel 修复不丢失）。

### 晋升前置（计划 WP6.1 原文绑定规则）

> **If promoted, before WP2 consumes any recoverable-set surface: re-run
> (a) the recovery panel, (b) the fixed feasible-row panel, (c) the
> fresh-seed panel on the merged controller; the WP2 verifier binds to the
> merged controller's re-measured boundary.** If not promoted, WP2 binds to
> the v4 surface as measured.

即三项复测全部在**合并控制器**上重新跑：
(a) recovery panel（`scripts/feasibility_audit/reflex_overshoot_recovery.py`）；
(b) 固定可行行 panel（feasible-only，
`scripts/feasibility_audit/fresh_panel_retest.py --feasible-only-panel`）；
(c) fresh-seed panel（同脚本 Part B）。WP2 verifier 绑定合并控制器复测出的
recoverable-set 边界；不晋升则绑定 v4 已测 surface。

### 选项清单（留给用户勾选）

| 选项 | 内容 | 后果 |
|---|---|---|
| A（推荐） | 加深滑移让位条款后晋升合并控制器 | 需先实现让位条款 + 在 recovery 网格验证 + 三项复测；WP2 绑定合并边界 |
| B（现状默认） | 不晋升，v4 维持 incumbent | WP2 直接绑定 v4 已测 surface；v5 的 2 行修复与碰撞 1→0 收益放弃 |
| C（不推荐） | 原样晋升 v5 | 实测代价：深超调域丢 26–28 个可救回合、μ≥0.6 无障出界 4→14/1→14 |

## 工件清单

- `experiments/feasibility_audit/v5_panel_validation_summary.json` / `v5_panel_validation_rows.csv`
- `experiments/feasibility_audit/reflex_overshoot_recovery.json`
- `experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv`
- `experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json`
- `experiments/feasibility_audit/chrono_hf4_full_rows.csv`
- `docs/feasibility-audit-v5-highspeed-tracking-repair-2026-06.md`（Track B 测量全文）
- `docs/selfid-reflex-recovery-budget-2026-06.md`（测量 C 全文）
- `docs/feasibility-route-hf4-full-discrepancy-2026-06.md`（HF4 全量）
- `docs/research-plan-phase2-capability-boundary-tracking.md`（WP6.1 条款）

## PI disposition (2026-06-12)

Promotion is deferred: not a live question while the research program is
ongoing. v4 stays deployed; v5 remains a filed candidate with this packet
as its record; revisit at research completion.
