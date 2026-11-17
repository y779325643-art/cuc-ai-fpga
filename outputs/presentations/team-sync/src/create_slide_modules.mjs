import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const slidesDir = path.join(__dirname, "slides");

const deckData = {
  palette: {
    bg: "#F7F9FC",
    ink: "#162033",
    muted: "#5B6475",
    line: "#D8DEE9",
    blue: "#2457D6",
    cyan: "#00A6A6",
    green: "#2E8B57",
    amber: "#C47A1B",
    red: "#B23B3B",
    navy: "#0E1B2A",
    white: "#FFFFFF",
    chip: "#EAF0FF",
  },
  slides: [
    {
      type: "cover",
      title: "HNAI-FPGA 项目技术同步",
      kicker: "自然语言驱动、约束验证的 FPGA 设计生成平台",
      subtitle: "团队内部汇报 | 技术路线、工具链闭环与下一步工程化",
      date: "2026-06-04",
      claim: "目标不是生成一段 RTL，而是交付可验证、可综合、可部署的 FPGA 设计包。",
      metrics: [
        ["96.4%", "RTL 编译成功率"],
        ["88.7%", "时序闭合率"],
        ["29-38x", "相对 CPU 加速"],
        ["94-97%", "设计时间缩短"],
      ],
    },
    {
      type: "problem",
      title: "为什么要做：非 DNN 算法的 FPGA 落地仍然很重",
      claim: "现有 FPGA AI 工具多围绕 DNN 推理，GA/RL/路径规划/调度优化仍依赖专家手工硬件设计。",
      points: [
        ["传统流程周期长", "算法规格、架构选择、RTL/HLS、仿真、综合、约束迭代通常需要 48-120 小时。"],
        ["专业门槛高", "需要同时掌握 HDL/HLS、时序闭合、资源映射、板级验证和工具链交互。"],
        ["LLM-to-RTL 不够", "通用大模型能产出代码片段，但缺少物理约束验证，复杂设计容易时序失败或资源超限。"],
        ["现有工具覆盖窄", "Vitis AI、hls4ml、FINN 更适合已训练 DNN 模型，不解决非 DNN 算法到工程包的闭环。"],
      ],
    },
    {
      type: "architecture",
      title: "项目定位：从自然语言到 FPGA 工程包的闭环平台",
      claim: "HNAI-FPGA 将需求、架构、代码、约束、仿真、综合和部署打包在一个可追踪流水线中。",
      layers: [
        ["1", "自然语言需求接口", "抽取算法、平台、性能、接口、功耗和验证条件"],
        ["2", "HIS 中间表示", "把模糊需求转为机器可验证的硬件意图规范"],
        ["3", "算法到架构映射", "选择模板、并行度、流水深度、存储结构"],
        ["4", "RTL/HLS 生成", "输出模块、wrapper、testbench、XDC 和 manifest"],
        ["5", "硬规则检查器", "时序、资源、接口、数值、功耗、CDC、复位、综合规则"],
        ["6", "多物理工具闭环", "Verilator/Vivado/Quartus 报告结构化反馈"],
        ["7", "DSE 与部署", "帕累托搜索、报告、API、bitstream/checkpoint"],
      ],
    },
    {
      type: "workflow",
      title: "工程闭环：Agent 负责调度，EDA 工具负责验证",
      claim: "Agent 不直接“相信”生成结果，而是把每一步交给可执行工具验证，再用报告驱动下一轮修正。",
      steps: [
        ["需求解析", "自然语言 -> HIS JSON"],
        ["模板实例化", "GA/RL/路径规划等算法模板"],
        ["代码与约束", "RTL/HLS + TB + XDC"],
        ["快速检查", "schema、lint、规则、CDC/复位"],
        ["仿真", "Verilator/xsim + 黄金模型"],
        ["综合实现", "Vivado/Quartus batch"],
        ["报告解析", "资源、时序、功耗、DRC"],
        ["迭代输出", "修正参数或交付设计包"],
      ],
    },
    {
      type: "tools",
      title: "工具层实现：把命令行能力封装成受控 Tool API",
      claim: "第一版工具层应当小而可靠：白名单命令、固定输入输出、timeout、日志解析、项目目录隔离。",
      groups: [
        ["语法/仿真", ["verilator --lint-only", "iverilog / xvlog", "xsim / Verilator + golden model"]],
        ["Vivado 批处理", ["vivado -mode batch -source run.tcl", "report_utilization / report_timing_summary", "report_power / report_drc / check_timing"]],
        ["约束与报告", ["parse_xdc / validate_pins", "parse_vivado_log", "budget_check / power_check"]],
      ],
      note: "当前工作区没有 RTL/Vivado 工程文件，PPT 中将工具链作为待工程化模块呈现。",
    },
    {
      type: "xdc",
      title: "XDC 约束：从“能综合”推进到“能落板”",
      claim: "XDC 是连接 RTL 逻辑和真实 FPGA 物理世界的关键文件，Agent 必须能检查但不能随意猜测。",
      checks: [
        ["端口覆盖", "top ports 是否都有 PACKAGE_PIN / IOSTANDARD"],
        ["时钟完整性", "主时钟是否 create_clock；生成时钟是否声明"],
        ["接口时序", "set_input_delay / set_output_delay 是否匹配外设协议"],
        ["危险例外", "false_path / multicycle_path 必须解释来源，不能自动滥加"],
        ["板卡一致性", "pin map、IO bank、电压、差分对与目标 board profile 对齐"],
      ],
      snippet: [
        "set_property PACKAGE_PIN H16 [get_ports clk]",
        "set_property IOSTANDARD LVCMOS33 [get_ports clk]",
        "create_clock -period 8.000 -name clk [get_ports clk]",
      ],
    },
    {
      type: "metrics",
      title: "资源/功耗/性能：把 Vivado 报告转成可决策指标",
      claim: "BRAM、DSP、LUT、FF、功耗和 timing slack 都应进入结构化预算检查，而不是停留在长日志里。",
      cards: [
        ["资源预算", "LUT / FF / DSP / BRAM / URAM", "超过 80% 预警，超过 100% 阻断"],
        ["时序质量", "WNS / TNS / critical path", "WNS >= 0 才能进入交付候选"],
        ["功耗估计", "static / dynamic / total power", "结合 SAIF/VCD 活动文件可提高可信度"],
        ["模板调参", "并行度 / 流水深度 / 位宽", "资源超限时自动降并行或换存储策略"],
      ],
      examples: [
        ["GA-KP", "48 DSP", "36 BRAM", "7.2 W"],
        ["RL-PONG", "112 DSP", "68 BRAM", "6.4 W"],
      ],
    },
    {
      type: "evidence",
      title: "当前论文级结果：证明路线可行，但仍需板级验证",
      claim: "现有结果来自 Vivado OOC 综合、Verilator 功能仿真和功耗估计，应作为技术可行性指标，而非量产承诺。",
      bars: [
        ["RTL 编译成功率", 96.4, "基础 LLM 61.2%"],
        ["仿真通过率", 92.1, "完整流水线"],
        ["时序闭合率", 88.7, "基础 LLM 34.1%"],
        ["资源超限率", 1.4, "越低越好"],
      ],
      callouts: [
        "六个 GA/RL 基准覆盖背包、TSP、调度、GridWorld、Pong-lite、路径规划。",
        "相对 CPU 获得 29.4x 至 37.9x 平均吞吐加速。",
        "相比专家手工开发，端到端设计时间缩短 94% 至 97%。",
      ],
    },
    {
      type: "templates",
      title: "算法模板库：让生成结果落在可验证架构边界内",
      claim: "模板库不是代码片段仓库，而是包含参数、资源模型、接口、验证方式和约束边界的工程资产。",
      templates: [
        ["GA", "PopulationMemory、FitnessArray、Selection、Crossover、Mutation、LFSR RNG"],
        ["RL-Q", "StateEncoder、Q-table BRAM、argmax、reward update、epsilon-greedy"],
        ["DQN", "ConvEngine、FC、INT8 quant、ControlScheduler、frame buffer"],
        ["通用扩展", "矩阵乘、路径规划、调度优化、控制、信号处理、图算法"],
      ],
      formula: "estimate = f(parallel_lanes, pipeline_depth, data_width, memory_type)",
    },
    {
      type: "mvp",
      title: "MVP 切法：先做可跑通的最小闭环",
      claim: "不要一开始承诺通用硬件自动设计；第一版目标是自动跑检查、读报告、给出可执行修正建议。",
      lanes: [
        ["输入", "HIS / board profile / algorithm template / budget.yaml"],
        ["生成", "RTL/HLS skeleton、testbench、XDC template、Vivado Tcl"],
        ["验证", "lint、仿真、综合、timing、power、DRC"],
        ["输出", "诊断报告、资源表、失败定位、下一轮参数建议"],
      ],
      done: [
        "2 个端到端模板：GA-KP 与 RL-GW",
        "1 个主板卡 profile：ZCU104 或 Zynq-7020",
        "可重复生成 reports/ 与 summary.json",
      ],
    },
    {
      type: "team",
      title: "团队分工：把研究问题拆成可并行工程流",
      claim: "团队同步的重点是明确边界：算法模板、RTL/约束、工具执行、报告解析、产品化展示可以并行推进。",
      roles: [
        ["算法模板", "GA/RL 参考实现、HIS 字段、参数范围、资源估计"],
        ["FPGA/RTL", "模板模块、AXI wrapper、testbench、XDC、板级 bring-up"],
        ["工具链 Agent", "Tool API、Vivado Tcl、日志解析、timeout、白名单安全"],
        ["验证评估", "golden model、仿真用例、资源/功耗/时序对比表"],
        ["产品文档", "Web 仪表盘原型、报告导出、试点案例材料"],
      ],
    },
    {
      type: "roadmap",
      title: "下一步：从文稿成果走向可演示工程",
      claim: "近期目标应定义为“可演示、可复现、可试点的 FPGA 设计生成 MVP”。",
      roadmap: [
        ["第 1 阶段", "环境与工具闭环", "安装/配置 Verilator + Vivado batch；跑通 lint、仿真、综合、报告解析。"],
        ["第 2 阶段", "模板与约束", "完成 GA-KP/RL-GW 模板、board profile、XDC 检查和预算规则。"],
        ["第 3 阶段", "板级 demo", "在 ZCU104/Zynq-7020 完成 bitstream、主机 API、功耗/性能实测。"],
        ["第 4 阶段", "试点交付", "打包报告、案例白皮书、课程/科研试点流程。"],
      ],
      asks: [
        "确定首块开发板与 Vivado 版本",
        "整理第一个可公开 demo 的算法输入",
        "建立 reports/summary.json 的统一格式",
      ],
    },
  ],
};

const helper = String.raw`
const P = ${JSON.stringify(deckData.palette, null, 2)};

function addBg(slide, ctx, title, claim) {
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.bg });
  ctx.addShape(slide, { x: 0, y: 0, width: 12, height: ctx.H, fill: P.blue });
  ctx.addText(slide, { x: 54, y: 34, width: 820, height: 42, text: title, fontSize: 28, bold: true, color: P.ink, typeface: "Microsoft YaHei" });
  ctx.addText(slide, { x: 54, y: 80, width: 930, height: 42, text: claim, fontSize: 17, color: P.muted, typeface: "Microsoft YaHei" });
  ctx.addText(slide, { x: 1110, y: 42, width: 110, height: 24, text: "HNAI-FPGA", fontSize: 13, bold: true, color: P.blue, align: "right", typeface: "Aptos" });
}

function addFooter(slide, ctx, n) {
  ctx.addShape(slide, { x: 54, y: 674, width: 1070, height: 1.2, fill: P.line });
  ctx.addText(slide, { x: 54, y: 686, width: 520, height: 20, text: "团队内部技术同步 | source: project manuscript & business plan", fontSize: 10, color: P.muted, typeface: "Aptos" });
  ctx.addText(slide, { x: 1160, y: 686, width: 44, height: 20, text: String(n).padStart(2, "0"), fontSize: 11, color: P.muted, align: "right", typeface: "Aptos" });
}

function card(slide, ctx, x, y, w, h, opts = {}) {
  ctx.addShape(slide, { x, y, width: w, height: h, fill: opts.fill || P.white, line: ctx.line(opts.line || P.line, opts.lineWidth || 1) });
}

function label(slide, ctx, x, y, w, h, text, opts = {}) {
  ctx.addText(slide, { x, y, width: w, height: h, text, fontSize: opts.size || 15, bold: opts.bold || false, color: opts.color || P.ink, typeface: opts.face || "Microsoft YaHei", align: opts.align || "left", valign: opts.valign || "top", insets: opts.insets || { left: 0, right: 0, top: 0, bottom: 0 } });
}

function bullet(slide, ctx, x, y, title, body, color = P.blue) {
  ctx.addShape(slide, { x, y: y + 5, width: 8, height: 8, fill: color });
  label(slide, ctx, x + 20, y, 250, 22, title, { size: 16, bold: true });
  label(slide, ctx, x + 20, y + 26, 470, 48, body, { size: 13, color: P.muted });
}

function arrow(slide, ctx, x1, y1, x2, y2, color = P.blue) {
  ctx.addShape(slide, { geometry: "line", x: x1, y: y1, width: x2 - x1, height: y2 - y1, line: ctx.line(color, 2) });
  ctx.addShape(slide, { geometry: "triangle", x: x2 - 8, y: y2 - 6, width: 12, height: 12, fill: color, line: ctx.line(color, 0) });
}
`;

function makeSlideSource(slide, index) {
  const data = JSON.stringify(slide, null, 2);
  return `${helper}
const data = ${data};

export async function slide${String(index).padStart(2, "0")}(presentation, ctx) {
  const slide = presentation.slides.add();
  const n = ${index};
  if (data.type === "cover") {
    ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.navy });
    ctx.addShape(slide, { x: 0, y: 520, width: ctx.W, height: 200, fill: "#102C45" });
    ctx.addShape(slide, { x: 830, y: 0, width: 450, height: ctx.H, fill: "#173B5F" });
    label(slide, ctx, 70, 66, 760, 40, data.kicker, { size: 18, color: "#A7D8FF" });
    label(slide, ctx, 70, 124, 780, 110, data.title, { size: 48, bold: true, color: P.white });
    label(slide, ctx, 74, 244, 740, 56, data.subtitle, { size: 22, color: "#D7DEE8" });
    label(slide, ctx, 74, 336, 640, 70, data.claim, { size: 22, bold: true, color: P.white });
    label(slide, ctx, 70, 640, 300, 28, data.date, { size: 15, color: "#AAB8C8" });
    data.metrics.forEach((m, i) => {
      const y = 118 + i * 118;
      card(slide, ctx, 885, y, 280, 82, { fill: "#FFFFFF12", line: "#FFFFFF30" });
      label(slide, ctx, 908, y + 12, 150, 34, m[0], { size: 31, bold: true, color: P.white, face: "Aptos Display" });
      label(slide, ctx, 908, y + 52, 220, 22, m[1], { size: 14, color: "#D7DEE8" });
    });
  } else {
    addBg(slide, ctx, data.title, data.claim);

    if (data.type === "problem") {
      data.points.forEach((p, i) => {
        const x = 68 + (i % 2) * 570;
        const y = 165 + Math.floor(i / 2) * 190;
        card(slide, ctx, x, y, 500, 145);
        ctx.addShape(slide, { x, y, width: 6, height: 145, fill: [P.blue, P.cyan, P.amber, P.red][i] });
        label(slide, ctx, x + 24, y + 22, 250, 28, p[0], { size: 20, bold: true });
        label(slide, ctx, x + 24, y + 62, 420, 58, p[1], { size: 15, color: P.muted });
      });
    }

    if (data.type === "architecture") {
      const xs = [62, 233, 404, 575, 746, 917, 1088];
      data.layers.forEach((l, i) => {
        const x = xs[i];
        const y = i % 2 === 0 ? 170 : 318;
        card(slide, ctx, x, y, 140, 112, { fill: i % 2 === 0 ? P.white : P.chip, line: P.line });
        label(slide, ctx, x + 14, y + 10, 34, 28, l[0], { size: 22, bold: true, color: P.blue, face: "Aptos Display" });
        label(slide, ctx, x + 14, y + 42, 112, 26, l[1], { size: 14, bold: true });
        label(slide, ctx, x + 14, y + 74, 108, 34, l[2], { size: 10.5, color: P.muted });
        if (i < data.layers.length - 1) arrow(slide, ctx, x + 142, y + 55, xs[i + 1] - 8, (i + 1) % 2 === 0 ? 225 : 373, "#96A3B8");
      });
      card(slide, ctx, 160, 510, 940, 76, { fill: "#EAF7F7", line: "#B7E1E1" });
      label(slide, ctx, 186, 530, 900, 34, "约束逐层递进：任何违反硬约束的候选都携带诊断信息返回上一层，而不是继续消耗综合资源。", { size: 19, bold: true, color: P.navy });
    }

    if (data.type === "workflow") {
      data.steps.forEach((s, i) => {
        const col = i % 4;
        const row = Math.floor(i / 4);
        const x = 66 + col * 286;
        const y = 170 + row * 190;
        card(slide, ctx, x, y, 230, 110, { fill: row === 0 ? P.white : "#F0FBFA" });
        label(slide, ctx, x + 16, y + 15, 35, 26, String(i + 1), { size: 20, bold: true, color: P.cyan, face: "Aptos Display" });
        label(slide, ctx, x + 58, y + 17, 150, 24, s[0], { size: 18, bold: true });
        label(slide, ctx, x + 18, y + 55, 190, 36, s[1], { size: 13, color: P.muted });
        if (i !== 3 && i !== 7) arrow(slide, ctx, x + 232, y + 55, x + 278, y + 55, "#9AA7BB");
      });
      arrow(slide, ctx, 1080, 226, 1080, 360, "#9AA7BB");
    }

    if (data.type === "tools") {
      data.groups.forEach((g, i) => {
        const x = 70 + i * 390;
        card(slide, ctx, x, 170, 330, 300, { fill: P.white });
        label(slide, ctx, x + 24, 194, 260, 30, g[0], { size: 21, bold: true, color: [P.blue, P.green, P.amber][i] });
        g[1].forEach((item, j) => label(slide, ctx, x + 28, 250 + j * 58, 270, 34, item, { size: 15, color: P.ink, face: "Aptos" }));
      });
      card(slide, ctx, 112, 520, 1030, 52, { fill: "#FFF7E8", line: "#F2D3A7" });
      label(slide, ctx, 135, 535, 980, 24, data.note, { size: 16, color: P.amber, bold: true });
    }

    if (data.type === "xdc") {
      data.checks.forEach((c, i) => {
        const x = 70 + (i % 3) * 370;
        const y = 160 + Math.floor(i / 3) * 118;
        card(slide, ctx, x, y, 316, 86, { fill: P.white });
        label(slide, ctx, x + 18, y + 14, 130, 24, c[0], { size: 17, bold: true, color: P.blue });
        label(slide, ctx, x + 18, y + 42, 270, 30, c[1], { size: 12.5, color: P.muted });
      });
      card(slide, ctx, 104, 470, 1050, 110, { fill: "#101827", line: "#101827" });
      data.snippet.forEach((line, i) => label(slide, ctx, 132, 495 + i * 27, 900, 22, line, { size: 17, color: "#EAF0FF", face: "Aptos Mono" }));
    }

    if (data.type === "metrics") {
      data.cards.forEach((c, i) => {
        const x = 70 + (i % 2) * 555;
        const y = 160 + Math.floor(i / 2) * 150;
        card(slide, ctx, x, y, 500, 112, { fill: P.white });
        label(slide, ctx, x + 24, y + 17, 160, 24, c[0], { size: 19, bold: true });
        label(slide, ctx, x + 24, y + 50, 220, 23, c[1], { size: 15, color: P.blue, face: "Aptos" });
        label(slide, ctx, x + 260, y + 35, 205, 42, c[2], { size: 13, color: P.muted });
      });
      data.examples.forEach((e, i) => {
        const x = 250 + i * 400;
        card(slide, ctx, x, 506, 330, 64, { fill: "#F0FBFA", line: "#B7E1E1" });
        label(slide, ctx, x + 20, 522, 90, 24, e[0], { size: 18, bold: true, color: P.green, face: "Aptos" });
        label(slide, ctx, x + 118, 523, 190, 22, e.slice(1).join(" | "), { size: 15, color: P.ink, face: "Aptos" });
      });
    }

    if (data.type === "evidence") {
      data.bars.forEach((b, i) => {
        const y = 166 + i * 78;
        label(slide, ctx, 80, y, 180, 26, b[0], { size: 16, bold: true });
        ctx.addShape(slide, { x: 280, y: y + 5, width: 520, height: 22, fill: "#E5EAF2" });
        ctx.addShape(slide, { x: 280, y: y + 5, width: Math.max(18, 520 * b[1] / 100), height: 22, fill: i === 3 ? P.amber : P.blue });
        label(slide, ctx, 820, y - 2, 90, 30, b[1] + "%", { size: 23, bold: true, color: i === 3 ? P.amber : P.blue, face: "Aptos Display" });
        label(slide, ctx, 920, y + 1, 250, 24, b[2], { size: 13, color: P.muted });
      });
      data.callouts.forEach((c, i) => bullet(slide, ctx, 110, 500 + i * 38, "", c, [P.green, P.cyan, P.amber][i]));
    }

    if (data.type === "templates") {
      data.templates.forEach((t, i) => {
        const x = 80 + (i % 2) * 555;
        const y = 160 + Math.floor(i / 2) * 145;
        card(slide, ctx, x, y, 500, 104, { fill: i < 2 ? P.white : "#F8FBFF" });
        label(slide, ctx, x + 24, y + 18, 95, 28, t[0], { size: 21, bold: true, color: [P.blue, P.green, P.cyan, P.amber][i], face: "Aptos Display" });
        label(slide, ctx, x + 125, y + 20, 335, 52, t[1], { size: 13.5, color: P.muted });
      });
      card(slide, ctx, 166, 512, 945, 58, { fill: "#EAF0FF", line: "#C8D5FF" });
      label(slide, ctx, 195, 531, 900, 24, data.formula, { size: 19, bold: true, color: P.blue, face: "Aptos" });
    }

    if (data.type === "mvp") {
      data.lanes.forEach((l, i) => {
        const x = 82 + i * 280;
        card(slide, ctx, x, 170, 230, 150, { fill: P.white });
        label(slide, ctx, x + 22, 194, 160, 28, l[0], { size: 21, bold: true, color: [P.blue, P.cyan, P.green, P.amber][i] });
        label(slide, ctx, x + 22, 238, 180, 48, l[1], { size: 14, color: P.muted });
        if (i < 3) arrow(slide, ctx, x + 232, 245, x + 272, 245, "#9AA7BB");
      });
      card(slide, ctx, 130, 410, 1020, 124, { fill: "#101827", line: "#101827" });
      label(slide, ctx, 160, 433, 180, 28, "MVP 完成标准", { size: 21, bold: true, color: P.white });
      data.done.forEach((d, i) => label(slide, ctx, 390, 430 + i * 33, 680, 26, d, { size: 17, color: "#EAF0FF" }));
    }

    if (data.type === "team") {
      data.roles.forEach((r, i) => {
        const y = 150 + i * 84;
        card(slide, ctx, 82, y, 1090, 58, { fill: i % 2 === 0 ? P.white : "#F0FBFA" });
        label(slide, ctx, 108, y + 15, 160, 24, r[0], { size: 18, bold: true, color: [P.blue, P.green, P.cyan, P.amber, P.red][i] });
        label(slide, ctx, 310, y + 16, 760, 24, r[1], { size: 15, color: P.ink });
      });
    }

    if (data.type === "roadmap") {
      data.roadmap.forEach((r, i) => {
        const x = 74 + i * 292;
        card(slide, ctx, x, 158, 245, 250, { fill: P.white });
        label(slide, ctx, x + 20, 184, 140, 26, r[0], { size: 19, bold: true, color: P.blue });
        label(slide, ctx, x + 20, 226, 180, 32, r[1], { size: 18, bold: true });
        label(slide, ctx, x + 20, 278, 195, 72, r[2], { size: 13.5, color: P.muted });
      });
      card(slide, ctx, 144, 486, 980, 84, { fill: "#FFF7E8", line: "#F2D3A7" });
      label(slide, ctx, 174, 510, 110, 28, "本周需要", { size: 20, bold: true, color: P.amber });
      data.asks.forEach((a, i) => label(slide, ctx, 330 + i * 250, 505, 220, 38, a, { size: 15, color: P.ink }));
    }

    addFooter(slide, ctx, n);
  }
  return slide;
}
`;
}

async function main() {
  await fs.mkdir(slidesDir, { recursive: true });
  for (let i = 0; i < deckData.slides.length; i += 1) {
    const fileName = `slide-${String(i + 1).padStart(2, "0")}.mjs`;
    await fs.writeFile(path.join(slidesDir, fileName), makeSlideSource(deckData.slides[i], i + 1), "utf8");
  }
}

await main();
