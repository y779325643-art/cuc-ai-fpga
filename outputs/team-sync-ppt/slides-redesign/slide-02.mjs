
const P = {
  bg: "#F3F7FB",
  panel: "#FFFFFF",
  ink: "#132033",
  muted: "#5D6878",
  faint: "#E4EAF2",
  blue: "#2557D6",
  cyan: "#11A8B8",
  mint: "#DDF7F3",
  amber: "#F08A24",
  red: "#D6514B",
  navy: "#0B1424",
  navy2: "#111E33",
  steel: "#73839A",
  white: "#FFFFFF",
  chip: "#EAF0FF",
};

function text(slide, ctx, x, y, width, height, value, opts = {}) {
  ctx.addText(slide, {
    x, y, width, height,
    text: value,
    fontSize: opts.size ?? 15,
    bold: opts.bold ?? false,
    color: opts.color ?? P.ink,
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    typeface: opts.face ?? "Microsoft YaHei",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

function box(slide, ctx, x, y, width, height, opts = {}) {
  ctx.addShape(slide, {
    x, y, width, height,
    fill: opts.fill ?? P.panel,
    line: ctx.line(opts.line ?? P.faint, opts.lineWidth ?? 1),
  });
}

function line(slide, ctx, x1, y1, x2, y2, color = P.steel, weight = 1.4) {
  ctx.addShape(slide, {
    geometry: "line",
    x: x1,
    y: y1,
    width: x2 - x1,
    height: y2 - y1,
    line: ctx.line(color, weight),
  });
}

function arrow(slide, ctx, x1, y1, x2, y2, color = P.steel) {
  line(slide, ctx, x1, y1, x2, y2, color, 2);
  ctx.addShape(slide, {
    geometry: "triangle",
    x: x2 - 7,
    y: y2 - 6,
    width: 12,
    height: 12,
    fill: color,
    line: ctx.line(color, 0),
  });
}

function circuit(slide, ctx, variant = "light") {
  const color = variant === "dark" ? "#FFFFFF12" : "#C9D4E433";
  for (let x = 80; x < 1230; x += 112) line(slide, ctx, x, 0, x, 720, color, 0.8);
  for (let y = 84; y < 690; y += 92) line(slide, ctx, 0, y, 1280, y, color, 0.8);
  const nodes = [[1100,118],[1184,118],[1184,210],[1010,302],[1096,394],[1190,484],[1038,586]];
  for (let i = 0; i < nodes.length - 1; i += 1) line(slide, ctx, nodes[i][0], nodes[i][1], nodes[i+1][0], nodes[i+1][1], color, 1.2);
}

function frame(slide, ctx, data, n) {
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.bg });
  circuit(slide, ctx);
  ctx.addShape(slide, { x: 0, y: 0, width: 1280, height: 96, fill: P.navy });
  ctx.addShape(slide, { x: 0, y: 96, width: 1280, height: 5, fill: P.blue });
  ctx.addShape(slide, { x: 1030, y: 0, width: 250, height: 96, fill: P.navy2 });
  text(slide, ctx, 54, 28, 770, 34, data.title, { size: 25, bold: true, color: P.white });
  text(slide, ctx, 54, 62, 900, 22, data.claim, { size: 13.2, color: "#C7D3E3" });
  text(slide, ctx, 1090, 32, 118, 20, "HNAI-FPGA", { size: 12, bold: true, color: "#7DD3FC", align: "right", face: "Aptos" });
  text(slide, ctx, 1216, 32, 38, 20, String(n).padStart(2, "0"), { size: 12, color: "#93A4BA", align: "right", face: "Aptos" });
  ctx.addShape(slide, { x: 54, y: 676, width: 1090, height: 1.1, fill: "#D8E0EA" });
  text(slide, ctx, 54, 688, 620, 18, "team technical sync | source: project manuscript & business plan", { size: 9.5, color: P.steel, face: "Aptos" });
}

function sectionTag(slide, ctx, x, y, value, color = P.blue) {
  ctx.addShape(slide, { x, y: y + 4, width: 8, height: 22, fill: color });
  text(slide, ctx, x + 18, y, 260, 26, value, { size: 17, bold: true, color });
}

function proofBand(slide, ctx, y, label, body, color = P.blue) {
  box(slide, ctx, 92, y, 1090, 58, { fill: "#FFFFFF", line: "#DDE6F2" });
  ctx.addShape(slide, { x: 92, y, width: 10, height: 58, fill: color });
  text(slide, ctx, 122, y + 12, 160, 24, label, { size: 16.2, bold: true, color });
  text(slide, ctx, 300, y + 14, 860, 24, body, { size: 14.5, bold: true, color: P.ink });
}

function miniMetric(slide, ctx, x, y, value, label, color = P.blue) {
  box(slide, ctx, x, y, 190, 92, { fill: "#FFFFFF16", line: "#FFFFFF2B" });
  text(slide, ctx, x + 18, y + 15, 150, 34, value, { size: 27, bold: true, color: P.white, face: "Aptos Display" });
  text(slide, ctx, x + 18, y + 55, 150, 20, label, { size: 12.5, color: "#CFE2F7" });
  ctx.addShape(slide, { x: x + 18, y: y + 78, width: 76, height: 3, fill: color });
}

const data = {
  "type": "problem",
  "title": "为什么要做：非 DNN 算法的 FPGA 落地仍然很重",
  "claim": "现有 FPGA AI 工具多围绕 DNN 推理，GA/RL/路径规划/调度优化仍依赖专家手工硬件设计。",
  "points": [
    [
      "传统流程周期长",
      "算法规格、架构选择、RTL/HLS、仿真、综合、约束迭代通常需要 48-120 小时。"
    ],
    [
      "专业门槛高",
      "需要同时掌握 HDL/HLS、时序闭合、资源映射、板级验证和工具链交互。"
    ],
    [
      "LLM-to-RTL 不够",
      "通用大模型能产出代码片段，但缺少物理约束验证，复杂设计容易时序失败或资源超限。"
    ],
    [
      "现有工具覆盖窄",
      "Vitis AI、hls4ml、FINN 更适合已训练 DNN 模型，不解决非 DNN 算法到工程包的闭环。"
    ]
  ]
};

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  const n = 2;

  if (data.type === "cover") {
    ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.navy });
    circuit(slide, ctx, "dark");
    ctx.addShape(slide, { x: 0, y: 520, width: ctx.W, height: 200, fill: "#10233B" });
    ctx.addShape(slide, { x: 835, y: 0, width: 445, height: ctx.H, fill: "#122C4B" });
    ctx.addShape(slide, { x: 835, y: 0, width: 5, height: ctx.H, fill: P.cyan });
    text(slide, ctx, 70, 58, 760, 26, data.kicker, { size: 15, color: "#7DD3FC", face: "Aptos" });
    text(slide, ctx, 70, 118, 740, 112, data.title, { size: 48, bold: true, color: P.white });
    text(slide, ctx, 74, 252, 710, 38, data.subtitle, { size: 19, color: "#C7D3E3" });
    ctx.addShape(slide, { x: 72, y: 332, width: 86, height: 4, fill: P.amber });
    text(slide, ctx, 74, 360, 660, 70, data.claim, { size: 22, bold: true, color: P.white });
    text(slide, ctx, 70, 640, 240, 24, data.date, { size: 12.5, color: "#93A4BA", face: "Aptos" });
    data.metrics.forEach((m, i) => miniMetric(slide, ctx, 900, 96 + i * 118, m[0], m[1], [P.cyan, P.blue, P.amber, "#58D29B"][i]));
    return slide;
  }

  frame(slide, ctx, data, n);

  if (data.type === "problem") {
    text(slide, ctx, 70, 132, 470, 30, "Four blockers before real board deployment", { size: 15, bold: true, color: P.steel, face: "Aptos" });
    data.points.forEach((p, i) => {
      const x = 70 + (i % 2) * 575;
      const y = 182 + Math.floor(i / 2) * 174;
      box(slide, ctx, x, y, 505, 126, { fill: i === 0 ? "#FFFFFF" : "#FAFCFF", line: "#DCE5F0" });
      ctx.addShape(slide, { x, y, width: 48, height: 126, fill: [P.blue, P.cyan, P.amber, P.red][i] });
      text(slide, ctx, x + 15, y + 20, 24, 28, String(i + 1), { size: 20, bold: true, color: P.white, face: "Aptos Display", align: "center" });
      text(slide, ctx, x + 70, y + 24, 220, 24, p[0], { size: 19, bold: true });
      text(slide, ctx, x + 70, y + 58, 410, 44, p[1], { size: 13.5, color: P.muted });
    });
  }

  if (data.type === "architecture") {
    const xs = [70, 230, 390, 550, 710, 870, 1030];
    data.layers.forEach((l, i) => {
      const y = i % 2 === 0 ? 158 : 334;
      box(slide, ctx, xs[i], y, 130, 132, { fill: i % 2 === 0 ? "#FFFFFF" : "#EAF0FF", line: "#D2DBEB" });
      text(slide, ctx, xs[i] + 14, y + 10, 36, 26, l[0], { size: 22, bold: true, color: P.blue, face: "Aptos Display" });
      text(slide, ctx, xs[i] + 14, y + 42, 106, 30, l[1], { size: 13.2, bold: true });
      text(slide, ctx, xs[i] + 14, y + 80, 102, 28, l[2], { size: 9.2, color: P.muted });
      if (i < data.layers.length - 1) arrow(slide, ctx, xs[i] + 132, y + 66, xs[i+1] - 8, (i + 1) % 2 === 0 ? 224 : 400, "#8CA0B8");
    });
    proofBand(slide, ctx, 540, "硬约束门禁", "任何违反约束的候选都携带诊断信息返回上一层，而不是继续消耗综合资源。", P.cyan);
  }

  if (data.type === "workflow") {
    data.steps.forEach((s, i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = 74 + col * 292;
      const y = 170 + row * 188;
      box(slide, ctx, x, y, 232, 118, { fill: row === 0 ? "#FFFFFF" : "#F0FBFA", line: "#D7E4EE" });
      text(slide, ctx, x + 18, y + 16, 34, 26, String(i + 1), { size: 20, bold: true, color: P.cyan, face: "Aptos Display" });
      text(slide, ctx, x + 62, y + 18, 150, 24, s[0], { size: 17, bold: true });
      text(slide, ctx, x + 20, y + 58, 190, 38, s[1], { size: 12.5, color: P.muted });
      if (i !== 3 && i !== 7) arrow(slide, ctx, x + 234, y + 58, x + 282, y + 58, "#91A2B8");
    });
    arrow(slide, ctx, 1108, 226, 1108, 360, "#91A2B8");
    proofBand(slide, ctx, 545, "闭环原则", "Agent 负责调度和修正，EDA 工具负责验证，报告负责驱动下一轮决策。", P.blue);
  }

  if (data.type === "tools") {
    data.groups.forEach((g, i) => {
      const x = 70 + i * 390;
      box(slide, ctx, x, 164, 330, 322, { fill: "#FFFFFF", line: "#DCE5F0" });
      ctx.addShape(slide, { x, y: 164, width: 330, height: 7, fill: [P.blue, P.cyan, P.amber][i] });
      text(slide, ctx, x + 24, 194, 260, 26, g[0], { size: 20, bold: true, color: [P.blue, P.cyan, P.amber][i] });
      g[1].forEach((item, j) => {
        ctx.addShape(slide, { x: x + 25, y: 254 + j * 60, width: 8, height: 8, fill: [P.blue, P.cyan, P.amber][i] });
        text(slide, ctx, x + 44, 246 + j * 60, 270, 34, item, { size: 14.2, color: P.ink, face: "Aptos" });
      });
    });
    proofBand(slide, ctx, 535, "工程边界", data.note, P.amber);
  }

  if (data.type === "xdc") {
    data.checks.forEach((c, i) => {
      const x = 70 + (i % 3) * 370;
      const y = 150 + Math.floor(i / 3) * 112;
      box(slide, ctx, x, y, 318, 82, { fill: "#FFFFFF", line: "#DCE5F0" });
      text(slide, ctx, x + 18, y + 13, 150, 22, c[0], { size: 16.5, bold: true, color: P.blue });
      text(slide, ctx, x + 18, y + 40, 272, 30, c[1], { size: 11.8, color: P.muted });
    });
    box(slide, ctx, 86, 462, 1090, 144, { fill: "#101827", line: "#101827" });
    text(slide, ctx, 114, 484, 190, 20, "XDC snippet", { size: 12, bold: true, color: "#7DD3FC", face: "Aptos" });
    data.snippet.forEach((row, i) => text(slide, ctx, 114, 512 + i * 26, 900, 22, row, { size: 15.2, color: "#EAF0FF", face: "Aptos Mono" }));
  }

  if (data.type === "metrics") {
    data.cards.forEach((c, i) => {
      const x = 72 + (i % 2) * 555;
      const y = 148 + Math.floor(i / 2) * 142;
      box(slide, ctx, x, y, 500, 104, { fill: "#FFFFFF", line: "#DCE5F0" });
      text(slide, ctx, x + 24, y + 18, 170, 24, c[0], { size: 18, bold: true });
      text(slide, ctx, x + 24, y + 50, 220, 22, c[1], { size: 14, color: P.blue, face: "Aptos" });
      text(slide, ctx, x + 270, y + 30, 205, 42, c[2], { size: 12.5, color: P.muted });
    });
    data.examples.forEach((e, i) => {
      const x = 250 + i * 400;
      box(slide, ctx, x, 512, 330, 72, { fill: P.mint, line: "#B7E1E1" });
      text(slide, ctx, x + 24, 534, 92, 24, e[0], { size: 18, bold: true, color: "#19765B", face: "Aptos" });
      text(slide, ctx, x + 124, 535, 190, 22, e.slice(1).join(" | "), { size: 14.5, color: P.ink, face: "Aptos" });
    });
  }

  if (data.type === "evidence") {
    data.bars.forEach((b, i) => {
      const y = 156 + i * 76;
      text(slide, ctx, 94, y, 170, 26, b[0], { size: 15.2, bold: true });
      ctx.addShape(slide, { x: 280, y: y + 6, width: 520, height: 24, fill: "#DFE7F1" });
      ctx.addShape(slide, { x: 280, y: y + 6, width: Math.max(18, 520 * b[1] / 100), height: 24, fill: i === 3 ? P.amber : P.blue });
      text(slide, ctx, 822, y - 2, 92, 32, b[1] + "%", { size: 23, bold: true, color: i === 3 ? P.amber : P.blue, face: "Aptos Display" });
      text(slide, ctx, 920, y + 3, 250, 22, b[2], { size: 12.2, color: P.muted });
    });
    data.callouts.forEach((c, i) => proofBand(slide, ctx, 466 + i * 58, ["基准覆盖", "吞吐提升", "时间缩短"][i], c, [P.cyan, P.blue, P.amber][i]));
  }

  if (data.type === "templates") {
    data.templates.forEach((t, i) => {
      const x = 80 + (i % 2) * 555;
      const y = 150 + Math.floor(i / 2) * 136;
      box(slide, ctx, x, y, 500, 98, { fill: i < 2 ? "#FFFFFF" : "#F8FBFF", line: "#DCE5F0" });
      text(slide, ctx, x + 24, y + 18, 95, 28, t[0], { size: 21, bold: true, color: [P.blue, "#19765B", P.cyan, P.amber][i], face: "Aptos Display" });
      text(slide, ctx, x + 124, y + 20, 340, 48, t[1], { size: 12.8, color: P.muted });
    });
    proofBand(slide, ctx, 538, "资源模型", data.formula, P.blue);
  }

  if (data.type === "mvp") {
    data.lanes.forEach((l, i) => {
      const x = 82 + i * 280;
      box(slide, ctx, x, 162, 230, 142, { fill: "#FFFFFF", line: "#DCE5F0" });
      text(slide, ctx, x + 22, 190, 160, 26, l[0], { size: 20, bold: true, color: [P.blue, P.cyan, "#19765B", P.amber][i] });
      text(slide, ctx, x + 22, 236, 182, 44, l[1], { size: 12.7, color: P.muted });
      if (i < 3) arrow(slide, ctx, x + 232, 234, x + 272, 234, "#91A2B8");
    });
    box(slide, ctx, 130, 398, 1020, 138, { fill: "#101827", line: "#101827" });
    text(slide, ctx, 160, 424, 180, 28, "MVP 完成标准", { size: 21, bold: true, color: P.white });
    data.done.forEach((d, i) => text(slide, ctx, 390, 423 + i * 34, 680, 26, d, { size: 16.2, color: "#EAF0FF" }));
  }

  if (data.type === "team") {
    data.roles.forEach((r, i) => {
      const y = 142 + i * 86;
      box(slide, ctx, 82, y, 1090, 62, { fill: i % 2 === 0 ? "#FFFFFF" : "#F0FBFA", line: "#DCE5F0" });
      text(slide, ctx, 108, y + 17, 160, 24, r[0], { size: 17.5, bold: true, color: [P.blue, "#19765B", P.cyan, P.amber, P.red][i] });
      text(slide, ctx, 310, y + 18, 780, 24, r[1], { size: 14.4, color: P.ink });
    });
  }

  if (data.type === "roadmap") {
    data.roadmap.forEach((r, i) => {
      const x = 74 + i * 292;
      box(slide, ctx, x, 150, 245, 252, { fill: "#FFFFFF", line: "#DCE5F0" });
      ctx.addShape(slide, { x, y: 150, width: 245, height: 7, fill: [P.blue, P.cyan, P.amber, "#19765B"][i] });
      text(slide, ctx, x + 20, 184, 140, 24, r[0], { size: 17, bold: true, color: P.blue });
      text(slide, ctx, x + 20, 224, 185, 32, r[1], { size: 17.2, bold: true });
      text(slide, ctx, x + 20, 278, 196, 76, r[2], { size: 12.5, color: P.muted });
    });
    proofBand(slide, ctx, 508, "本周需要", data.asks.join("    |    "), P.amber);
  }

  return slide;
}
