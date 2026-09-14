# SR2FPGA Paper 1 M4 正式验收报告

日期：2026-09-04  
审查 checkout：`c32fce02db1e`  
结论：**部分通过；继续停留在 M4，不进入 M5**

## 一、验收范围

本次按 M3 十模块只读审查当前代码、注册合同、测试与 artifact。没有修改代码、
`paper1-freeze-v1.7`、M0–M5、实验协议或官方评价逻辑；没有运行真实模型、G5、
official campaign、正式 hidden evaluator、训练或证据晋升。

详细映射、实施计划、原型功能清单、流程与测试准备见
`../writing/m4-implementation-prototype-v1.7.md`。

## 二、验收证据

1. 十个 M3 模块均已映射到实际入口、注册合同、测试、证据边界和最小缺口
   【已核实】。
2. 当前 checkout 上执行 16 个相关测试模块，共 `333 passed`；它们只证明离线
   development/excluded conformance【已核实】。
3. 当前 G3c replay 输出显示 M3/M4/M5 的 HIS hash 相同、M4/M5 初始 `top.sv`
   hash 相同；目录无 positive `g3-acceptance-v1` 或 official authority【已核实】。
4. `docs/current-status.md` 的 2026-08-30 状态仍将 CD3–CD7、CD9 标为 partial，
   CD10 标为 missing；当前 checkout 的额外 replay 输出没有形成更高权威的验收
   artifact【已核实】。
5. 由测试、smoke、代码存在或历史 L4 推出方法有效性，均不成立【已核实】。

## 三、M4验收标准

| 标准 | 结论 | 理由 |
|---|---|---|
| 实施步骤可执行 | 通过 | 剩余工作已按 G3c→G3d→positive G3→G4a→G4b 排序，并给出 artifact-derived 完成判据 |
| 资源、工具、合同和依赖明确 | 通过 | 已区分 fake/deterministic G3 资源、public/hidden stores、registered contracts 与后续 official authority |
| 原型功能与十模块对应完整 | 通过 | 十模块都有入口、接口、测试和状态；未重新发明平行架构 |
| 原型足以支撑 Paper-1 核心验证 | **未通过** | positive G3 acceptance、剩余 repair/H-stage/missingness 场景和 official producer/verifier 尚缺 |
| 风险与备选方案明确 | 通过 | 对泄漏、越权、兼容绕过、缺失重编码和 shared-cost 误归因均给出 fail-closed 备选 |
| 图件与实施表达一致 | 通过（无需新图） | M3 Figure 2–4 已覆盖全览、matched treatment 和 evaluator/evidence authority；M4 新图会重复 |

## 四、阻断项

仅保留三个最小阻断包：

1. **G3c/G3d scenario closure**：补齐 artifact-derived M1/M5
   failure→diagnosis→patch→rerun、M5 H-stage correction、per-call capability、
   public/hidden/L3 failure 与两轴 missingness。
2. **Positive G3 authority**：实现并验证注册的 `g3-acceptance-v1`，由完整 refs
   派生，且 `official_outcome=false`、`pass_credit_authority=false`、
   `g4b_authorized=false`。
3. **后续验证入口**：G4a candidate benchmark/statistics closure，以及 G5 之后的
   G4b verifier、official hidden/VPP producer 和 command gate；不得提前授权。

## 五、正式裁定

M4 的“现状审查、实施计划和原型边界”已通过；“原型能够完整支撑 Paper-1 核心
验证”尚未通过。因此：

> **M4 部分通过，transition hold 保持；不允许进入 M5。**

下一授权动作应是实施 M4.1（G3c）和 M4.2（G3d）的最小缺口，而不是运行真实
模型或启动后续 gate。本报告本身不构成该实施授权。

