# M2 外部近邻工作补强记录

日期：2026-08-29

状态：M2 已通过并继续补强；不进入 M3

## 完成工作

对上一轮4项 identity-ready 工作执行精确一手来源核验：

- RealBench：arXiv:2507.16200v1；
- HWE-Bench：arXiv:2604.14709v3；
- CLOSER-Bench：arXiv:2607.16632v1；
- ChipVerilog：arXiv:2607.13079v3。

新增
[`../foundation/external-primary-source-evidence.md`](../foundation/external-primary-source-evidence.md)
记录19条版本化、section-bounded evidence claims，并更新 canonical registry、
BibTeX、阅读覆盖台账和 v1.7 当前文献总结。

## 对 SR2FPGA 定位的实质影响

### RealBench

RealBench 已有60个 module-level 和4个 system-level from-scratch generation
任务，并使用详细多模态 specification、100% line-coverage reference
testbench 和 formal equivalence。SR2FPGA 因此不能再声称此前不存在
system-level or hierarchical RTL generation。剩余区别必须落在完整公共工程
合同、匹配信息/预算、public-hidden authority、固定分母和 FPGA endpoint。

### HWE-Bench

417个真实 bug-fix task 表明大规模 repository repair、native regression、
跨工件协调和硬件语义定位均已有强 prior art。SR2FPGA 必须强调 starting
state：HWE-Bench 从已有仓库和 issue 出发，Paper-1 主任务从冻结需求事实
构造新 project package。

### CLOSER-Bench

CLOSER-Bench 已覆盖 budgeted spec-to-RTL、RTL-to-GDS、spec-to-GDS 及
simulator/synthesis/STA/P&R cost。但当前是一项设计/隐藏目标和十任务 pilot，
使用 Sky130/OpenROAD ASIC flow。SR2FPGA 不能笼统声称首次跨阶段 closure；
应限定 FPGA target、方法匹配、VPP 分母和 evaluator authority。

### ChipVerilog

ChipVerilog 已包含64个 OpenCores-derived、跨模块和 full-system target，
并用 equivalence/simulation 验证。其生成目标排除 testbench、macro 和辅助
文件，因此仍不同于完整项目包，但“首个多模块/系统生成”已经不可用。

## 证据状态

4项工作从 `identity-ready` 升为 `official-primary-page verified`。它们没有
本地 PDF hash，不计入27项 claim-ready 或3项 local-PDF source-verified。

当前分层：

- 27 claim-ready；
- 3 local-PDF source-verified；
- 4 official-primary-page verified；
- canonical BibTeX 34项全部至少完成一手身份核验。

本轮没有修改历史日志、实验协议、代码或 official evaluation authority。

