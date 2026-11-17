import {
  Presentation,
  PresentationFile,
  text,
  shape,
  layers,
} from "@oai/artifact-tool";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.on("uncaughtException", (err) => {
  console.error("EXPORT_ERROR_NAME:", err?.name);
  console.error("EXPORT_ERROR_MESSAGE:", err?.message);
  console.error("EXPORT_ERROR_STACK:", String(err?.stack || "").split("\n").slice(0, 8).join("\n"));
  process.exit(1);
});

const outputDir = fileURLToPath(new URL("../deliverables/", import.meta.url));
const OUT = path.join(outputDir, "HNAI-FPGA_团队任务介绍.pptx");

const W = 1280;
const H = 720;
const C = {
  ink: "#17212B",
  muted: "#5C6670",
  navy: "#123047",
  blue: "#2F6B9A",
  cyan: "#3AA7A3",
  green: "#5A8F55",
  amber: "#D99A2B",
  coral: "#C85E4B",
  violet: "#6F5AA8",
  bg: "#F7F8F6",
  panel: "#FFFFFF",
  line: "#D6DDE2",
  paleBlue: "#E8F1F6",
  paleGreen: "#EAF3EA",
  paleAmber: "#FBF1DA",
  paleCoral: "#F7E6E1",
};

const p = Presentation.create();

function tx(value, x, y, w, h, style = {}) {
  return text(value, {
    position: { left: x, top: y },
    width: w,
    height: h,
    style: {
      fontFamily: "Arial",
      fontSize: 22,
      color: C.ink,
      ...style,
    },
  });
}

function box(x, y, w, h, fill = C.panel, line = C.line, radius = 8) {
  return shape({
    position: { left: x, top: y },
    width: w,
    height: h,
    fill,
    line: { color: line, width: 1.2 },
    borderRadius: radius,
  });
}

function pill(label, x, y, w, color, fill) {
  return layers({ position: { left: x, top: y }, width: w, height: 38 }, [
    shape({ width: w, height: 38, fill, line: { color, width: 1 }, borderRadius: 19 }),
    text(label, {
      position: { left: 12, top: 8 },
      width: w - 24,
      height: 22,
      style: { fontFamily: "Arial", fontSize: 15, color, fontWeight: 700, textAlign: "center" },
    }),
  ]);
}

function header(slide, title, kicker = "HNAI-FPGA team brief") {
  slide.compose(layers({ width: W, height: H }, [
    shape({ width: W, height: H, fill: C.bg, line: { color: C.bg, width: 0 } }),
    shape({ position: { left: 0, top: 0 }, width: W, height: 8, fill: C.navy, line: { color: C.navy, width: 0 } }),
    tx(kicker, 64, 32, 520, 22, { fontSize: 13, color: C.blue, fontWeight: 700 }),
    tx(title, 64, 58, 980, 52, { fontSize: 34, color: C.navy, fontWeight: 800 }),
    shape({ position: { left: 64, top: 118 }, width: 1130, height: 1.5, fill: C.line, line: { color: C.line, width: 0 } }),
  ]));
}

function addSlide(title, kicker) {
  const s = p.slides.add({ width: W, height: H });
  header(s, title, kicker);
  return s;
}

function bulletList(items, x, y, w, gap = 48, color = C.blue) {
  const children = [];
  items.forEach((item, i) => {
    const yy = y + i * gap;
    children.push(shape({ position: { left: x, top: yy + 7 }, width: 10, height: 10, fill: color, line: { color, width: 0 }, borderRadius: 5 }));
    children.push(tx(item, x + 24, yy, w - 24, gap, { fontSize: 21, color: C.ink }));
  });
  return children;
}

function metric(label, value, note, x, y, w, color, fill) {
  return layers({ position: { left: x, top: y }, width: w, height: 132 }, [
    shape({ width: w, height: 132, fill, line: { color, width: 1.2 }, borderRadius: 8 }),
    text(value, { position: { left: 18, top: 20 }, width: w - 36, height: 42, style: { fontFamily: "Arial", fontSize: 34, color, fontWeight: 800 } }),
    text(label, { position: { left: 18, top: 68 }, width: w - 36, height: 22, style: { fontFamily: "Arial", fontSize: 17, color: C.ink, fontWeight: 700 } }),
    text(note, { position: { left: 18, top: 94 }, width: w - 36, height: 28, style: { fontFamily: "Arial", fontSize: 13, color: C.muted } }),
  ]);
}

function flowNode(label, sub, x, y, w, color, fill) {
  return layers({ position: { left: x, top: y }, width: w, height: 92 }, [
    shape({ width: w, height: 92, fill, line: { color, width: 1.2 }, borderRadius: 8 }),
    text(label, { position: { left: 14, top: 14 }, width: w - 28, height: 24, style: { fontFamily: "Arial", fontSize: 18, color, fontWeight: 800 } }),
    text(sub, { position: { left: 14, top: 44 }, width: w - 28, height: 34, style: { fontFamily: "Arial", fontSize: 13, color: C.muted } }),
  ]);
}

function line(x1, y1, x2, y2, color = C.blue) {
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  const width = Math.max(Math.abs(x2 - x1), 2);
  const height = Math.max(Math.abs(y2 - y1), 2);
  if (Math.abs(y2 - y1) <= 4) {
    return shape({ position: { left, top: y1 - 1 }, width, height: 2, fill: color, line: { color, width: 0 } });
  }
  if (Math.abs(x2 - x1) <= 4) {
    return shape({ position: { left: x1 - 1, top }, width: 2, height, fill: color, line: { color, width: 0 } });
  }
  return shape({ position: { left, top }, width, height: 2, fill: color, line: { color, width: 0 } });
}

// 1
{
  const s = p.slides.add({ width: W, height: H });
  s.compose(layers({ width: W, height: H }, [
    shape({ width: W, height: H, fill: C.bg, line: { color: C.bg, width: 0 } }),
    shape({ position: { left: 0, top: 0 }, width: 18, height: H, fill: C.navy, line: { color: C.navy, width: 0 } }),
    tx("HNAI-FPGA", 72, 86, 780, 70, { fontSize: 54, color: C.navy, fontWeight: 900 }),
    tx("团队任务介绍：从自然语言硬件需求到经约束验证的 FPGA 设计包", 74, 164, 940, 82, { fontSize: 27, color: C.ink, fontWeight: 700 }),
    tx("目标不是商业企划，也不是论文写作分工；本次汇报用于对齐团队要完成的完整技术任务、工具链边界和阶段交付。", 76, 280, 850, 78, { fontSize: 22, color: C.muted }),
    metric("任务焦点", "NL2FPGA", "自然语言需求 -> HIS -> RTL/HLS/XDC/TB/报告", 76, 420, 310, C.blue, C.paleBlue),
    metric("技术闭环", "Verify", "语法、仿真、综合、时序、资源、功耗", 420, 420, 310, C.green, C.paleGreen),
    metric("目标产物", "Paper-ready", "先支撑一篇基础学术文章的实验与系统描述", 764, 420, 330, C.amber, C.paleAmber),
    tx("Source: current HNAI-FPGA IEEE Access draft, internal discussion, June 2026", 76, 660, 680, 20, { fontSize: 11, color: C.muted }),
  ]));
}

// 2
{
  const s = addSlide("这项任务要解决什么", "Task framing");
  s.compose(layers({ width: W, height: H }, [
    tx("核心问题", 82, 156, 180, 26, { fontSize: 18, color: C.blue, fontWeight: 800 }),
    tx("能否让一个平台接收自然语言硬件需求，并为非神经网络 AI 算法生成可部署、可验证的 FPGA 设计包？", 82, 190, 1000, 76, { fontSize: 28, color: C.ink, fontWeight: 800 }),
    ...bulletList([
      "现有 AI/FPGA 工具多聚焦 DNN 推理部署，入口通常是已训练模型或专家编写内核。",
      "通用 LLM 能生成 RTL 片段，但缺少物理约束、资源预算和时序闭合验证。",
      "团队任务是把“代码生成”升级为“约束验证闭环”和可复现实验系统。"
    ], 94, 310, 1030, 58, C.cyan),
    tx("边界：先完成学术基础版本，不展开商业模式；先验证系统闭环，不追求一次性覆盖所有 FPGA/算法。", 94, 540, 1000, 54, { fontSize: 22, color: C.coral, fontWeight: 700 }),
  ]));
}

// 3
{
  const s = addSlide("完整任务的输入与输出", "Deliverable definition");
  s.compose(layers({ width: W, height: H }, [
    box(80, 156, 300, 408, C.paleBlue, C.blue),
    tx("输入", 106, 184, 220, 30, { fontSize: 27, color: C.blue, fontWeight: 800 }),
    ...bulletList(["自然语言需求", "目标 FPGA 平台", "算法类别与约束", "性能/功耗/资源预算", "黄金模型或参考实现"], 112, 238, 220, 48, C.blue),
    box(490, 156, 300, 408, C.panel, C.line),
    tx("平台中间层", 516, 184, 240, 30, { fontSize: 27, color: C.navy, fontWeight: 800 }),
    ...bulletList(["HIS 结构化规格", "算法到架构映射", "硬规则检查器", "设计空间探索", "工具链调度与日志解析"], 522, 238, 230, 48, C.navy),
    box(900, 156, 300, 408, C.paleGreen, C.green),
    tx("输出", 926, 184, 220, 30, { fontSize: 27, color: C.green, fontWeight: 800 }),
    ...bulletList(["RTL / HLS 代码", "XDC 约束文件", "仿真 testbench", "综合/时序/功耗报告", "bitstream-ready checkpoint"], 932, 238, 230, 48, C.green),
    line(380, 360, 490, 360, C.blue),
    line(790, 360, 900, 360, C.green),
  ]));
}

// 4
{
  const s = addSlide("系统主线：不是单次生成，而是闭环迭代", "System loop");
  const nodes = [
    ["需求解析", "自然语言 -> HIS", 80, 190, C.blue, C.paleBlue],
    ["架构映射", "并行度、接口、数据表示", 275, 190, C.cyan, "#E4F5F3"],
    ["代码/约束生成", "RTL/HLS + XDC + TB", 470, 190, C.amber, C.paleAmber],
    ["工具链执行", "lint/sim/Vivado", 665, 190, C.violet, "#EEEAF7"],
    ["报告解析", "timing/resource/power", 860, 190, C.green, C.paleGreen],
    ["修正策略", "模板/参数/约束调整", 1055, 190, C.coral, C.paleCoral],
  ];
  const children = [];
  for (const [a,b,x,y,c,f] of nodes) children.push(flowNode(a,b,x,y,150,c,f));
  for (let i = 0; i < nodes.length - 1; i++) children.push(line(nodes[i][2] + 150, 236, nodes[i+1][2], 236, C.muted));
  children.push(shape({ position: { left: 155, top: 288 }, width: 975, height: 2, fill: C.coral, line: { color: C.coral, width: 0 } }));
  children.push(tx("feedback loop", 548, 304, 200, 18, { fontSize: 13, color: C.coral, fontWeight: 800, textAlign: "center" }));
  children.push(tx("闭环终止条件", 95, 405, 260, 28, { fontSize: 24, color: C.navy, fontWeight: 800 }));
  children.push(...bulletList(["功能仿真通过", "时序 WNS 满足目标", "LUT / FF / BRAM / DSP 未超预算", "功耗报告在预算内", "输出包可被复现"], 108, 454, 430, 38, C.green));
  children.push(box(640, 405, 500, 142, C.panel, C.line));
  children.push(tx("团队要实现的不是“让模型自信回答”，而是让每一步都有工具结果、结构化报告和可追溯日志。", 670, 438, 430, 76, { fontSize: 24, color: C.ink, fontWeight: 700 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 5
{
  const s = addSlide("七层架构：把平台拆成可分工模块", "Architecture");
  const layersData = [
    ["L1", "自然语言需求解析", "抽取算法、平台、约束、目标"],
    ["L2", "HIS 中间表示", "用 JSON schema 固化硬件意图"],
    ["L3", "算法到架构映射", "选择模板、并行度、数据位宽"],
    ["L4", "代码与约束生成", "RTL/HLS、XDC、testbench"],
    ["L5", "硬规则检查", "资源、接口、时钟、时序例外"],
    ["L6", "工具链反馈", "Verilator/iverilog/Vivado 报告"],
    ["L7", "设计空间探索", "参数搜索、回退、重新综合"],
  ];
  const children = [];
  layersData.forEach((r, i) => {
    const y = 150 + i * 66;
    const color = [C.blue, C.cyan, C.amber, C.violet, C.coral, C.green, C.navy][i];
    children.push(shape({ position: { left: 88, top: y }, width: 74, height: 46, fill: color, line: { color, width: 0 }, borderRadius: 6 }));
    children.push(tx(r[0], 104, y + 10, 44, 20, { fontSize: 19, color: "#FFFFFF", fontWeight: 900, textAlign: "center" }));
    children.push(box(174, y, 890, 46, C.panel, C.line, 6));
    children.push(tx(r[1], 198, y + 10, 250, 22, { fontSize: 19, color: C.ink, fontWeight: 800 }));
    children.push(tx(r[2], 474, y + 11, 520, 22, { fontSize: 17, color: C.muted }));
  });
  children.push(tx("每层都要定义：输入、输出、失败条件、日志格式、谁负责。", 170, 632, 820, 30, { fontSize: 22, color: C.coral, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 6
{
  const s = addSlide("工具链能力：Agent 调用的是受控工具，不是直接操作环境", "Tool layer");
  const cols = [
    ["代码检查", ["verilator --lint-only", "iverilog / xvlog", "SystemVerilog 语法与风格"]],
    ["功能验证", ["testbench 生成", "cocotb / xsim", "黄金模型对比"]],
    ["Vivado 批处理", ["synth / impl Tcl", "timing / utilization", "checkpoint 与报告"]],
    ["日志解析", ["ERROR/WARNING 提取", "WNS / TNS / utilization", "结构化 JSON 输出"]],
  ];
  const children = [];
  cols.forEach((c, i) => {
    const x = 80 + i * 292;
    const color = [C.blue, C.green, C.amber, C.coral][i];
    const fill = [C.paleBlue, C.paleGreen, C.paleAmber, C.paleCoral][i];
    children.push(box(x, 160, 250, 330, fill, color, 8));
    children.push(tx(c[0], x + 22, 190, 200, 28, { fontSize: 24, color, fontWeight: 900 }));
    children.push(...bulletList(c[1], x + 30, 252, 190, 56, color));
  });
  children.push(tx("安全边界：白名单命令、项目目录内运行、timeout、日志留存、禁止自动添加高风险 false_path。", 98, 560, 1040, 42, { fontSize: 22, color: C.navy, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 7
{
  const s = addSlide("XDC 约束：决定设计能否真正落到板子上", "Constraints track");
  s.compose(layers({ width: W, height: H }, [
    flowNode("顶层端口", "module ports", 90, 190, 180, C.blue, C.paleBlue),
    flowNode("板卡信息", "part/package/pin map", 90, 330, 180, C.cyan, "#E4F5F3"),
    flowNode("XDC 文件", "pin/clock/I/O/timing", 410, 260, 210, C.amber, C.paleAmber),
    flowNode("Vivado 检查", "report_drc + check_timing", 760, 260, 230, C.green, C.paleGreen),
    flowNode("修复建议", "缺失/冲突/危险约束", 1050, 260, 160, C.coral, C.paleCoral),
    line(270, 236, 410, 296, C.blue),
    line(270, 376, 410, 328, C.cyan),
    line(620, 306, 760, 306, C.amber),
    line(990, 306, 1050, 306, C.green),
    tx("第一版 XDC 检查范围", 110, 520, 320, 28, { fontSize: 24, color: C.navy, fontWeight: 900 }),
    ...bulletList(["端口是否被约束", "时钟是否 create_clock", "PACKAGE_PIN / IOSTANDARD 是否成对", "XDC 是否引用不存在端口", "false_path / multicycle_path 风险提示"], 124, 570, 900, 30, C.coral),
  ]));
}

// 8
{
  const s = addSlide("资源与功耗：从报告解析到预算判定", "Resource and power");
  s.compose(layers({ width: W, height: H }, [
    metric("BRAM", "budget", "容量、缓存、line buffer、表项", 80, 170, 240, C.blue, C.paleBlue),
    metric("DSP", "budget", "乘加阵列、并行度、复用策略", 360, 170, 240, C.green, C.paleGreen),
    metric("LUT/FF", "budget", "控制逻辑、状态机、接口 glue logic", 640, 170, 240, C.amber, C.paleAmber),
    metric("Power", "budget", "综合后粗估、实现后复核、活动文件增强", 920, 170, 240, C.coral, C.paleCoral),
    box(102, 380, 1010, 128, C.panel, C.line),
    tx("预算配置示例", 132, 405, 200, 24, { fontSize: 22, color: C.navy, fontWeight: 900 }),
    tx("target_device: xc7z020clg400-1   |   warn: 80%   |   fail: 100%   |   metrics: LUT / FF / BRAM / DSP / WNS / power", 132, 448, 920, 28, { fontSize: 20, color: C.ink, fontWeight: 700 }),
    tx("输出给团队的不是完整 Vivado 原始日志，而是 violations、top offenders、可行动的参数调整建议。", 132, 550, 920, 38, { fontSize: 22, color: C.muted }),
  ]));
}

// 9
{
  const s = addSlide("算法模板：把学术任务落到可实现的 FPGA 模块", "Algorithm templates");
  const items = [
    ["GA-FPGA", "selection / crossover / mutation / fitness", C.blue, C.paleBlue],
    ["RL-FPGA", "Q-table / policy / DQN inference / environment step", C.green, C.paleGreen],
    ["矩阵与向量", "systolic array / MAC reuse / fixed-point", C.amber, C.paleAmber],
    ["量化与近似", "位宽搜索 / LUT / PWL approximation", C.coral, C.paleCoral],
  ];
  const children = [];
  items.forEach((it, i) => {
    const x = 90 + (i % 2) * 560;
    const y = 175 + Math.floor(i / 2) * 180;
    children.push(box(x, y, 480, 120, it[3], it[2], 8));
    children.push(tx(it[0], x + 26, y + 24, 180, 28, { fontSize: 25, color: it[2], fontWeight: 900 }));
    children.push(tx(it[1], x + 26, y + 62, 400, 28, { fontSize: 18, color: C.ink }));
  });
  children.push(tx("模板库每个条目要带：参数、适用算法、资源估算式、接口规范、验证用例和回退策略。", 110, 575, 980, 34, { fontSize: 23, color: C.navy, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 10
{
  const s = addSlide("基准与实验：团队需要产出的可复现证据", "Benchmark plan");
  const headers = ["类别", "任务", "平台", "关键指标"];
  const rows = [
    ["GA", "0-1 Knapsack", "Zynq-7020", "吞吐 / 资源 / 设计时间"],
    ["GA", "TSP", "Artix-7 200T", "加速比 / DSP / BRAM"],
    ["GA", "Task Scheduling", "Zynq UltraScale+", "收敛速度 / 功耗"],
    ["RL", "GridWorld Q-learning", "Zynq-7020", "决策时延 / 正确性"],
    ["RL", "Pong-lite / DQN", "Artix-7 200T", "吞吐 / timing closure"],
    ["RL", "Path Planning", "Zynq UltraScale+", "能效 / 接口稳定性"],
  ];
  const children = [box(90, 160, 1090, 390, C.panel, C.line, 8)];
  const x0 = [120, 260, 560, 820];
  headers.forEach((h, i) => children.push(tx(h, x0[i], 188, 210, 24, { fontSize: 18, color: C.navy, fontWeight: 900 })));
  rows.forEach((r, ri) => {
    const y = 235 + ri * 45;
    children.push(shape({ position: { left: 110, top: y - 6 }, width: 1030, height: 1, fill: C.line, line: { color: C.line, width: 0 } }));
    r.forEach((v, i) => children.push(tx(v, x0[i], y, i === 3 ? 300 : 240, 22, { fontSize: 17, color: i === 0 ? C.blue : C.ink, fontWeight: i === 0 ? 800 : 500 })));
  });
  children.push(tx("这些不是 PPT 装饰表格，而是后续论文和系统可信度的证据清单。", 120, 595, 900, 30, { fontSize: 23, color: C.coral, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 11
{
  const s = addSlide("团队分工：按可交付模块组织", "Work packages");
  const wp = [
    ["WP1", "规格与 HIS", "需求 schema、例子、校验器", C.blue, C.paleBlue],
    ["WP2", "模板与生成", "GA/RL 模板、RTL/HLS 生成策略", C.green, C.paleGreen],
    ["WP3", "约束与验证", "XDC、testbench、黄金模型、仿真", C.amber, C.paleAmber],
    ["WP4", "Vivado 工具层", "Tcl、批处理、报告解析、错误定位", C.violet, "#EEEAF7"],
    ["WP5", "实验与数据", "基准复现、指标表、消融实验", C.coral, C.paleCoral],
    ["WP6", "集成与文档", "manifest、日志规范、复现实验包", C.navy, C.paleBlue],
  ];
  const children = [];
  wp.forEach((w, i) => {
    const x = 80 + (i % 3) * 390;
    const y = 160 + Math.floor(i / 3) * 185;
    children.push(box(x, y, 335, 128, w[4], w[3], 8));
    children.push(tx(w[0], x + 20, y + 22, 70, 26, { fontSize: 24, color: w[3], fontWeight: 900 }));
    children.push(tx(w[1], x + 92, y + 22, 200, 26, { fontSize: 23, color: C.ink, fontWeight: 900 }));
    children.push(tx(w[2], x + 22, y + 66, 280, 38, { fontSize: 17, color: C.muted }));
  });
  children.push(tx("每个 WP 的验收方式：代码/配置可运行、输出可复现、失败日志可解释。", 98, 565, 980, 34, { fontSize: 23, color: C.navy, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 12
{
  const s = addSlide("阶段计划：从最小闭环到论文级证据", "Milestones");
  const phases = [
    ["M1", "最小闭环", "需求 -> HIS -> 模板 -> lint/sim", C.blue, C.paleBlue],
    ["M2", "Vivado 接入", "synth/report/check_timing/XDC 检查", C.green, C.paleGreen],
    ["M3", "基准实验", "GA/RL 六个任务的指标表", C.amber, C.paleAmber],
    ["M4", "系统固化", "消融、复现包、论文图表支撑", C.coral, C.paleCoral],
  ];
  const children = [];
  phases.forEach((ph, i) => {
    const x = 95 + i * 280;
    children.push(shape({ position: { left: x, top: 220 }, width: 70, height: 70, fill: ph[4], line: { color: ph[4], width: 0 }, borderRadius: 35 }));
    children.push(tx(ph[0], x + 14, 240, 42, 26, { fontSize: 23, color: "#FFFFFF", fontWeight: 900, textAlign: "center" }));
    children.push(box(x - 32, 330, 210, 150, ph[5], ph[4], 8));
    children.push(tx(ph[1], x - 8, 360, 160, 26, { fontSize: 23, color: ph[4], fontWeight: 900, textAlign: "center" }));
    children.push(tx(ph[2], x - 12, 402, 170, 42, { fontSize: 16, color: C.ink, textAlign: "center" }));
    if (i < phases.length - 1) children.push(line(x + 74, 255, x + 248, 255, C.muted));
  });
  children.push(tx("建议节奏：先做能跑通的 M1/M2，再决定哪些实验数据足以支撑基础学术文章。", 110, 575, 960, 34, { fontSize: 23, color: C.navy, fontWeight: 800 }));
  s.compose(layers({ width: W, height: H }, children));
}

// 13
{
  const s = addSlide("下一步：本周需要对齐的决定", "Immediate decisions");
  s.compose(layers({ width: W, height: H }, [
    box(90, 160, 520, 360, C.panel, C.line, 8),
    tx("技术决定", 120, 195, 200, 28, { fontSize: 25, color: C.blue, fontWeight: 900 }),
    ...bulletList(["首个 FPGA 目标板卡与 Vivado 版本", "第一批算法模板：GA-KP 或 RL-GridWorld", "语法/仿真工具优先级", "预算配置字段和报告 JSON schema"], 132, 250, 420, 48, C.blue),
    box(670, 160, 520, 360, C.panel, C.line, 8),
    tx("协作决定", 700, 195, 200, 28, { fontSize: 25, color: C.green, fontWeight: 900 }),
    ...bulletList(["每个 WP 的负责人和接口人", "代码、实验、文档目录规范", "每周验收：能运行的工具输出", "论文只接收已经验证过的数据与图表"], 712, 250, 420, 48, C.green),
    tx("汇报结束时希望团队形成共识：我们先做一个可信的约束验证闭环，再让论文自然长出来。", 118, 585, 980, 40, { fontSize: 24, color: C.coral, fontWeight: 900 }),
  ]));
}

await mkdir(outputDir, { recursive: true });
const pptx = await PresentationFile.exportPptx(p);
await writeFile(OUT, Buffer.from(pptx.data));
console.log(OUT);
